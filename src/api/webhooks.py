import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.agent.orchestrator import AgentOrchestrator
from src.config import get_settings
from src.db.engine import get_db
from src.db.models import Conversacion, Mensaje
from src.whatsapp.client import WhatsAppClient

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/webhook", tags=["webhook"])

orchestrator = AgentOrchestrator()
wa_client = WhatsAppClient()


@router.get("/whatsapp")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode", default=""),
    hub_verify_token: str = Query(alias="hub.verify_token", default=""),
    hub_challenge: str = Query(alias="hub.challenge", default=""),
):
    if hub_mode == "subscribe" and hub_verify_token == settings.meta_verify_token:
        logger.info("Webhook verified by Meta")
        return PlainTextResponse(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/whatsapp")
async def receive_message(request: Request, db: AsyncSession = Depends(get_db)):
    payload: dict[str, Any] = await request.json()

    message_data = _extract_message(payload)
    if not message_data:
        return {"status": "ignored"}

    phone = message_data["phone"]
    text = message_data["text"]
    wa_msg_id = message_data["wa_message_id"]

    # Check for duplicate message
    dup_check = await db.execute(
        select(Mensaje).where(Mensaje.whatsapp_message_id == wa_msg_id)
    )
    if dup_check.scalar_one_or_none():
        logger.info(f"Duplicate message ignored: {wa_msg_id}")
        return {"status": "duplicate"}

    # Get or create conversation
    conv_result = await db.execute(
        select(Conversacion).where(Conversacion.telefono_whatsapp == phone).limit(1)
    )
    conversacion = conv_result.scalar_one_or_none()

    if not conversacion:
        conversacion = Conversacion(telefono_whatsapp=phone, canal="whatsapp", estado="activa")
        db.add(conversacion)
        await db.flush()

    # Save incoming message
    msg_cliente = Mensaje(
        conversacion_id=conversacion.id,
        origen="cliente",
        contenido=text,
        tipo_contenido="texto",
        whatsapp_message_id=wa_msg_id,
    )
    db.add(msg_cliente)
    await db.flush()

    # Load last 50 messages as conversation history
    hist_result = await db.execute(
        select(Mensaje)
        .where(Mensaje.conversacion_id == conversacion.id)
        .order_by(Mensaje.created_at.desc())
        .limit(50)
    )
    mensajes_db = list(reversed(hist_result.scalars().all()))

    history = [
        {
            "role": "user" if m.origen == "cliente" else "assistant",
            "content": m.contenido,
        }
        for m in mensajes_db
    ]

    # Run agent
    respuesta = await orchestrator.handle_message(history, db, phase="inicial")

    # Save agent response
    msg_agente = Mensaje(
        conversacion_id=conversacion.id,
        origen="agente",
        contenido=respuesta,
        tipo_contenido="texto",
    )
    db.add(msg_agente)

    # Send via WhatsApp
    await wa_client.send_text(phone, respuesta)

    return {"status": "ok"}


def _extract_message(payload: dict) -> dict | None:
    try:
        entry = payload["entry"][0]
        change = entry["changes"][0]["value"]
        messages = change.get("messages")
        if not messages:
            return None
        msg = messages[0]
        if msg.get("type") != "text":
            return None
        return {
            "phone": msg["from"],
            "text": msg["text"]["body"],
            "wa_message_id": msg["id"],
        }
    except (KeyError, IndexError, TypeError):
        return None
