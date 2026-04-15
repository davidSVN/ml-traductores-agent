import datetime
from typing import Optional

from langgraph.graph import MessagesState

REQUIRED_FIELDS = ["nombre", "empresa", "email"]
REQUIRED_IF_PRESENCIAL: list[str] = []  # reservado para lógica futura


class AgentState(MessagesState):
    """
    Estado completo del agente para ML Traductores.

    MessagesState provee el campo `messages: list[BaseMessage]` con el reducer
    `add_messages` — LangGraph lo persiste automáticamente en PostgreSQL via checkpointer.

    Thread ID usado: `wa_{phone}` (un hilo por número WhatsApp).
    """

    # Contexto de la conversación
    phone: str
    conversacion_id: int
    phase: str

    # Datos del contacto (quien escribe por WhatsApp)
    nombre: Optional[str]
    empresa: Optional[str]
    email: Optional[str]
    telefono: Optional[str]
    cargo: Optional[str]

    # Datos del servicio solicitado
    servicio: Optional[str]
    idioma: Optional[str]
    fecha: Optional[str]
    horario: Optional[str]
    ubicacion: Optional[str]
    cantidad: Optional[str]
    num_interpretes: Optional[str]

    # Datos de empresa (para crear cliente nuevo)
    nit: Optional[str]
    ciudad: Optional[str]
    direccion: Optional[str]
    sector: Optional[str]
    exento_iva: Optional[bool]

    # Datos del contacto adicionales
    puede_aprobar_cotizacion: Optional[bool]

    # IDs resueltos por tools
    cliente_id: Optional[int]
    contacto_id: Optional[int]
    cotizacion_id: Optional[int]
    cotizacion_estado: Optional[str]

    # Metadata del cliente (cargada por buscar_cliente / buscar_contacto_por_telefono)
    es_recurrente: Optional[bool]
    servicios_confirmados: Optional[int]
    nivel_precio: Optional[str]
    notas_pricing: Optional[str]


# ─── Funciones auxiliares (state es dict en LangGraph) ───────────────────────

def missing_required(state: dict) -> list[str]:
    return [f for f in REQUIRED_FIELDS if not state.get(f)]


def is_ready_to_qualify(state: dict) -> bool:
    return len(missing_required(state)) == 0


def prompt_summary(state: dict) -> str:
    """Texto inyectado en el system prompt para que el LLM sepa el estado actual."""
    skip = {
        "phase", "phone", "conversacion_id", "messages",
        "cliente_id", "contacto_id", "cotizacion_id", "cotizacion_estado",
        "es_recurrente", "servicios_confirmados", "nivel_precio", "notas_pricing",
    }
    collected = {
        k: v for k, v in state.items()
        if v is not None and k not in skip
    }
    missing = missing_required(state)

    lines = [
        f"Fecha actual: {datetime.date.today().isoformat()}",
        f"Fase: {state.get('phase', 'inicial')}",
    ]
    if collected:
        lines.append("Datos ya recopilados: " + ", ".join(f"{k}={v}" for k, v in collected.items()))
    if missing:
        lines.append("Campos obligatorios faltantes: " + ", ".join(missing))
    if state.get("cliente_id"):
        lines.append(f"Cliente en DB: id={state['cliente_id']}")
        if state.get("es_recurrente"):
            lines.append("Es cliente recurrente")
        if state.get("servicios_confirmados"):
            lines.append(f"Servicios confirmados historicos: {state['servicios_confirmados']}")
        if state.get("nivel_precio"):
            lines.append(f"Nivel de precio: {state['nivel_precio']}")
        if state.get("notas_pricing"):
            lines.append(f"Notas de pricing (instrucciones internas): {state['notas_pricing']}")
    if state.get("cotizacion_id"):
        lines.append(f"Cotizacion activa: id={state['cotizacion_id']}")
    if state.get("cotizacion_estado"):
        lines.append(f"Estado cotizacion: {state['cotizacion_estado']}")
    return "\n".join(lines)
