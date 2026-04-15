"""
Tools LangGraph para cotización, envío de documentos y escalada a María Luisa.
Usan InjectedState para leer campos del AgentState sin exponerlos al LLM.
"""
import datetime
import json
import logging
from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from sqlalchemy import select

from src.db.engine import async_session_factory
from src.db.models import Cotizacion, SolicitudAgente

logger = logging.getLogger(__name__)


@tool
async def calcular_cotizacion(
    tipo_servicio: str,
    idioma_destino: str,
    cantidad: float,
    fecha_inicio: str,
    fecha_fin: str,
    num_interpretes: int = 2,
    num_receptores: int = 0,
    num_dias: int = 1,
    idioma_origen: str = "español",
    ubicacion: str = "",
    state: Annotated[dict, InjectedState] = None,
) -> str:
    """
    Consulta las tarifas reales de la base de datos y crea un borrador de cotización numerado.
    Devuelve un JSON con las líneas de precio, subtotal, IVA y total.

    Llama esta herramienta cuando ya tienes TODOS los datos del servicio recopilados,
    incluyendo obligatoriamente las fechas del evento.

    tipo_servicio: interpretacion_simultanea_presencial | interpretacion_simultanea_virtual |
                   interpretacion_consecutiva | traduccion_documentos | transcripcion
    idioma_destino: idioma destino (ej: "inglés", "francés", "portugués").
    idioma_origen: idioma origen, default "español".
    cantidad: horas totales para interpretación (días × horas/día), palabras para traducción,
              minutos para transcripción.
    fecha_inicio: fecha de inicio del evento en formato YYYY-MM-DD (ej: "2026-05-20"). OBLIGATORIO.
    fecha_fin: fecha de fin del evento en formato YYYY-MM-DD. Si es un solo día, igual a fecha_inicio.
    num_interpretes: intérpretes simultáneos. Siempre 2 si la sesión supera 1.5 horas.
    num_receptores: receptores de simultánea necesarios (0 si no aplica).
    num_dias: días de duración del evento (para cálculo de equipos).
    ubicacion: ciudad y lugar del evento (para detectar recargo fuera de Bogotá).
    """
    from src.services.cotizacion import calcular_borrador

    cliente_id = state.get("cliente_id") if state else None
    if not cliente_id:
        return json.dumps({
            "error": True,
            "mensaje": "No hay cliente identificado en la conversación. Verifica que el cliente esté registrado en DB.",
        }, ensure_ascii=False)

    result = await calcular_borrador(
        cliente_id=cliente_id,
        contacto_id=state.get("contacto_id"),
        conversacion_id=state.get("conversacion_id"),
        tipo_servicio=tipo_servicio,
        idioma_destino=idioma_destino,
        idioma_origen=idioma_origen,
        cantidad=cantidad,
        num_interpretes=num_interpretes,
        num_receptores=num_receptores,
        num_dias=num_dias,
        ubicacion=ubicacion or state.get("ubicacion", ""),
        horario=state.get("horario", ""),
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
    )

    if result.get("error"):
        logger.warning(f"calcular_cotizacion error: {result['mensaje']}")
    else:
        logger.info(
            f"calcular_cotizacion OK: {result['numero_cotizacion']} "
            f"total={result['total_formateado']}"
        )

    return json.dumps(result, ensure_ascii=False)


@tool
async def enviar_cotizacion(
    cotizacion_id: int,
    mensaje_acompanamiento: str = "",
    state: Annotated[dict, InjectedState] = None,
) -> str:
    """
    Genera el PDF de la cotización y lo envía al cliente por WhatsApp.
    Llama esta herramienta DESPUÉS de calcular_cotizacion y de presentar el resumen.

    cotizacion_id: ID retornado por calcular_cotizacion.
    mensaje_acompanamiento: Texto breve que acompaña el PDF (máx 2 oraciones).
    """
    from src.services.documento import docx_a_pdf, generar_word
    from src.storage.s3 import upload_cotizacion
    from src.whatsapp.client import WhatsAppClient

    phone = state.get("phone", "") if state else ""
    if not phone:
        return json.dumps({"error": True, "mensaje": "No hay número de teléfono en estado."}, ensure_ascii=False)

    # 1. Obtener número de cotización para el nombre del archivo
    async with async_session_factory() as db:
        result = await db.execute(select(Cotizacion).where(Cotizacion.id == cotizacion_id))
        cot = result.scalar_one_or_none()

    if not cot:
        return json.dumps({"error": True, "mensaje": f"Cotización {cotizacion_id} no encontrada."}, ensure_ascii=False)

    numero = cot.numero_cotizacion

    try:
        # 2. Generar Word → PDF
        logger.info(f"Generando Word para cotización {numero}...")
        docx_bytes = await generar_word(cotizacion_id)

        logger.info(f"Convirtiendo a PDF con LibreOffice...")
        pdf_bytes = docx_a_pdf(docx_bytes)

        # 3. Subir a S3
        logger.info(f"Subiendo PDF a S3...")
        url = await upload_cotizacion(cotizacion_id, pdf_bytes, numero)

        # 4. Enviar por WhatsApp
        caption = mensaje_acompanamiento or (
            "Adjunto encontrará su cotización formal. "
            "Quedamos atentos a sus comentarios."
        )
        wa = WhatsAppClient()
        await wa.send_document(
            to=phone,
            document_url=url,
            filename=f"{numero}.pdf",
            caption=caption,
        )
        logger.info(f"Cotización {numero} enviada a {phone}")

        # 5. Marcar como enviada
        async with async_session_factory() as db:
            db_cot = await db.get(Cotizacion, cotizacion_id)
            if db_cot:
                db_cot.estado = "enviada"
                await db.commit()

        return json.dumps({
            "enviada": True,
            "cotizacion_id": cotizacion_id,
            "numero_cotizacion": numero,
            "url": url,
        }, ensure_ascii=False)

    except Exception as e:
        logger.error(f"Error enviando cotización {cotizacion_id}: {e}", exc_info=True)
        return json.dumps({
            "error": True,
            "mensaje": f"Error generando o enviando el PDF: {e}. Usa crear_solicitud(tipo='consulta_precio') para escalar.",
        }, ensure_ascii=False)


@tool
async def crear_solicitud(
    tipo: str,
    titulo: str,
    descripcion: str,
    state: Annotated[dict, InjectedState] = None,
) -> str:
    """
    Crea una solicitud de atención en el dashboard de María Luisa.
    Úsala cuando no puedas resolver el caso de forma autónoma.

    tipo: "consulta_precio" | "descuento_especial" | "servicio_no_catalogado" | "atencion_humana"
    titulo: Resumen en una línea (máx 200 caracteres) de lo que necesita María Luisa.
    descripcion: Contexto completo del caso (empresa, servicio, fecha, problema).
    """
    st = state or {}
    async with async_session_factory() as db:
        solicitud = SolicitudAgente(
            cliente_id=st.get("cliente_id"),
            cotizacion_id=st.get("cotizacion_id"),
            conversacion_id=st.get("conversacion_id"),
            tipo=tipo,
            estado="pendiente",
            prioridad="normal",
            titulo=titulo[:200],
            descripcion=descripcion,
            datos_formulario={
                "phone": st.get("phone"),
                "nombre": st.get("nombre"),
                "empresa": st.get("empresa"),
                "servicio": st.get("servicio"),
                "idioma": st.get("idioma"),
                "fecha": st.get("fecha"),
                "ubicacion": st.get("ubicacion"),
                "cantidad": st.get("cantidad"),
            },
        )
        db.add(solicitud)
        await db.commit()
        await db.refresh(solicitud)

    logger.info(f"Solicitud creada: id={solicitud.id} tipo={tipo} titulo={titulo!r}")
    return json.dumps({
        "solicitud_id": solicitud.id,
        "tipo": tipo,
        "mensaje_para_cliente": "He escalado su caso a nuestra encargada. Ella le contactara a la brevedad.",
    }, ensure_ascii=False)


@tool
async def actualizar_cotizacion(
    cotizacion_id: int,
    estado: str,
    motivo: str = "",
) -> str:
    """
    Actualiza el estado de una cotizacion segun la decision del cliente.
    Llamar despues de que el cliente responde si aprueba, rechaza o pide cambios.

    cotizacion_id: ID de la cotizacion (el mismo retornado por calcular_cotizacion).
    estado: Decision del cliente — uno de: "aprobada", "rechazada", "a_modificar".
    motivo: Razon opcional (requerida si es rechazada para registrar feedback).
    """
    estados_validos = {"aprobada", "rechazada", "a_modificar"}
    if estado not in estados_validos:
        return json.dumps({
            "error": True,
            "mensaje": f"Estado invalido '{estado}'. Debe ser: aprobada, rechazada o a_modificar.",
        }, ensure_ascii=False)

    async with async_session_factory() as db:
        cot = await db.get(Cotizacion, cotizacion_id)
        if not cot:
            return json.dumps({
                "error": True,
                "mensaje": f"Cotizacion {cotizacion_id} no encontrada.",
            }, ensure_ascii=False)

        cot.estado = estado
        cot.fecha_respuesta = datetime.date.today()
        if estado == "rechazada" and motivo:
            cot.razon_perdida = motivo
        await db.commit()

    logger.info(f"Cotizacion {cotizacion_id} actualizada a estado={estado!r}")
    return json.dumps({
        "ok": True,
        "cotizacion_id": cotizacion_id,
        "numero_cotizacion": cot.numero_cotizacion,
        "estado": estado,
    }, ensure_ascii=False)
