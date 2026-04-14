import json
import logging

from langchain_core.tools import tool
from sqlalchemy import select

from src.db.engine import async_session_factory
from src.db.models import Cotizacion, Servicio, TarifaAlquilerEquipo

logger = logging.getLogger(__name__)


@tool
async def listar_servicios() -> str:
    """
    Lista todos los servicios activos que ofrece ML Traductores,
    incluyendo interpretación, traducción, transcripción y equipos de alquiler.
    Usa esta tool cuando el cliente pregunte qué servicios están disponibles o
    cuando necesites conocer los idiomas y modalidades actuales.
    """
    async with async_session_factory() as db:
        stmt = (
            select(Servicio)
            .where(Servicio.activo == True)  # noqa: E712
            .order_by(Servicio.nombre)
        )
        result = await db.execute(stmt)
        servicios = result.scalars().all()

        stmt_eq = (
            select(TarifaAlquilerEquipo.tipo_equipo, TarifaAlquilerEquipo.descripcion)
            .where(TarifaAlquilerEquipo.activo == True)  # noqa: E712
            .distinct()
            .order_by(TarifaAlquilerEquipo.tipo_equipo)
        )
        result_eq = await db.execute(stmt_eq)
        equipos = result_eq.all()

        return json.dumps({
            "servicios_profesionales": [
                {
                    "nombre": s.nombre,
                    "idioma_origen": s.idioma_origen,
                    "idioma_destino": s.idioma_destino,
                    "unidad_cobro": s.unidad_cobro,
                    "num_interpretes_default": s.num_interpretes_default,
                }
                for s in servicios
            ],
            "equipos_alquiler": [
                {"tipo": row.tipo_equipo, "descripcion": row.descripcion}
                for row in equipos
            ],
        }, ensure_ascii=False)


@tool
async def consultar_historial(cliente_id: int) -> str:
    """
    Consulta las últimas cotizaciones de un cliente existente.
    Úsala cuando el cliente ya esté identificado (tienes cliente_id) para ver
    su historial antes de cotizar o para adaptar el trato según su trayectoria.
    """
    async with async_session_factory() as db:
        stmt = (
            select(Cotizacion)
            .where(Cotizacion.cliente_id == cliente_id)
            .order_by(Cotizacion.fecha.desc())
            .limit(5)
        )
        result = await db.execute(stmt)
        cotizaciones = result.scalars().all()

        if not cotizaciones:
            return json.dumps({"tiene_historial": False, "cotizaciones": []})

        return json.dumps({
            "tiene_historial": True,
            "cotizaciones": [
                {
                    "numero": c.numero_cotizacion,
                    "fecha": c.fecha.isoformat() if c.fecha else None,
                    "total": float(c.total) if c.total is not None else None,
                    "estado": c.estado,
                    "notas_internas": c.notas_internas,
                }
                for c in cotizaciones
            ],
        }, ensure_ascii=False)


@tool
async def consultar_tarifas(tipo_servicio: str, idioma: str = "") -> str:
    """
    Consulta tarifas de un tipo de servicio específico.
    Úsala cuando necesites orientación de precios para un servicio concreto
    antes de hacer el cálculo formal en la siguiente fase.
    tipo_servicio: nombre o parte del nombre (ej: 'simultánea', 'traducción').
    idioma: idioma destino opcional (ej: 'ingles', 'frances').
    """
    async with async_session_factory() as db:
        stmt = select(Servicio).where(
            Servicio.nombre.ilike(f"%{tipo_servicio}%"),
            Servicio.activo == True,  # noqa: E712
        )
        if idioma:
            stmt = stmt.where(Servicio.idioma_destino == idioma)

        result = await db.execute(stmt)
        servicios = result.scalars().all()

        if not servicios:
            return json.dumps({"encontrado": False, "servicios": []})

        return json.dumps({
            "encontrado": True,
            "servicios": [
                {
                    "id": s.id,
                    "nombre": s.nombre,
                    "idioma_origen": s.idioma_origen,
                    "idioma_destino": s.idioma_destino,
                    "precio_cliente": float(s.precio_cliente),
                    "unidad_cobro": s.unidad_cobro,
                    "num_interpretes_default": s.num_interpretes_default,
                    "notas": s.notas,
                }
                for s in servicios
            ],
        }, ensure_ascii=False)
