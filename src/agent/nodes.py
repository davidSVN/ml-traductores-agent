import json
import logging
from pathlib import Path

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, ToolMessage
from sqlalchemy import select

from src.agent.phase_detector import detect_phase
from src.agent.state import AgentState, missing_required, prompt_summary
from src.config import get_settings
from src.db.engine import async_session_factory
from src.db.models import Cliente, Contacto
from src.tools.db_cliente import buscar_cliente, crear_cliente, crear_contacto, actualizar_contacto, actualizar_cliente
from src.tools.db_conversacion import marcar_revisar
from src.tools.db_cotizacion import (
    actualizar_cotizacion, calcular_cotizacion, crear_solicitud, enviar_cotizacion, generar_contrato
)
from src.tools.db_servicios import consultar_historial, consultar_tarifas, listar_servicios

logger = logging.getLogger(__name__)
settings = get_settings()

SKILLS_DIR = Path(__file__).parent.parent / "skills"

# Skills cargadas por fase
PHASE_SKILLS: dict[str, list[str]] = {
    "inicial":             ["personalidad.md"],
    "recopilando":         ["personalidad.md", "recopilacion.md"],
    "cualificando":        ["personalidad.md", "recopilacion.md"],
    "listo_para_cotizar":  ["personalidad.md", "cotizacion.md"],
    "cotizando":           ["personalidad.md", "cotizando.md"],
}

# Tools disponibles por fase
# lookup_contact_node ya hace el lookup automatico por WhatsApp al inicio
PHASE_TOOLS: dict[str, list] = {
    "inicial": [
        listar_servicios,
        marcar_revisar,
    ],
    "recopilando": [
        listar_servicios, buscar_cliente, crear_cliente, crear_contacto,
        marcar_revisar,
    ],
    "cualificando": [
        buscar_cliente, crear_contacto, consultar_historial,
        marcar_revisar,
    ],
    "listo_para_cotizar": [
        consultar_historial, consultar_tarifas,
        calcular_cotizacion, enviar_cotizacion, crear_solicitud,
        actualizar_cliente, actualizar_contacto,
        marcar_revisar,
    ],
    "cotizando": [
        actualizar_cotizacion, calcular_cotizacion, enviar_cotizacion,
        generar_contrato, crear_solicitud, marcar_revisar,
        crear_contacto, crear_cliente,
        actualizar_contacto, actualizar_cliente,
    ],
}


def _load_skills(phase: str) -> str:
    filenames = PHASE_SKILLS.get(phase, PHASE_SKILLS["inicial"])
    parts: list[str] = []
    for filename in filenames:
        path = SKILLS_DIR / filename
        if path.exists():
            parts.append(path.read_text(encoding="utf-8"))
        else:
            logger.warning(f"Skill file not found: {path}")
    return "\n\n---\n\n".join(parts)


def _build_system_prompt(state: AgentState) -> str:
    phase = state.get("phase", "inicial")
    skills = _load_skills(phase)
    estado = prompt_summary(state)
    return skills + "\n\n---\n\n## Estado de esta conversación\n" + estado


# ─────────────────────────────────────────
# NODOS DEL GRAFO
# ─────────────────────────────────────────

async def detect_phase_node(state: AgentState) -> dict:
    """
    Nodo Python puro — detecta la fase sin llamar al LLM.
    No consume tokens extra.
    """
    phase = detect_phase(state)
    logger.info(f"phase_detector: {state.get('phase', 'inicial')!r} → {phase!r} | missing={missing_required(state)}")
    return {"phase": phase}


async def lookup_contact_node(state: AgentState) -> dict:
    """
    Nodo Python puro — busca el contacto por número WhatsApp al inicio de la conversación.
    Solo actúa si cliente_id aún no está en state (evita re-buscar en cada mensaje).
    No consume tokens — acceso directo a DB.
    """
    if state.get("cliente_id") is not None:
        return {}  # ya identificado en una llamada anterior

    phone = state.get("phone", "")
    if not phone:
        return {}

    # Normalizar: quitar + y prefijo 57 de Colombia si el número tiene 12 dígitos
    normalized = phone.lstrip("+")
    if normalized.startswith("57") and len(normalized) == 12:
        normalized = normalized[2:]

    async with async_session_factory() as db:
        result = await db.execute(
            select(Contacto, Cliente)
            .join(Cliente, Contacto.cliente_id == Cliente.id)
            .where(
                Contacto.telefono.ilike(f"%{normalized}%")
                | Contacto.telefono.ilike(f"%{phone}%")
            )
            .limit(1)
        )
        row = result.first()

    if not row:
        logger.info(f"lookup_contact: phone={phone} → no encontrado en DB")
        return {}

    contacto, cliente = row
    nombre_fmt = contacto.nombre_completo.title() if contacto.nombre_completo else ""
    logger.info(
        f"lookup_contact: phone={phone} → cliente_id={cliente.id} "
        f"contacto={nombre_fmt!r} empresa={cliente.nombre_empresa!r}"
    )
    return {
        "cliente_id": cliente.id,
        "contacto_id": contacto.id,
        "nombre": nombre_fmt,
        "empresa": cliente.nombre_empresa,
        "email": contacto.email,
        "cargo": contacto.cargo,
        "es_recurrente": cliente.es_recurrente,
        "nivel_precio": cliente.nivel_precio,
        "notas_pricing": cliente.notas_pricing,
        "servicios_confirmados": cliente.servicios_confirmados,
    }


def _sanitize_messages(messages: list) -> list:
    """
    Garantiza que cada tool_use tenga su tool_result correspondiente.
    Inyecta ToolMessages sintéticos para IDs huérfanos (e.g. de sesiones interrumpidas).
    Evita BadRequestError 400 de Anthropic.
    """
    from langchain_core.messages import AIMessage

    satisfied_ids = {
        msg.tool_call_id
        for msg in messages
        if isinstance(msg, ToolMessage) and hasattr(msg, "tool_call_id")
    }

    result = []
    for msg in messages:
        result.append(msg)
        if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
            orphaned = [tc for tc in msg.tool_calls if tc["id"] not in satisfied_ids]
            for tc in orphaned:
                logger.warning(
                    f"sanitize: inyectando tool_result sintético — "
                    f"id={tc['id']} name={tc['name']}"
                )
                result.append(ToolMessage(
                    content='{"error": "Tool call interrupted — no result available."}',
                    tool_call_id=tc["id"],
                    name=tc["name"],
                ))
    return result


async def chatbot_node(state: AgentState) -> dict:
    """
    Nodo principal — llama al LLM con las skills y tools apropiadas para la fase actual.
    """
    tools = PHASE_TOOLS.get(state.get("phase", "inicial"), PHASE_TOOLS["inicial"])
    system_prompt = _build_system_prompt(state)

    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=settings.anthropic_api_key,
        max_tokens=4096,
    ).bind_tools(tools)

    messages = [SystemMessage(content=system_prompt)] + _sanitize_messages(list(state["messages"]))
    response = await llm.ainvoke(messages)
    return {"messages": [response]}


async def update_state_node(state: AgentState) -> dict:
    """
    Nodo que lee los ToolMessages recién agregados y actualiza AgentState
    con la información extraída (cliente_id, nombre, empresa, etc.).
    Corre después de ToolNode y antes de volver a chatbot_node.
    """
    updates: dict = {}

    for msg in reversed(state["messages"]):
        if not isinstance(msg, ToolMessage):
            break
        try:
            result = json.loads(msg.content)
        except (json.JSONDecodeError, TypeError):
            continue

        tool_name = msg.name
        _apply_tool_result(updates, tool_name, result)

    return updates


def _apply_tool_result(updates: dict, tool_name: str, result: dict) -> None:
    """Extrae campos relevantes del resultado de una tool y los agrega a `updates`."""
    if not isinstance(result, dict):
        return

    if tool_name == "buscar_cliente" and result.get("encontrado"):
        updates["cliente_id"] = result.get("cliente_id")
        updates["es_recurrente"] = result.get("es_recurrente")
        updates["servicios_confirmados"] = result.get("servicios_confirmados")
        updates["nivel_precio"] = result.get("nivel_precio")
        updates["notas_pricing"] = result.get("notas_pricing")
        contactos = result.get("contactos", [])
        if len(contactos) == 1:
            c = contactos[0]
            if not updates.get("nombre"):
                updates["nombre"] = c.get("nombre")
            if not updates.get("email"):
                updates["email"] = c.get("email")
            updates["contacto_id"] = c.get("id")

    elif tool_name == "crear_cliente":
        updates["cliente_id"] = result.get("cliente_id")
        updates["contacto_id"] = result.get("contacto_id")
        if result.get("exento_iva") is not None:
            updates["exento_iva"] = result.get("exento_iva")

    elif tool_name == "crear_contacto":
        updates["contacto_id"] = result.get("contacto_id")
        if result.get("cliente_id"):
            updates["cliente_id"] = result.get("cliente_id")
        if result.get("puede_aprobar_cotizacion") is not None:
            updates["puede_aprobar_cotizacion"] = result.get("puede_aprobar_cotizacion")

    elif tool_name == "calcular_cotizacion" and not result.get("error"):
        updates["cotizacion_id"] = result.get("cotizacion_id")

    elif tool_name == "actualizar_cotizacion" and not result.get("error"):
        updates["cotizacion_estado"] = result.get("estado")

    # marcar_revisar: no actualiza AgentState (solo cambia DB)
