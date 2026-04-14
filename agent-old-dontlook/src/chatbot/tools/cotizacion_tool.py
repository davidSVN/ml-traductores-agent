"""
Tool para calcular cotizaciones consultando tarifas reales de la BD.
El agente la llama ANTES de crear_solicitud(tipo='aprobar_cotizacion').
"""
import json
import os
from typing import Annotated, Any

import httpx
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from ..state import State

_API_BASE = os.getenv("API_URL", "http://127.0.0.1:8000")


@tool
async def calcular_cotizacion(
    empresa: str,
    tipo_servicio: str,
    idioma_destino: str,
    cantidad: float,
    num_interpretes: int = 2,
    num_receptores: int = 0,
    num_dias: int = 1,
    idioma_origen: str = "español",
    ubicacion: str = "",
    state: Annotated[State, InjectedState],
) -> str:
    """
    Consulta las tarifas reales de la base de datos y calcula el precio de la cotización.
    Registra automáticamente un borrador numerado en la BD.
    Devuelve un JSON con las líneas de precio, subtotal, IVA y total.

    IMPORTANTE: Llama esta herramienta ANTES de crear_solicitud(tipo='aprobar_cotizacion').
    El resultado lo debes incluir como datos_formulario en crear_solicitud.

    Args:
        empresa: Nombre de la empresa del cliente (ej: "Banco de la República").
        tipo_servicio: Tipo de servicio. Valores válidos:
            "interpretacion_simultanea_presencial"
            "interpretacion_simultanea_virtual"
            "interpretacion_consecutiva"
            "traduccion_documentos"
            "transcripcion"
        idioma_destino: Idioma destino (ej: "inglés", "francés", "portugués", "alemán").
        cantidad: Para interpretación → total de horas (días × horas_por_día).
                  Para traducción → número de palabras.
                  Para transcripción → minutos de audio.
        num_interpretes: Cantidad de intérpretes simultáneos. Default 2 para presencial.
        num_receptores: Receptores de simultánea necesarios. 0 si no aplica.
        num_dias: Duración del evento en días (para calcular precio de equipos).
        idioma_origen: Idioma origen del servicio. Default "español".
        ubicacion: Ciudad y lugar del evento.
    """
    payload: dict[str, Any] = {
        "empresa": empresa,
        "tipo_servicio": tipo_servicio,
        "idioma_origen": idioma_origen,
        "idioma_destino": idioma_destino,
        "cantidad": cantidad,
        "num_interpretes": num_interpretes,
        "num_receptores": num_receptores,
        "num_dias": num_dias,
        "ubicacion": ubicacion,
        "conversacion_id": state.conversacion_id if state else None,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{_API_BASE}/api/cotizaciones/calcular-borrador",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as e:
        return (
            f"Error al calcular la cotización (HTTP {e.response.status_code}): "
            f"{e.response.text}. "
            "Usa crear_solicitud(tipo='consulta_precio') para escalar a María Luisa."
        )
    except Exception as e:
        return (
            f"Error de conexión al calcular la cotización: {e}. "
            "Usa crear_solicitud(tipo='consulta_precio') para escalar a María Luisa."
        )

    if data.get("error"):
        return data.get("mensaje", "No se encontró tarifa en el catálogo.")

    return json.dumps(data, ensure_ascii=False)
