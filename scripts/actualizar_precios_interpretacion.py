"""
Actualiza los servicios de interpretación en la DB al modelo de precios por día.
IDs 1-11 (categoria = 'interpretacion_vivo') pasan de por_hora a por_dia.
precio_cliente = 2.600.000 (día completo de 8h, precio de referencia para bandas).
Idempotente — se puede ejecutar múltiples veces.
"""
import asyncio
import selectors
import sys
from decimal import Decimal

from sqlalchemy import update

sys.path.insert(0, ".")

from src.db.engine import async_session_factory
from src.db.models import Servicio


async def run():
    async with async_session_factory() as db:
        result = await db.execute(
            update(Servicio)
            .where(Servicio.categoria == "interpretacion_vivo")
            .values(
                unidad_cobro="por_dia",
                precio_base=Decimal("2600000"),
                precio_cliente=Decimal("2600000"),
                markup_porcentaje=Decimal("0"),
            )
            .returning(Servicio.id, Servicio.nombre)
        )
        filas = result.fetchall()
        await db.commit()

    print(f"OK: {len(filas)} servicios actualizados:")
    for fila in filas:
        print(f"  id={fila.id} | {fila.nombre}")


if __name__ == "__main__":
    if sys.platform == "win32":
        loop = asyncio.SelectorEventLoop(selectors.SelectSelector())
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run())
    else:
        asyncio.run(run())
