"""
Cron endpoint para seguimiento automático de cotizaciones.
Railway lo ejecuta cada hora vía HTTP POST con header X-Cron-Secret.

Lógica:
  - Día 1: cotizaciones enviadas hace >= 1 día, 0 seguimientos automáticos
  - Día 3: cotizaciones enviadas hace >= 3 días, 1 seguimiento automático
  - Día 7: cotizaciones enviadas hace >= 7 días, 2 seguimientos automáticos
  - Día 8+: 3 seguimientos realizados → estado = "vencida"

Configura en Railway:
  Cron: 0 * * * *  (cada hora)
  Command: curl -X POST https://<tu-dominio>/cron/seguimiento -H "X-Cron-Secret: <CRON_SECRET>"
"""
import datetime
import logging

from fastapi import APIRouter, Header, HTTPException
from sqlalchemy import func, select

from src.config import get_settings
from src.db.engine import async_session_factory
from src.db.models import Cliente, Contacto, Cotizacion, LineaCotizacion, Seguimiento, SolicitudAgente
from src.whatsapp.client import WhatsAppClient

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/cron", tags=["cron"])

# Días de espera por número de seguimiento ya enviado
SCHEDULE = {
    0: 1,   # 0 seguimientos → enviar al día 1
    1: 3,   # 1 seguimiento  → enviar al día 3
    2: 7,   # 2 seguimientos → enviar al día 7
}
MAX_SEGUIMIENTOS = 3
DIAS_VENCIMIENTO = 8


MENSAJES_SEGUIMIENTO = [
    # Seguimiento 1 — día 1
    (
        "Hola {nombre}, le escribimos de *ML Traductores*. "
        "¿Recibió la cotización *{numero}* que le enviamos al correo? "
        "Si tiene alguna pregunta o desea confirmar el servicio, con gusto le atendemos."
    ),
    # Seguimiento 2 — día 3
    (
        "Hola {nombre}, seguimos a su disposición en *ML Traductores*. "
        "¿Pudo revisar la cotización *{numero}* por *${total}*? "
        "Si no la encontró en su bandeja de entrada, con gusto la reenviamos. "
        "¿Podemos confirmar el servicio?"
    ),
    # Seguimiento 3 — día 7
    (
        "Hola {nombre}, la cotización *{numero}* por *${total}* está próxima a vencer. "
        "Si desea confirmar el servicio o necesita algún ajuste, "
        "estamos disponibles para atenderle. — *ML Traductores*"
    ),
]


@router.post("/seguimiento")
async def run_seguimiento(x_cron_secret: str = Header(default="")):
    if x_cron_secret != settings.cron_secret:
        raise HTTPException(status_code=403, detail="Unauthorized")

    hoy = datetime.date.today()
    procesadas = 0
    vencidas = 0
    errores = 0

    async with async_session_factory() as db:
        # Cotizaciones en estado "enviada" con fecha_envio definida
        result = await db.execute(
            select(Cotizacion)
            .where(Cotizacion.estado == "enviada")
            .where(Cotizacion.fecha_envio.isnot(None))
        )
        cotizaciones = result.scalars().all()

    for cot in cotizaciones:
        try:
            dias_transcurridos = (hoy - cot.fecha_envio).days

            # Contar seguimientos automáticos ya enviados
            async with async_session_factory() as db:
                count_result = await db.execute(
                    select(func.count(Seguimiento.id))
                    .where(Seguimiento.cotizacion_id == cot.id)
                    .where(Seguimiento.metodo == "whatsapp_automatico")
                )
                num_seguimientos = count_result.scalar() or 0

            # Marcar como vencida si superó límite
            if num_seguimientos >= MAX_SEGUIMIENTOS or dias_transcurridos >= DIAS_VENCIMIENTO:
                async with async_session_factory() as db:
                    db_cot = await db.get(Cotizacion, cot.id)
                    if db_cot and db_cot.estado == "enviada":
                        db_cot.estado = "vencida"
                        db_cot.fecha_cierre = hoy
                        await db.commit()
                        vencidas += 1
                        logger.info(f"Cotización {cot.numero_cotizacion} marcada como vencida")
                continue

            # Verificar si toca enviar seguimiento según el schedule
            dias_requeridos = SCHEDULE.get(num_seguimientos)
            if dias_requeridos is None or dias_transcurridos < dias_requeridos:
                continue

            # Obtener teléfono del contacto
            if not cot.contacto_id:
                continue

            async with async_session_factory() as db:
                contacto = await db.get(Contacto, cot.contacto_id)

            if not contacto or not contacto.telefono:
                logger.warning(f"Cotización {cot.numero_cotizacion}: contacto sin teléfono")
                continue

            # Formatear mensaje
            nombre = contacto.nombre_completo.split()[0] if contacto.nombre_completo else "cliente"
            total_fmt = f"{int(cot.total):,}".replace(",", ".") if cot.total else "—"
            mensaje = MENSAJES_SEGUIMIENTO[num_seguimientos].format(
                nombre=nombre,
                numero=cot.numero_cotizacion,
                total=total_fmt,
            )

            # Enviar WhatsApp
            wa = WhatsAppClient()
            await wa.send_text(contacto.telefono, mensaje)

            # Registrar seguimiento
            async with async_session_factory() as db:
                db.add(Seguimiento(
                    cotizacion_id=cot.id,
                    metodo="whatsapp_automatico",
                    resultado=f"seguimiento_{num_seguimientos + 1}_enviado",
                    proximo_seguimiento=hoy + datetime.timedelta(
                        days=SCHEDULE.get(num_seguimientos + 1, 999)
                    ) if num_seguimientos + 1 < MAX_SEGUIMIENTOS else None,
                ))
                await db.commit()

            procesadas += 1
            logger.info(
                f"Seguimiento {num_seguimientos + 1} enviado: "
                f"{cot.numero_cotizacion} → {contacto.telefono}"
            )

        except Exception as e:
            errores += 1
            logger.error(f"Error procesando cotización {cot.numero_cotizacion}: {e}", exc_info=True)

    logger.info(f"Cron seguimiento: {procesadas} enviados, {vencidas} vencidas, {errores} errores")

    # ── Bloque 2: recordatorio 1h post-email (ML aprobó → email al cliente) ──────
    recordatorios_1h = await _run_recordatorio_1h()

    # ── Bloque 3: recordatorios pre-evento por datos de facturación faltantes ─────
    recordatorios_facturacion = await _run_recordatorios_facturacion()

    return {
        "ok": True,
        "seguimientos_enviados": procesadas,
        "cotizaciones_vencidas": vencidas,
        "errores": errores,
        "recordatorios_1h": recordatorios_1h,
        "recordatorios_facturacion": recordatorios_facturacion,
    }


async def _run_recordatorio_1h() -> int:
    """
    Envía WhatsApp ~1h después de que ML aprueba y el email sale al cliente,
    preguntando si pudo revisar la cotización.
    Ventana: SolicitudAgente resuelta entre 30min y 3h atrás (tolerante al cron horario).
    """
    ahora = datetime.datetime.utcnow()
    limite_min = ahora - datetime.timedelta(minutes=30)
    limite_max = ahora - datetime.timedelta(hours=3)
    enviados = 0

    async with async_session_factory() as db:
        result = await db.execute(
            select(SolicitudAgente)
            .where(SolicitudAgente.estado == "aprobada")
            .where(SolicitudAgente.tipo == "aprobar_cotizacion")
            .where(SolicitudAgente.resuelta_at.isnot(None))
            .where(SolicitudAgente.resuelta_at <= limite_min)
            .where(SolicitudAgente.resuelta_at >= limite_max)
        )
        solicitudes = result.scalars().all()

    for sol in solicitudes:
        try:
            if not sol.cotizacion_id:
                continue

            # Verificar que no se haya enviado ya este recordatorio
            async with async_session_factory() as db:
                ya_enviado = await db.execute(
                    select(func.count(Seguimiento.id))
                    .where(Seguimiento.cotizacion_id == sol.cotizacion_id)
                    .where(Seguimiento.metodo == "whatsapp_aprobacion_1h")
                )
                if (ya_enviado.scalar() or 0) > 0:
                    continue

                # Verificar que el cliente no haya aprobado ya (cotizacion sigue en "aprobada" por ML pero el cliente no respondió)
                cot = await db.get(Cotizacion, sol.cotizacion_id)
                if not cot:
                    continue

            datos = sol.datos_formulario or {}
            phone = datos.get("phone", "")
            nombre = (datos.get("nombre") or "").split()[0] or "cliente"
            numero = datos.get("numero_cotizacion") or (cot.numero_cotizacion if cot else "")

            if not phone:
                continue

            mensaje = (
                f"Hola {nombre}, ¿pudo revisar la cotización *{numero}* "
                f"que le enviamos al correo? Cuando guste confirmamos. — *ML Traductores*"
            )

            wa = WhatsAppClient()
            await wa.send_text(phone, mensaje)

            async with async_session_factory() as db:
                db.add(Seguimiento(
                    cotizacion_id=sol.cotizacion_id,
                    metodo="whatsapp_aprobacion_1h",
                    resultado="recordatorio_revision_enviado",
                ))
                await db.commit()

            enviados += 1
            logger.info(f"Recordatorio 1h enviado: {numero} → {phone}")

        except Exception as e:
            logger.error(f"Error recordatorio 1h sol={sol.id}: {e}", exc_info=True)

    return enviados


# Días previos al evento en los que se envía recordatorio de facturación
DIAS_RECORDATORIO_FACTURACION = [10, 5, 3, 1]

MENSAJES_FACTURACION = {
    10: (
        "Hola {nombre}, su evento de *{servicio}* está programado para el *{fecha}*. "
        "Para tener lista la factura a tiempo, ¿me confirma {datos_faltantes} de *{empresa}*?"
    ),
    5: (
        "Hola {nombre}, en *5 días* es su evento. "
        "Aún nos falta {datos_faltantes} para emitir la factura. ¿Nos lo puede confirmar hoy?"
    ),
    3: (
        "Hola {nombre}, quedan *3 días* para el evento. "
        "Para no tener demoras con la facturación necesitamos {datos_faltantes}. ¿Lo tiene disponible?"
    ),
    1: (
        "Hola {nombre}, *mañana es el evento*. "
        "Para emitir la factura después del servicio necesitamos {datos_faltantes}. "
        "¿Nos lo confirma ahora? — *ML Traductores*"
    ),
}


async def _run_recordatorios_facturacion() -> int:
    """
    Envía recordatorios de WhatsApp a -10, -5, -3 y -1 días del evento
    cuando faltan datos de facturación (NIT, RUT, orden de compra).
    """
    hoy = datetime.date.today()
    enviados = 0

    async with async_session_factory() as db:
        result = await db.execute(
            select(Cotizacion)
            .join(Cliente, Cotizacion.cliente_id == Cliente.id)
            .where(Cotizacion.estado == "aprobada")
            .where(Cotizacion.contacto_id.isnot(None))
        )
        cotizaciones = result.scalars().all()

    for cot in cotizaciones:
        try:
            # Obtener fecha del evento desde primera línea
            async with async_session_factory() as db:
                linea_result = await db.execute(
                    select(LineaCotizacion)
                    .where(LineaCotizacion.cotizacion_id == cot.id)
                    .where(LineaCotizacion.fecha_servicio_inicio.isnot(None))
                    .order_by(LineaCotizacion.fecha_servicio_inicio)
                    .limit(1)
                )
                linea = linea_result.scalar_one_or_none()

            if not linea or not linea.fecha_servicio_inicio:
                continue

            dias_al_evento = (linea.fecha_servicio_inicio - hoy).days
            if dias_al_evento not in DIAS_RECORDATORIO_FACTURACION:
                continue

            # Obtener cliente para verificar datos faltantes
            async with async_session_factory() as db:
                cliente = await db.get(Cliente, cot.cliente_id)
                contacto = await db.get(Contacto, cot.contacto_id)

            if not cliente or not contacto or not contacto.telefono:
                continue

            # Determinar qué falta
            faltantes = []
            if not cliente.nit:
                faltantes.append("el NIT")
            if not cliente.tiene_rut or not cliente.numero_rut:
                faltantes.append("el número de RUT")
            if not cot.numero_orden_compra:
                faltantes.append("la orden de compra (si manejan)")

            if not faltantes:
                continue  # Todo completo, no enviar

            # Verificar que no se haya enviado ya para este intervalo
            metodo_clave = f"recordatorio_facturacion_{dias_al_evento}d"
            async with async_session_factory() as db:
                ya_enviado = await db.execute(
                    select(func.count(Seguimiento.id))
                    .where(Seguimiento.cotizacion_id == cot.id)
                    .where(Seguimiento.metodo == metodo_clave)
                )
                if (ya_enviado.scalar() or 0) > 0:
                    continue

            nombre = (contacto.nombre_completo or "").split()[0] or "cliente"
            empresa = cliente.nombre_empresa or "su empresa"
            fecha_fmt = linea.fecha_servicio_inicio.strftime("%d/%m/%Y")
            datos_faltantes_str = " y ".join(faltantes)

            servicio_nombre = "servicio"
            async with async_session_factory() as db:
                linea_full = await db.execute(
                    select(LineaCotizacion)
                    .where(LineaCotizacion.cotizacion_id == cot.id)
                    .limit(1)
                )
                l = linea_full.scalar_one_or_none()
                if l and l.descripcion_generada:
                    servicio_nombre = l.descripcion_generada.split()[0].lower()

            mensaje = MENSAJES_FACTURACION[dias_al_evento].format(
                nombre=nombre,
                servicio=servicio_nombre,
                fecha=fecha_fmt,
                empresa=empresa,
                datos_faltantes=datos_faltantes_str,
            )

            wa = WhatsAppClient()
            await wa.send_text(contacto.telefono, mensaje)

            async with async_session_factory() as db:
                db.add(Seguimiento(
                    cotizacion_id=cot.id,
                    metodo=metodo_clave,
                    resultado=f"recordatorio_facturacion_enviado_{dias_al_evento}d_antes",
                ))
                await db.commit()

            enviados += 1
            logger.info(
                f"Recordatorio facturación -{dias_al_evento}d: "
                f"{cot.numero_cotizacion} → {contacto.telefono} (faltan: {faltantes})"
            )

        except Exception as e:
            logger.error(f"Error recordatorio facturación cot={cot.id}: {e}", exc_info=True)

    return enviados
