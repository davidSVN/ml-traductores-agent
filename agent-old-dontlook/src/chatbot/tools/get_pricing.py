from __future__ import annotations

from langchain_core.tools import tool


@tool
async def get_pricing(service_type: str, language_pair: str) -> str:
    """Consulta las tarifas base para un servicio y par de idiomas.

    Args:
        service_type: Tipo de servicio (e.g., 'traduccion_documentos', 'interpretacion_vivo')
        language_pair: Par de idiomas en formato 'origen-destino' (e.g., 'es-en', 'en-fr')
    """
    # TODO: implement database query against tarifas_base table
    return (
        f"[PLACEHOLDER] Tarifas para {service_type} ({language_pair}): "
        "Consultar con Maria Luisa para tarifas actualizadas."
    )
