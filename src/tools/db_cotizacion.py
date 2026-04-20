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
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import flag_modified

from src.db.models import Cotizacion, LineaCotizacion, Mensaje, MensajeInterno, SolicitudAgente

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
    horario: str = "",
    exento_iva: bool = None,
    state: Annotated[dict, InjectedState] = None,
) -> str:
    """
    Consulta las tarifas reales de la base de datos y crea un borrador de cotización numerado.
    Devuelve un JSON con las líneas de precio, subtotal, IVA y total.

    Llama esta herramienta cuando ya tienes TODOS los datos obligatorios:
    tipo_servicio, idioma, fechas, horario, lugar, horas/día, email destinatario, nombre, cargo, IVA.

    tipo_servicio: interpretacion_simultanea_presencial | interpretacion_simultanea_virtual |
                   interpretacion_consecutiva | traduccion_documentos | transcripcion
    idioma_destino: idioma destino (ej: "inglés", "francés", "portugués").
    idioma_origen: idioma origen, default "español".
    cantidad: para interpretación = horas POR DÍA (no el total). Traducción = palabras. Transcripción = minutos.
    fecha_inicio: fecha de inicio en formato YYYY-MM-DD. OBLIGATORIO.
    fecha_fin: fecha de fin en formato YYYY-MM-DD. Igual a fecha_inicio si es un solo día.
    num_interpretes: intérpretes simultáneos. Siempre 2 si la sesión supera 1.5 horas.
    num_receptores: receptores de simultánea necesarios (0 si no aplica).
    num_dias: días de duración del evento (para cálculo de equipos).
    ubicacion: ciudad y lugar del evento (para detectar recargo fuera de Bogotá).
    horario: horario del evento (ej: "8am a 5pm").
    exento_iva: True si el cliente es organismo internacional exento de IVA. False si es nacional.
                Si no se pasa, se usa el valor guardado en DB del cliente.
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
        horario=horario or state.get("horario", ""),
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        exento_iva_override=exento_iva,
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
    state: Annotated[dict, InjectedState] = None,
) -> str:
    """
    Genera el PDF de la cotización, lo sube a S3 para revisión interna y notifica al cliente
    por WhatsApp que su cotización está en proceso.

    El PDF NO se envía al cliente directamente. Se envía al correo del destinatario SOLO
    cuando María Luisa lo apruebe desde el panel de Aprobaciones.

    Llama esta herramienta DESPUÉS de calcular_cotizacion y de tener todos los datos obligatorios:
    email destinatario, nombre, cargo (deben estar en el state).

    cotizacion_id: ID retornado por calcular_cotizacion.
    """
    from src.services.documento import docx_a_pdf, generar_word
    from src.storage.s3 import upload_cotizacion
    from src.whatsapp.client import WhatsAppClient

    phone = state.get("phone", "") if state else ""
    if not phone:
        return json.dumps({"error": True, "mensaje": "No hay número de teléfono en estado."}, ensure_ascii=False)

    # Datos del destinatario desde state
    email_dest = state.get("email", "") if state else ""
    nombre_dest = state.get("nombre", "") if state else ""
    cargo_dest = state.get("cargo", "") if state else ""

    # 1. Obtener cotización completa con líneas, cliente y contacto
    async with async_session_factory() as db:
        result = await db.execute(
            select(Cotizacion)
            .options(
                selectinload(Cotizacion.lineas).selectinload(LineaCotizacion.servicio),
                selectinload(Cotizacion.cliente),
                selectinload(Cotizacion.contacto),
            )
            .where(Cotizacion.id == cotizacion_id)
        )
        cot = result.scalar_one_or_none()

    if not cot:
        return json.dumps({"error": True, "mensaje": f"Cotización {cotizacion_id} no encontrada."}, ensure_ascii=False)

    numero = cot.numero_cotizacion

    try:
        # 2. Generar Word → PDF (para revisión interna y envío futuro por email)
        logger.info(f"Generando PDF para cotización {numero}...")
        docx_bytes = await generar_word(cotizacion_id)
        pdf_bytes = docx_a_pdf(docx_bytes)

        # 3. Subir a S3 (María Luisa puede previsualizar en el panel)
        url = await upload_cotizacion(cotizacion_id, pdf_bytes, numero)

        # 4. Notificar al cliente por WhatsApp — SIN enviar el PDF
        email_display = f" al correo *{email_dest}*" if email_dest else ""
        wa = WhatsAppClient()
        await wa.send_text(
            phone,
            f"Estamos preparando su cotización formal *{numero}*. "
            f"En cuanto esté lista se la enviaremos{email_display}. Le notificaremos por aquí. 👍"
        )
        logger.info(f"Notificación WA enviada a {phone} — cotización {numero} en revisión interna")

        # 5. Guardar en DB + crear solicitud en panel de aprobaciones
        conversacion_id = state.get("conversacion_id") if state else None
        cliente_id = state.get("cliente_id") if state else None
        nombre = state.get("nombre", "") if state else ""
        empresa = state.get("empresa", "") if state else ""

        # Construir resumen de líneas ANTES de abrir sesión (cot cargado con selectinload)
        _lineas_texto = []
        for _linea in cot.lineas:
            _nombre_item = (
                _linea.servicio.nombre if _linea.servicio
                else _linea.descripcion_generada or "Ítem"
            )
            _idioma = f" ({_linea.servicio.idioma_destino})" if _linea.servicio and _linea.servicio.idioma_destino else ""
            _detalles = []
            if _linea.fecha_servicio_inicio:
                _fecha_str = _linea.fecha_servicio_inicio.strftime("%d/%m/%Y")
                if _linea.fecha_servicio_fin and _linea.fecha_servicio_fin != _linea.fecha_servicio_inicio:
                    _fecha_str += f" – {_linea.fecha_servicio_fin.strftime('%d/%m/%Y')}"
                _detalles.append(_fecha_str)
            if _linea.horario:
                _detalles.append(_linea.horario)
            if _linea.cantidad is not None:
                _detalles.append(f"{float(_linea.cantidad):g}h")
            if _linea.num_interpretes and _linea.num_interpretes > 1:
                _detalles.append(f"{_linea.num_interpretes} intérpretes")
            if _linea.num_equipos:
                _detalles.append(f"{_linea.num_equipos} equipos")
            _precio_fmt = f"${_linea.precio_total:,.0f}".replace(",", ".")
            _detalle_str = f" — {' · '.join(_detalles)}" if _detalles else ""
            _lineas_texto.append(f"  • {_nombre_item}{_idioma}{_detalle_str} → {_precio_fmt}")

        _resumen_lineas = "\n".join(_lineas_texto) if _lineas_texto else "  (sin líneas)"

        _cliente_label_pre = (
            (cot.cliente.nombre_empresa if cot.cliente else None)
            or nombre_dest or f"cliente {cliente_id}"
        )
        _subtotal_fmt = f"${cot.subtotal:,.0f}".replace(",", ".") if cot.subtotal else "—"
        _iva_fmt = f"${cot.iva:,.0f}".replace(",", ".") if cot.iva else "—"
        _total_fmt = f"${cot.total:,.0f}".replace(",", ".") if cot.total else "—"
        _iva_linea = f"  IVA (19%):    {_iva_fmt}\n" if not cot.exento_iva else "  (Exento de IVA)\n"
        _ubicacion_linea = f"📍 {cot.ubicacion_evento}\n" if cot.ubicacion_evento else ""
        _dest_linea = f"📧 Destinatario: {nombre_dest}" + (f" ({cargo_dest})" if cargo_dest else "") + f" — {email_dest}\n" if nombre_dest or email_dest else ""

        _contenido_mensaje = (
            f"Nueva cotización {numero} lista para revisión — {_cliente_label_pre}.\n\n"
            f"{_dest_linea}"
            f"{_ubicacion_linea}"
            f"📋 Servicios cotizados:\n{_resumen_lineas}\n\n"
            f"💰 Resumen de valor:\n"
            f"  Subtotal:     {_subtotal_fmt}\n"
            f"{_iva_linea}"
            f"  Total:        {_total_fmt}\n\n"
            f"Aprueba para enviar al cliente, modifica precios o rechaza."
        )

        async with async_session_factory() as db:
            db_cot = await db.get(Cotizacion, cotizacion_id)
            if db_cot:
                db_cot.estado = "enviada"

            if conversacion_id:
                db.add(Mensaje(
                    conversacion_id=conversacion_id,
                    origen="agente",
                    contenido=f"Cotización {numero} en revisión interna",
                    tipo_contenido="texto",
                ))

            # Datos completos para el panel (incluye email/nombre/cargo del destinatario)
            cliente_db = cot.cliente
            contacto_db = cot.contacto
            primera_linea = cot.lineas[0] if cot.lineas else None

            empresa_db = cliente_db.nombre_empresa if cliente_db else (empresa or "")
            nombre_db = contacto_db.nombre_completo if contacto_db else (nombre or "")
            cliente_label = empresa_db or nombre_db or f"cliente {cliente_id}"

            # email/nombre/cargo del destinatario: prioridad state > contacto DB
            email_final = email_dest or (contacto_db.email if contacto_db else None)
            nombre_final = nombre_dest or nombre_db
            cargo_final = cargo_dest or (contacto_db.cargo if contacto_db else None)

            datos = {
                "phone": phone,
                "empresa": empresa_db,
                "nombre": nombre_final,
                "cargo": cargo_final,
                "email": email_final,
                "email_destinatario": email_final,
                "nombre_destinatario": nombre_final,
                "cargo_destinatario": cargo_final,
                "ubicacion": cot.ubicacion_evento,
                "url_pdf": url,
            }
            if primera_linea:
                if primera_linea.servicio:
                    datos["servicio"] = primera_linea.servicio.nombre
                    datos["idioma"] = primera_linea.servicio.idioma_destino
                if primera_linea.fecha_servicio_inicio:
                    datos["fecha_inicio"] = str(primera_linea.fecha_servicio_inicio)
                if primera_linea.fecha_servicio_fin:
                    datos["fecha_fin"] = str(primera_linea.fecha_servicio_fin)
                if primera_linea.horario:
                    datos["horario"] = primera_linea.horario
                if primera_linea.cantidad is not None:
                    datos["cantidad"] = float(primera_linea.cantidad)
                if primera_linea.num_interpretes:
                    datos["interpretes"] = primera_linea.num_interpretes

            # Reutilizar solicitud existente del mismo cliente (un chat por cliente)
            existing_result = await db.execute(
                select(SolicitudAgente)
                .where(SolicitudAgente.cliente_id == cliente_id)
                .where(SolicitudAgente.tipo == "aprobar_cotizacion")
                .order_by(SolicitudAgente.created_at.desc())
                .limit(1)
            )
            existing = existing_result.scalar_one_or_none()

            es_actualizacion = existing is not None
            if existing:
                cotizacion_anterior_id = existing.cotizacion_id
                existing.cotizacion_id = cotizacion_id
                existing.estado = "pendiente"
                existing.datos_formulario = datos
                flag_modified(existing, "datos_formulario")
                existing.titulo = f"Cotizaciones de {cliente_label}"
                solicitud = existing
                await db.flush()

                if cotizacion_anterior_id and cotizacion_anterior_id != cotizacion_id:
                    cot_anterior = await db.get(Cotizacion, cotizacion_anterior_id)
                    if cot_anterior and cot_anterior.estado not in ("aprobada",):
                        cot_anterior.estado = "negociando"
                        logger.info(f"Cotización anterior {cotizacion_anterior_id} reemplazada por {cotizacion_id}")
            else:
                solicitud = SolicitudAgente(
                    cliente_id=cliente_id,
                    cotizacion_id=cotizacion_id,
                    conversacion_id=conversacion_id,
                    tipo="aprobar_cotizacion",
                    estado="pendiente",
                    prioridad="normal",
                    titulo=f"Cotizaciones de {cliente_label}",
                    descripcion=(
                        f"Cotización del agente para {cliente_label}. "
                        f"Revisar y aprobar para enviar al cliente por email."
                    ),
                    datos_formulario=datos,
                )
                db.add(solicitud)
                await db.flush()

            prefijo = "🔄 *Cotización actualizada* — cliente solicitó cambios.\n\n" if es_actualizacion else ""
            try:
                db.add(MensajeInterno(
                    solicitud_id=solicitud.id,
                    origen="agente",
                    contenido=prefijo + _contenido_mensaje,
                    tipo_contenido="texto",
                ))
            except Exception as e_msg:
                logger.error(f"Error creando MensajeInterno sol={solicitud.id}: {e_msg}", exc_info=True)

            await db.commit()
            await db.refresh(solicitud)

        logger.info(f"Solicitud aprobar_cotizacion creada automáticamente: id={solicitud.id} cot={numero}")

        return json.dumps({
            "enviada": True,
            "cotizacion_id": cotizacion_id,
            "numero_cotizacion": numero,
            "url": url,
            "solicitud_id": solicitud.id,
        }, ensure_ascii=False)

    except Exception as e:
        logger.error(f"Error procesando cotización {cotizacion_id}: {e}", exc_info=True)
        return json.dumps({
            "error": True,
            "mensaje": f"Error generando el PDF: {e}. Usa crear_solicitud(tipo='consulta_precio') para escalar.",
        }, ensure_ascii=False)


@tool
async def enviar_cotizacion_email(
    cotizacion_id: int,
    email: str,
    nombre_destinatario: str,
    numero_cotizacion: str,
) -> str:
    """
    [STUB — integración email pendiente]
    Registra la intención de enviar el PDF de cotización por correo electrónico.
    La integración real (SendGrid / AWS SES) se conectará aquí en una fase futura.

    Llamar SOLO desde handle_aprobacion cuando María Luisa aprueba.
    No llamar desde el agente directamente.

    cotizacion_id: ID de la cotización aprobada.
    email: correo del destinatario.
    nombre_destinatario: nombre completo a quien va dirigida.
    numero_cotizacion: número de la cotización (ej: COT-20260419-001).
    """
    import aiosmtplib
    import httpx
    from email import encoders
    from email.mime.base import MIMEBase
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    from src.config import get_settings

    settings = get_settings()

    if not settings.gmail_user or not settings.gmail_app_password:
        logger.error("enviar_cotizacion_email: GMAIL_USER o GMAIL_APP_PASSWORD no configurados")
        return json.dumps({"enviado": False, "error": "Credenciales Gmail no configuradas"}, ensure_ascii=False)

    # 1. Obtener url_pdf desde SolicitudAgente.datos_formulario
    async with async_session_factory() as db:
        result = await db.execute(
            select(SolicitudAgente)
            .where(SolicitudAgente.cotizacion_id == cotizacion_id)
            .where(SolicitudAgente.tipo == "aprobar_cotizacion")
            .order_by(SolicitudAgente.created_at.desc())
            .limit(1)
        )
        sol = result.scalar_one_or_none()

    url_pdf = (sol.datos_formulario or {}).get("url_pdf") if sol else None
    if not url_pdf:
        logger.error(f"enviar_cotizacion_email: sin url_pdf para cot {cotizacion_id}")
        return json.dumps({"enviado": False, "error": "No se encontró el PDF en S3"}, ensure_ascii=False)

    # 2. Descargar PDF desde S3
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url_pdf)
        r.raise_for_status()
        pdf_bytes = r.content

    # 3. Construir email MIME
    msg = MIMEMultipart()
    msg["From"] = f"ML Traductores <{settings.gmail_user}>"
    msg["To"] = f"{nombre_destinatario} <{email}>"
    msg["Subject"] = f"Cotización {numero_cotizacion} — ML Traductores"

    cuerpo = (
        f"Estimado/a {nombre_destinatario},\n\n"
        f"Adjunto encontrará la cotización formal {numero_cotizacion} de ML Traductores.\n\n"
        f"Quedamos atentos a sus comentarios y próximos pasos.\n\n"
        f"Atentamente,\nML Traductores"
    )
    msg.attach(MIMEText(cuerpo, "plain", "utf-8"))

    part = MIMEBase("application", "octet-stream")
    part.set_payload(pdf_bytes)
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f'attachment; filename="{numero_cotizacion}.pdf"')
    msg.attach(part)

    # 4. Enviar por SMTP Gmail (STARTTLS port 587)
    await aiosmtplib.send(
        msg,
        hostname="smtp.gmail.com",
        port=587,
        username=settings.gmail_user,
        password=settings.gmail_app_password,
        start_tls=True,
    )

    logger.info(f"Email enviado: {numero_cotizacion} → {email}")
    return json.dumps({
        "enviado": True,
        "email": email,
        "destinatario": nombre_destinatario,
        "numero_cotizacion": numero_cotizacion,
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
    # Mapeo LLM → valores reales del constraint estado_valido en DB
    # borrador | enviada | en_seguimiento | negociando | aprobada | perdida | vencida
    ESTADO_MAP = {
        "aprobada":    "aprobada",
        "rechazada":   "perdida",
        "a_modificar": "negociando",
    }
    estados_validos = set(ESTADO_MAP.keys())
    if estado not in estados_validos:
        return json.dumps({
            "error": True,
            "mensaje": f"Estado invalido '{estado}'. Debe ser: aprobada, rechazada o a_modificar.",
        }, ensure_ascii=False)

    estado_db = ESTADO_MAP[estado]

    async with async_session_factory() as db:
        cot = await db.get(Cotizacion, cotizacion_id)
        if not cot:
            return json.dumps({
                "error": True,
                "mensaje": f"Cotizacion {cotizacion_id} no encontrada.",
            }, ensure_ascii=False)

        cot.estado = estado_db
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


@tool
async def generar_contrato(
    cotizacion_id: int,
    state: Annotated[dict, InjectedState] = None,
) -> str:
    """
    Genera el PDF de confirmación de servicio (contrato) y lo envía por WhatsApp.
    Llama esta herramienta DESPUÉS de actualizar_cotizacion(id, "aprobada").
    Incluye los datos del servicio, condiciones económicas y datos bancarios para el anticipo.

    cotizacion_id: ID de la cotización aprobada.
    """
    from src.services.documento import docx_a_pdf, generar_word_contrato
    from src.storage.s3 import upload_contrato
    from src.whatsapp.client import WhatsAppClient

    phone = state.get("phone", "") if state else ""
    if not phone:
        return json.dumps({"error": True, "mensaje": "No hay número de teléfono en estado."}, ensure_ascii=False)

    async with async_session_factory() as db:
        cot = await db.get(Cotizacion, cotizacion_id)

    if not cot:
        return json.dumps({"error": True, "mensaje": f"Cotización {cotizacion_id} no encontrada."}, ensure_ascii=False)

    numero = cot.numero_cotizacion
    numero_cont = numero.replace("COT-", "CONT-")

    try:
        logger.info(f"Generando contrato para cotización {numero}...")
        docx_bytes = await generar_word_contrato(cotizacion_id)
        pdf_bytes = docx_a_pdf(docx_bytes)

        logger.info("Subiendo contrato a S3...")
        url = await upload_contrato(cotizacion_id, pdf_bytes, numero)

        caption = (
            f"Adjunto la confirmación formal de servicio *{numero_cont}*. "
            "Incluye los datos bancarios para el anticipo. Quedamos atentos."
        )
        wa = WhatsAppClient()
        await wa.send_document(
            to=phone,
            document_url=url,
            filename=f"{numero_cont}.pdf",
            caption=caption,
        )
        logger.info(f"Contrato {numero_cont} enviado a {phone}")

        conversacion_id = state.get("conversacion_id") if state else None
        async with async_session_factory() as db:
            if conversacion_id:
                db.add(Mensaje(
                    conversacion_id=conversacion_id,
                    origen="agente",
                    contenido=f"Contrato {numero_cont} enviado",
                    tipo_contenido="documento",
                    url_archivo=url,
                ))
            from src.db.models import Seguimiento
            db.add(Seguimiento(
                cotizacion_id=cotizacion_id,
                metodo="whatsapp",
                resultado="contrato_enviado",
            ))
            await db.commit()

        return json.dumps({
            "enviado": True,
            "cotizacion_id": cotizacion_id,
            "numero_contrato": numero_cont,
            "url": url,
        }, ensure_ascii=False)

    except Exception as e:
        logger.error(f"Error generando contrato {cotizacion_id}: {e}", exc_info=True)
        return json.dumps({
            "error": True,
            "mensaje": f"Error generando el contrato: {e}",
        }, ensure_ascii=False)
