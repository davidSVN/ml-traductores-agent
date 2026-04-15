"""
Tool para gestionar el estado de la conversacion en la base de datos.
"""
import json
import logging
from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from src.db.engine import async_session_factory
from src.db.models import Conversacion

logger = logging.getLogger(__name__)


@tool
async def marcar_revisar(
    motivo: str,
    state: Annotated[dict, InjectedState] = None,
) -> str:
    """
    Marca la conversacion actual como "revisar" para que Maria Luisa la revise en el dashboard.
    Usa esta herramienta cuando no puedas resolver algo por tu cuenta:
    - No encuentras el servicio en el catalogo.
    - El cliente pide algo fuera de lo estandar.
    - Tienes dudas sobre el precio o condiciones.
    - El cliente hace una pregunta que no puedes responder con certeza.
    - Cualquier situacion ambigua que requiera criterio humano.

    motivo: Descripcion breve de por que se escala (ej: "El cliente pide descuento del 40%, fuera de rango").
    """
    conversacion_id = (state or {}).get("conversacion_id")
    if not conversacion_id:
        return json.dumps({"ok": False, "mensaje": "No se encontro conversacion_id en el estado."})

    async with async_session_factory() as db:
        conv = await db.get(Conversacion, conversacion_id)
        if not conv:
            return json.dumps({"ok": False, "mensaje": f"Conversacion {conversacion_id} no encontrada."})

        conv.estado = "revisar"
        # Guardar motivo en metadata
        meta = conv.metadata_ or {}
        meta["motivo_revisar"] = motivo
        conv.metadata_ = meta
        await db.commit()

    logger.info(f"Conversacion {conversacion_id} marcada como 'revisar': {motivo!r}")
    return json.dumps({
        "ok": True,
        "mensaje": "La conversacion fue marcada para revision. Maria Luisa la atendra pronto.",
    }, ensure_ascii=False)
