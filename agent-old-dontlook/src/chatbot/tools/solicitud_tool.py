"""
Tool para crear solicitudes de revisión destinadas a la encargada.
Llama al endpoint POST /api/solicitudes de la API, que persiste en BD y
notifica al panel vía WebSocket.
"""
import os
from typing import Any, Annotated

import httpx
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from ..state import State

_API_BASE = os.getenv("API_URL", "http://127.0.0.1:8000")


@tool
async def crear_solicitud(
    tipo: str,
    titulo: str,
    descripcion: str,
    prioridad: str,
    datos_formulario: dict[str, Any],
    state: Annotated[State, InjectedState],
) -> str:
    """
    Crea una solicitud de revisión para la encargada María Luisa y le notifica en tiempo real.

    Cuándo usarla:
    - tipo='aprobar_cotizacion': la cotización está lista y necesita aprobación antes de enviarse.
    - tipo='completar_cliente': el cliente es nuevo y faltan datos de pricing (NIT, nivel, descuentos).
    - tipo='escalar_negociacion': el descuento solicitado supera el máximo permitido.
    - tipo='consulta_precio': el servicio solicitado no tiene tarifa en el catálogo.
    - tipo='otro': cualquier otra situación que requiera decisión humana.

    Args:
        tipo: Tipo de solicitud (aprobar_cotizacion | completar_cliente | escalar_negociacion | consulta_precio | otro)
        titulo: Título breve y descriptivo (ej: "Aprobar COT-056 — Ecopetrol S.A.")
        descripcion: Contexto completo para María Luisa: qué pide el cliente, qué recomiendas y por qué
        prioridad: urgente | normal | baja
        datos_formulario: Datos estructurados relevantes (líneas de cotización, campos faltantes, valores de negociación, etc.)
    """
    payload = {
        "tipo": tipo,
        "titulo": titulo,
        "descripcion": descripcion,
        "prioridad": prioridad,
        "datos_formulario": datos_formulario,
        "conversacion_id": state.conversacion_id,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(f"{_API_BASE}/api/solicitudes/", json=payload)
            resp.raise_for_status()
            data = resp.json()
        return (
            f"Solicitud #{data['id']} creada correctamente. "
            f"María Luisa recibirá la notificación en el panel."
        )
    except httpx.HTTPStatusError as e:
        return f"Error al crear la solicitud (HTTP {e.response.status_code}): {e.response.text}"
    except Exception as e:
        return f"Error al crear la solicitud: {e}"
