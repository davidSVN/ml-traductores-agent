from __future__ import annotations

from langchain_core.tools import tool


@tool
async def create_quote(
    client_name: str,
    client_email: str,
    service_type: str,
    language_pair: str,
    volume: str,
    urgency: str = "normal",
    notes: str = "",
) -> str:
    """Genera una cotizacion formal para el cliente.

    Args:
        client_name: Nombre del cliente
        client_email: Correo del cliente
        service_type: Tipo de servicio solicitado
        language_pair: Par de idiomas origen-destino
        volume: Volumen estimado (palabras, horas, etc.)
        urgency: Nivel de urgencia (normal, urgente, express)
        notes: Notas o requerimientos especiales
    """
    # TODO: implement quote creation in cotizaciones table
    return (
        f"[PLACEHOLDER] Cotizacion creada para {client_name} ({client_email}). "
        f"Servicio: {service_type}, Idiomas: {language_pair}, Volumen: {volume}. "
        "Numero de cotizacion: COT-0000. Pendiente de aprobacion."
    )
