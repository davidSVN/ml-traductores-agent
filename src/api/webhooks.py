import datetime
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from langchain_core.messages import HumanMessage
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.db.engine import get_db
from src.db.models import Conversacion, Mensaje
from src.whatsapp.client import WhatsAppClient

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/webhook", tags=["webhook"])
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

    # Get or create conversation (for dashboard / mensajes table)
    conv_result = await db.execute(
        select(Conversacion)
        .where(Conversacion.telefono_whatsapp == phone)
        .order_by(desc(Conversacion.id))
        .limit(1)
    )
    conversacion = conv_result.scalar_one_or_none()

    if not conversacion:
        conversacion = Conversacion(telefono_whatsapp=phone, canal="whatsapp", estado="activa")
        db.add(conversacion)
        await db.flush()

    # Save incoming message to mensajes table (for dashboard)
    msg_cliente = Mensaje(
        conversacion_id=conversacion.id,
        origen="cliente",
        contenido=text,
        tipo_contenido="texto",
        whatsapp_message_id=wa_msg_id,
    )
    db.add(msg_cliente)
    await db.flush()

    # Update conversation summary with incoming message
    now = datetime.datetime.now(datetime.timezone.utc)
    conversacion.ultimo_mensaje_at = now
    conversacion.ultimo_mensaje_preview = text[:100]
    conversacion.mensajes_no_leidos = (conversacion.mensajes_no_leidos or 0) + 1

    # Run LangGraph — thread_id ties this to the conversation history in the checkpointer
    graph = request.app.state.graph
    config = {"configurable": {"thread_id": f"wa_{phone}"}}

    result = await graph.ainvoke(
        {
            "messages": [HumanMessage(content=text)],
            "phone": phone,
            "conversacion_id": conversacion.id,
        },
        config=config,
    )

    respuesta = result["messages"][-1].content

    # Update conversation link to client if resolved by LangGraph
    cliente_id = result.get("cliente_id")
    if cliente_id and not conversacion.cliente_id:
        conversacion.cliente_id = cliente_id

    # Save agent response to mensajes table (for dashboard)
    msg_agente = Mensaje(
        conversacion_id=conversacion.id,
        origen="agente",
        contenido=respuesta,
        tipo_contenido="texto",
    )
    db.add(msg_agente)

    # Update conversation summary with agent response
    conversacion.ultimo_mensaje_at = datetime.datetime.now(datetime.timezone.utc)
    conversacion.ultimo_mensaje_preview = respuesta[:100]

    # Send via WhatsApp
    await wa_client.send_text(phone, respuesta)

    await db.commit()
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
