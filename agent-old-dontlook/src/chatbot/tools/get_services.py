from __future__ import annotations

from langchain_core.tools import tool


@tool
async def get_services(category: str = "") -> str:
    """Consulta el catalogo de servicios disponibles de ML Traductores.

    Args:
        category: Categoria opcional para filtrar (e.g., 'traduccion_documentos',
                  'interpretacion_vivo', 'transcripcion', 'localizacion',
                  'alquiler_equipos'). Si esta vacio, retorna todos los servicios.
    """
    # TODO: implement database query against servicios table
    return (
        f"[PLACEHOLDER] Servicios disponibles"
        + (f" en categoria '{category}'" if category else "")
        + ": Consultar catalogo en base de datos."
    )
