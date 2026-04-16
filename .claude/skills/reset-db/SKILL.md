---
name: reset-db
description: Borra toda la data de clientes, contactos, cotizaciones, conversaciones y checkpoints de LangGraph. Deja intactas las tablas de servicios, tarifas y recargos. Úsalo cuando quieras empezar desde cero.
---

Ejecuta el siguiente script Python usando el intérprete del virtualenv del proyecto ML Traductores.

El proyecto está en: `C:/Users/david.vasquez/Documents/personal/ia para empresas/catizaciones-ml-traductores/ml-traductores-agent`

Corre este comando con la tool Bash:


cd "C:/Users/david.vasquez/Documents/personal/ia para empresas/catizaciones-ml-traductores/ml-traductores-agent" && .venv/Scripts/python.exe -c "
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
"


Tablas que NO se tocan: `servicios`, `tarifas_alquiler_equipos`, `recargos`, `checkpoint_migrations`.

Muestra el resultado de cada tabla eliminada y confirma con "Base de datos limpia. Listo para empezar desde cero."

G