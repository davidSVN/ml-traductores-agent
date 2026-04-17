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
from src.db.models import Contacto, Cotizacion, Seguimiento
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
        "Hola {nombre}, le escribimos de *ML Traductores* para saber si tuvo la oportunidad "
        "de revisar la cotización *{numero}* por *${total}*. "
        "¿Tiene alguna pregunta o podemos confirmar el servicio?"
    ),
    # Seguimiento 2 — día 3
    (
        "Hola {nombre}, seguimos a su disposición en *ML Traductores*. "
        "La cotización *{numero}* por *${total}* sigue disponible. "
        "¿Podemos ayudarle a tomar una decisión o hacer algún ajuste?"
    ),
    # Seguimiento 3 — día 7
    (
        "Hola {nombre}, le recordamos que la cotización *{numero}* por *${total}* "
        "vence en los próximos días. Si desea confirmar el servicio o necesita alguna "
        "modificación, con gusto le atendemos antes de que expire. — *ML Traductores*"
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
    return {
        "ok": True,
        "seguimientos_enviados": procesadas,
        "cotizaciones_vencidas": vencidas,
        "errores": errores,
    }
