"""
Reset de base de datos — ML Traductores
Borra clientes, contactos, cotizaciones, conversaciones y checkpoints de LangGraph.
NO toca: servicios, tarifas_alquiler_equipos, recargos, checkpoint_migrations.

Uso:
    .venv/Scripts/python.exe scripts/reset_db.py
"""
import asyncio
import selectors
import sys

sys.path.insert(0, ".")


TABLAS = [
    "mensajes_internos",
    "solicitudes_agente",
    "mensajes",
    "conversaciones",
    "seguimientos",
    "ordenes_servicio",
    "lineas_cotizacion",
    "versiones_cotizacion",
    "cotizaciones",
    "contactos",
    "clientes",
    "checkpoint_writes",
    "checkpoint_blobs",
    "checkpoints",
]


async def run():
    from src.db.engine import async_session_factory
    from sqlalchemy import text

    print("Iniciando reset de base de datos...\n")
    async with async_session_factory() as db:
        for tabla in TABLAS:
            result = await db.execute(text(f"DELETE FROM {tabla}"))
            print(f"  ✓ {tabla:<30} {result.rowcount} filas eliminadas")
        await db.commit()

    print("\nBase de datos limpia. Listo para empezar desde cero.")
    print("(servicios, tarifas y recargos intactos)")


if __name__ == "__main__":
    loop = asyncio.SelectorEventLoop(selectors.SelectSelector())
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run())
