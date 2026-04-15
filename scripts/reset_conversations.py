"""
Reset script — borra conversaciones, clientes, contactos y checkpoints de LangGraph.
Uso: python -m scripts.reset_conversations
"""
import asyncio
import selectors
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from src.config import get_settings


async def reset():
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=True)

    async with engine.begin() as conn:
        print("\n=== BORRANDO DATOS DE PANEL ===")
        await conn.execute(text("DELETE FROM mensajes_internos"))
        await conn.execute(text("DELETE FROM solicitudes_agente"))
        await conn.execute(text("DELETE FROM mensajes"))
        await conn.execute(text("DELETE FROM conversaciones"))
        print("OK: mensajes_internos, solicitudes_agente, mensajes, conversaciones borradas")

        print("\n=== BORRANDO CLIENTES Y CONTACTOS ===")
        await conn.execute(text("DELETE FROM seguimientos"))
        await conn.execute(text("DELETE FROM ordenes_servicio"))
        await conn.execute(text("DELETE FROM lineas_cotizacion"))
        await conn.execute(text("DELETE FROM versiones_cotizacion"))
        await conn.execute(text("DELETE FROM cotizaciones"))
        await conn.execute(text("DELETE FROM contactos"))
        await conn.execute(text("DELETE FROM clientes"))
        print("OK: cotizaciones, contactos, clientes borrados")

        print("\n=== BORRANDO CHECKPOINTS DE LANGGRAPH ===")
        for table in ["checkpoint_blobs", "checkpoint_writes", "checkpoints"]:
            try:
                await conn.execute(text(f"DELETE FROM {table}"))
                print(f"OK: {table} borrada")
            except Exception as e:
                print(f"  {table} no existe o no se pudo borrar: {e}")

    await engine.dispose()
    print("\nDONE: Reset completo. Puedes empezar conversaciones frescas.")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.run(
            reset(),
            loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()),
        )
    else:
        asyncio.run(reset())
