"""
Servicio de aprobación interna.
Ejecuta acciones de la encargada sobre cotizaciones: aprobar, modificar, rechazar.
También interpreta mensajes de texto libre usando Claude (ligero, sin LangGraph).
"""
import json
import logging
import re
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.db.engine import async_session_factory
from src.db.models import (
    Cotizacion,
    LineaCotizacion,
    MensajeInterno,
    SolicitudAgente,
)

logger = logging.getLogger(__name__)


async def handle_aprobacion(
    solicitud_id: int,
    cotizacion_id: int,
    phone: str,
    cliente_nombre: str,
    numero_cotizacion: str,
    total: float,
    respuesta: str | None = None,
) -> None:
    """
    Marca cotización como aprobada, envía PDF por email (stub) y notifica al cliente por WhatsApp.
    """
    from src.tools.db_cotizacion import enviar_cotizacion_email
    from src.whatsapp.client import WhatsAppClient

    # Leer email y nombre del destinatario desde datos_formulario
    async with async_session_factory() as db:
        sol = await db.get(SolicitudAgente, solicitud_id)
        datos = sol.datos_formulario if sol else {}
    email_dest = datos.get("email_destinatario") or datos.get("email", "")
    nombre_dest = datos.get("nombre_destinatario") or datos.get("nombre", cliente_nombre)

    async with async_session_factory() as db:
        cot = await db.get(Cotizacion, cotizacion_id)
        if cot and cot.estado == "aprobada":
            logger.info(f"handle_aprobacion: cot {cotizacion_id} ya aprobada, omitiendo duplicado")
            db.add(MensajeInterno(
                solicitud_id=solicitud_id,
                origen="agente",
                contenido="ℹ️ Cotización ya estaba aprobada. No se reenvió.",
                tipo_contenido="accion",
            ))
            await db.commit()
            return

        if cot:
            cot.estado = "aprobada"

        # Enviar por email (stub)
        if email_dest:
            await enviar_cotizacion_email.ainvoke({
                "cotizacion_id": cotizacion_id,
                "email": email_dest,
                "nombre_destinatario": nombre_dest,
                "numero_cotizacion": numero_cotizacion,
            })
            texto_wa = (
                f"¡Su cotización formal *{numero_cotizacion}* ya está lista! "
                f"La enviamos al correo *{email_dest}*. "
                f"Quedamos atentos a sus comentarios. 📧"
            )
        else:
            logger.warning(f"handle_aprobacion sol={solicitud_id}: sin email_destinatario, no se envía por correo")
            texto_wa = (
                f"Su cotización *{numero_cotizacion}* ha sido procesada. "
                f"En breve recibirá el documento formal. 📋"
            )

        if respuesta:
            texto_wa += f"\n\n_{respuesta}_"

        db.add(MensajeInterno(
            solicitud_id=solicitud_id,
            origen="agente",
            contenido=f"✅ Cotización aprobada — PDF enviado a {email_dest or 'sin correo registrado'}.\nWA al cliente: \"{texto_wa}\"",
            tipo_contenido="accion",
        ))
        await db.commit()

    wa = WhatsAppClient()
    await wa.send_text(phone, texto_wa)
    logger.info(f"Notificación WA enviada a {phone} — cot {numero_cotizacion} aprobada")


async def handle_modificacion(
    solicitud_id: int,
    cotizacion_id: int,
    phone: str,
    descuento_porcentaje: float | None = None,
    markup_personalizado: float | None = None,
    respuesta: str | None = None,
    actualizar_pricing_cliente: bool = True,
) -> None:
    """
    Aplica nuevo pricing a la cotización existente, regenera PDF y lo envía al cliente.
    Si actualizar_pricing_cliente=False, asume que el caller ya actualizó el cliente.
    """
    from src.services.documento import docx_a_pdf, generar_word
    from src.storage.s3 import upload_cotizacion
    from src.whatsapp.client import WhatsAppClient

    async with async_session_factory() as db:
        result = await db.execute(
            select(Cotizacion)
            .options(
                selectinload(Cotizacion.lineas).selectinload(LineaCotizacion.servicio),
                selectinload(Cotizacion.cliente),
            )
            .where(Cotizacion.id == cotizacion_id)
        )
        cot = result.scalar_one_or_none()
        if not cot:
            logger.error(f"handle_modificacion: cotizacion {cotizacion_id} no encontrada")
            return

        # Actualizar pricing del cliente (omitir si el caller ya lo hizo)
        if actualizar_pricing_cliente and cot.cliente:
            if markup_personalizado is not None:
                cot.cliente.markup_personalizado = Decimal(str(markup_personalizado))
            if descuento_porcentaje is not None:
                cot.cliente.descuento_min_porcentaje = Decimal(str(descuento_porcentaje))
                cot.cliente.descuento_max_porcentaje = Decimal(str(descuento_porcentaje))

        # Aplicar descuento proporcional a cada línea
        if descuento_porcentaje is not None:
            factor = Decimal("1") - Decimal(str(descuento_porcentaje)) / Decimal("100")
            nuevo_subtotal = Decimal("0")
            for linea in cot.lineas:
                linea.precio_total = linea.precio_total * factor
                nuevo_subtotal += linea.precio_total

            cot.subtotal = nuevo_subtotal
            if not cot.exento_iva:
                cot.iva = nuevo_subtotal * Decimal("0.19")
                cot.total = nuevo_subtotal + cot.iva
            else:
                cot.iva = Decimal("0")
                cot.total = nuevo_subtotal

        # Versionar número: COT-001 → COT-001A → COT-001B → ...
        numero_base = cot.numero_cotizacion
        if numero_base and numero_base[-1].isalpha():
            # Ya tiene versión: COT-001A → COT-001B
            base = numero_base[:-1]
            siguiente_letra = chr(ord(numero_base[-1]) + 1)
        else:
            # Primera modificación: COT-001 → COT-001A
            base = numero_base
            siguiente_letra = "A"
        numero = f"{base}{siguiente_letra}"
        cot.numero_cotizacion = numero
        cot.version = siguiente_letra

        total_fmt = f"${cot.total:,.0f}".replace(",", ".")
        await db.commit()

    # Regenerar PDF con los nuevos valores
    docx_bytes = await generar_word(cotizacion_id)
    pdf_bytes = docx_a_pdf(docx_bytes)
    url = await upload_cotizacion(cotizacion_id, pdf_bytes, numero)

    # Actualizar url_pdf en la solicitud y agregar mensaje interno
    async with async_session_factory() as db:
        sol = await db.get(SolicitudAgente, solicitud_id)
        if sol:
            datos = dict(sol.datos_formulario or {})
            datos["url_pdf"] = url
            sol.datos_formulario = datos

        caption = respuesta or (
            "Revisamos tu cotización y tenemos una actualización de precios. "
            "Nuevo documento adjunto."
        )
        texto_interno = (
            f"✏️ Cotización ajustada: {numero} — Nuevo total: {total_fmt}\n"
            f"PDF regenerado y enviado al cliente."
        )
        if descuento_porcentaje:
            texto_interno += f" (Descuento aplicado: {descuento_porcentaje}%)"

        db.add(MensajeInterno(
            solicitud_id=solicitud_id,
            origen="agente",
            contenido=texto_interno,
            tipo_contenido="accion",
        ))
        await db.commit()

    wa = WhatsAppClient()
    await wa.send_document(
        to=phone,
        document_url=url,
        filename=f"{numero}.pdf",
        caption=caption,
    )
    logger.info(f"Cotización modificada enviada a {phone} — {numero}")


async def handle_rechazo(
    solicitud_id: int,
    cotizacion_id: int,
) -> None:
    """
    Marca cotización como perdida. Sin WhatsApp al cliente.
    """
    async with async_session_factory() as db:
        cot = await db.get(Cotizacion, cotizacion_id)
        if cot:
            cot.estado = "perdida"

        db.add(MensajeInterno(
            solicitud_id=solicitud_id,
            origen="agente",
            contenido="❌ Registrado. Cotización marcada como perdida. Sin comunicación al cliente.",
            tipo_contenido="accion",
        ))
        await db.commit()

    logger.info(f"Cotización {cotizacion_id} rechazada, marcada como perdida")


async def interpretar_mensaje_encargada(
    solicitud_id: int,
    mensaje: str,
    historial: list[dict],
    contexto_solicitud: dict,
) -> dict:
    """
    Usa Claude (Haiku, ligero) para clasificar la intención de un mensaje de la encargada.
    Retorna: {"accion": "aprobar"|"modificar"|"informativo", "descuento": float|null, "nota": str, "respuesta_agente": str}
    """
    import pathlib
    from langchain_anthropic import ChatAnthropic
    from langchain_core.messages import HumanMessage, SystemMessage
    from src.config import get_settings

    settings = get_settings()

    skill_path = pathlib.Path(__file__).parent.parent / "skills" / "aprobacion_interna.md"
    system_prompt = skill_path.read_text(encoding="utf-8") if skill_path.exists() else (
        "Clasifica el mensaje de la encargada. "
        'Responde JSON: {"accion":"aprobar"|"modificar"|"informativo","descuento":null,"nota":"","respuesta_agente":""}'
    )

    historial_txt = "\n".join(
        f"[{m.get('origen', '?')}]: {m.get('contenido', '')}" for m in historial[-10:]
    )
    contexto_txt = json.dumps(contexto_solicitud, ensure_ascii=False, indent=2)

    user_content = (
        f"## Contexto de la solicitud\n{contexto_txt}\n\n"
        f"## Historial reciente\n{historial_txt}\n\n"
        f"## Mensaje de la encargada\n{mensaje}"
    )

    llm = ChatAnthropic(
        model="claude-haiku-4-5",
        api_key=settings.anthropic_api_key,
        max_tokens=512,
    )

    response = await llm.ainvoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content),
    ])

    text = response.content if hasattr(response, "content") else str(response)

    try:
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = {"accion": "informativo", "descuento": None, "nota": "", "respuesta_agente": text}
    except Exception:
        result = {"accion": "informativo", "descuento": None, "nota": "", "respuesta_agente": text}

    logger.info(f"interpretar_mensaje_encargada sol={solicitud_id} accion={result.get('accion')}")
    return result
