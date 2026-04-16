import asyncio, selectors, sys
sys.path.insert(0, '.')

async def run():
from src.db.engine import async_session_factory
from sqlalchemy import text

tablas = [
    'mensajes_internos',
    'solicitudes_agente',
    'mensajes',
    'conversaciones',
    'seguimientos',
    'ordenes_servicio',
    'lineas_cotizacion',
    'versiones_cotizacion',
    'cotizaciones',
    'contactos',
    'clientes',
    'checkpoint_writes',
    'checkpoint_blobs',
    'checkpoints',
]

async with async_session_factory() as db:
    for tabla in tablas:
        result = await db.execute(text(f'DELETE FROM {tabla}'))
        print(f'OK: {tabla} — {result.rowcount} filas eliminadas')
    await db.commit()
print('DONE: base de datos limpia')

loop = asyncio.SelectorEventLoop(selectors.SelectSelector())
asyncio.set_event_loop(loop)
loop.run_until_complete(run())
