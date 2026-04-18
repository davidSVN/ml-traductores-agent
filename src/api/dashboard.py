import asyncio
import datetime
import logging
from typing import Generic, Optional, TypeVar

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.engine import async_session_factory, get_db
from src.db.models import (
    Cliente,
    Contacto,
    Conversacion,
    Cotizacion,
    LineaCotizacion,
    Mensaje,
    MensajeInterno,
    Servicio,
    SolicitudAgente,
    TarifaAlquilerEquipo,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

T = TypeVar("T")


# ─────────────────────────────────────────
# SCHEMAS GENÉRICOS
# ─────────────────────────────────────────


class PaginationMeta(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    data: list[T]
    meta: PaginationMeta


# ─────────────────────────────────────────
# SCHEMAS DE SALIDA
# ─────────────────────────────────────────


class StatsOut(BaseModel):
    conversaciones_activas: int
    cotizaciones_total: int
    cotizaciones_este_mes: int
    ingresos_total: float
    ingresos_este_mes: float
    solicitudes_pendientes: int
    clientes_total: int


class ConversacionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    cliente_id: Optional[int]
    cliente_nombre: Optional[str] = None
    nombre_temporal: Optional[str]
    telefono_whatsapp: Optional[str]
    estado: str
    ultimo_mensaje_preview: Optional[str]
    ultimo_mensaje_at: Optional[datetime.datetime]
    mensajes_no_leidos: Optional[int]
    created_at: Optional[datetime.datetime]


class MensajeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    origen: str
    contenido: str
    tipo_contenido: str
    url_archivo: Optional[str]
    created_at: Optional[datetime.datetime]


class ConversacionDetalleOut(BaseModel):
    id: int
    nombre_temporal: Optional[str]
    telefono_whatsapp: Optional[str]
    estado: str
    cliente_nombre: Optional[str]


class MensajesResponse(BaseModel):
    conversacion: ConversacionDetalleOut
    mensajes: list[MensajeOut]
    has_more: bool


class ClienteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre_empresa: Optional[str]
    tipo_cliente: Optional[str]
    nit: Optional[str]
    es_recurrente: Optional[bool]
    ciudad: Optional[str]
    nivel_precio: Optional[str]
    exento_iva: Optional[bool]
    servicios_confirmados: Optional[int]
    ultima_cotizacion: Optional[datetime.date]
    contactos_count: int = 0


class ContactoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre_completo: str
    email: Optional[str]
    telefono: Optional[str]
    cargo: Optional[str]
    es_principal: Optional[bool]
    puede_aprobar_cotizacion: Optional[bool]


class ServicioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    categoria: str
    unidad_cobro: str
    idioma_origen: str
    idioma_destino: str
    precio_base: float
    precio_cliente: float
    es_presencial: bool
    activo: bool


class EquipoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tipo_equipo: str
    cantidad_min: int
    cantidad_max: int
    num_dias: Optional[int]
    precio_proveedor: float
    precio_cliente: float
    descripcion: Optional[str]
    activo: bool


class SolicitudOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tipo: str
    estado: str
    prioridad: Optional[str]
    titulo: str
    descripcion: Optional[str] = None
    cliente_nombre: Optional[str] = None
    numero_cotizacion: Optional[str] = None
    created_at: Optional[datetime.datetime]


class MensajeInternoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    origen: str
    contenido: str
    tipo_contenido: Optional[str]
    created_at: Optional[datetime.datetime]


class SolicitudDetalleOut(BaseModel):
    id: int
    tipo: str
    estado: str
    prioridad: Optional[str]
    titulo: str
    descripcion: Optional[str]
    datos_formulario: dict
    respuesta_encargada: Optional[str]
    created_at: Optional[datetime.datetime]
    resuelta_at: Optional[datetime.datetime]
    # Cliente
    cliente_id: Optional[int]
    cliente_nombre: Optional[str]
    cliente_nivel_precio: Optional[str]
    cliente_descuento_min: Optional[float]
    cliente_descuento_max: Optional[float]
    cliente_markup: Optional[float]
    cliente_notas_pricing: Optional[str]
    # Contacto (de la cotizacion asociada)
    contacto_id: Optional[int]
    contacto_nombre: Optional[str]
    contacto_email: Optional[str]
    contacto_telefono: Optional[str]
    contacto_cargo: Optional[str]
    # Cotización
    cotizacion_id: Optional[int]
    numero_cotizacion: Optional[str]
    cotizacion_total: Optional[float]
    cotizacion_estado: Optional[str]


class MensajeInternoIn(BaseModel):
    contenido: str


class ResolverSolicitudIn(BaseModel):
    accion: str  # "aprobar" | "rechazar" | "modificar"
    respuesta: Optional[str] = None
    nivel_precio: Optional[str] = None
    descuento_min: Optional[float] = None
    descuento_max: Optional[float] = None
    markup_personalizado: Optional[float] = None
    notas_pricing: Optional[str] = None


class UpdatePricingIn(BaseModel):
    nivel_precio: Optional[str] = None
    descuento_min_porcentaje: Optional[float] = None
    descuento_max_porcentaje: Optional[float] = None
    markup_personalizado: Optional[float] = None
    notas_pricing: Optional[str] = None


class UpdateContactoIn(BaseModel):
    nombre_completo: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    cargo: Optional[str] = None
    puede_aprobar_cotizacion: Optional[bool] = None


class MensajesInternosResponse(BaseModel):
    mensajes: list[MensajeInternoOut]
    solicitud_estado: str


class LineaCotizacionOut(BaseModel):
    id: int
    descripcion: str
    precio_total: float
    fecha_inicio: Optional[str] = None
    fecha_fin: Optional[str] = None
    horario: Optional[str] = None


class ModificarLineaIn(BaseModel):
    linea_id: int
    nuevo_precio: float


class ModificarLineasIn(BaseModel):
    lineas: list[ModificarLineaIn]
    respuesta: Optional[str] = None


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────


def _paginate(total: int, page: int, page_size: int) -> PaginationMeta:
    pages = max(1, (total + page_size - 1) // page_size)
    return PaginationMeta(total=total, page=page, page_size=page_size, pages=pages)


# ─────────────────────────────────────────
# BACKGROUND TASKS DE APROBACIÓN
# ─────────────────────────────────────────


async def _ejecutar_accion_aprobacion(
    solicitud_id: int,
    accion: str,
    phone: str,
    cliente_nombre: str,
    cotizacion_id: int,
    numero_cotizacion: str,
    total: float,
    descuento_min: Optional[float],
    markup_personalizado: Optional[float],
    respuesta: Optional[str],
) -> None:
    """Dispatcher que llama handle_aprobacion/modificacion/rechazo según acción.
    El pricing del cliente ya fue actualizado por resolver_solicitud antes de llamar aquí."""
    from src.services.aprobacion import handle_aprobacion, handle_modificacion, handle_rechazo
    try:
        if accion == "aprobar":
            await handle_aprobacion(
                solicitud_id, cotizacion_id, phone, cliente_nombre,
                numero_cotizacion, total, respuesta,
            )
        elif accion == "modificar":
            await handle_modificacion(
                solicitud_id, cotizacion_id, phone, descuento_min, markup_personalizado, respuesta,
                actualizar_pricing_cliente=False,  # ya actualizado por resolver_solicitud
            )
        elif accion == "rechazar":
            await handle_rechazo(solicitud_id, cotizacion_id)
    except Exception as e:
        logger.error(f"_ejecutar_accion_aprobacion error (sol={solicitud_id}): {e}", exc_info=True)


async def _regenerar_y_enviar_pdf(
    solicitud_id: int,
    cotizacion_id: int,
    phone: str,
    numero_cotizacion: str,
    total: float,
    respuesta: Optional[str],
) -> None:
    """Regenera el PDF con los precios actualizados y lo envía al cliente por WhatsApp."""
    from src.services.documento import docx_a_pdf, generar_word
    from src.storage.s3 import upload_cotizacion
    from src.whatsapp.client import WhatsAppClient
    try:
        docx_bytes = await generar_word(cotizacion_id)
        pdf_bytes = docx_a_pdf(docx_bytes)
        url = await upload_cotizacion(cotizacion_id, pdf_bytes, numero_cotizacion)

        total_fmt = f"${total:,.0f}".replace(",", ".")
        async with async_session_factory() as db:
            sol = await db.get(SolicitudAgente, solicitud_id)
            if sol:
                datos = dict(sol.datos_formulario or {})
                datos["url_pdf"] = url
                sol.datos_formulario = datos
            db.add(MensajeInterno(
                solicitud_id=solicitud_id,
                origen="agente",
                contenido=f"✏️ PDF regenerado y enviado al cliente — {numero_cotizacion} · Nuevo total: {total_fmt}",
                tipo_contenido="accion",
            ))
            await db.commit()

        caption = respuesta or "Te enviamos una versión actualizada de la cotización con los precios ajustados."
        wa = WhatsAppClient()
        await wa.send_document(
            to=phone,
            document_url=url,
            filename=f"{numero_cotizacion}.pdf",
            caption=caption,
        )
        logger.info(f"PDF modificado enviado a {phone} — {numero_cotizacion}")
    except Exception as e:
        logger.error(f"_regenerar_y_enviar_pdf error: {e}", exc_info=True)


async def _procesar_texto_encargada(solicitud_id: int, texto: str) -> None:
    """Carga contexto, llama a interpretar_mensaje_encargada y actúa si corresponde."""
    from src.services.aprobacion import (
        handle_aprobacion,
        handle_modificacion,
        interpretar_mensaje_encargada,
    )
    try:
        async with async_session_factory() as db:
            result = await db.execute(
                select(SolicitudAgente)
                .options(
                    selectinload(SolicitudAgente.cliente),
                    selectinload(SolicitudAgente.cotizacion),
                )
                .where(SolicitudAgente.id == solicitud_id)
            )
            sol = result.scalar_one_or_none()
            if not sol:
                return

            msgs_result = await db.execute(
                select(MensajeInterno)
                .where(MensajeInterno.solicitud_id == solicitud_id)
                .order_by(MensajeInterno.id.asc())
            )
            mensajes = msgs_result.scalars().all()
            historial = [{"origen": m.origen, "contenido": m.contenido} for m in mensajes]

            datos = sol.datos_formulario or {}
            phone = datos.get("phone", "")
            cot_id = sol.cotizacion_id
            cot_numero = sol.cotizacion.numero_cotizacion if sol.cotizacion else ""
            cot_total = float(sol.cotizacion.total) if sol.cotizacion and sol.cotizacion.total else 0.0
            cliente_label = datos.get("empresa") or datos.get("nombre") or "cliente"

            contexto = {
                "cliente": cliente_label,
                "numero_cotizacion": cot_numero,
                "total": cot_total,
                "estado_solicitud": sol.estado,
            }

        resultado = await interpretar_mensaje_encargada(solicitud_id, texto, historial, contexto)
        accion = resultado.get("accion", "informativo")
        respuesta_agente = resultado.get("respuesta_agente", "")
        descuento = resultado.get("descuento")

        if accion == "aprobar" and phone and cot_id:
            await handle_aprobacion(
                solicitud_id, cot_id, phone, cliente_label, cot_numero, cot_total, respuesta_agente,
            )
        elif accion == "modificar" and phone and cot_id:
            await handle_modificacion(
                solicitud_id, cot_id, phone, descuento, None, respuesta_agente,
            )
        elif respuesta_agente:
            async with async_session_factory() as db:
                db.add(MensajeInterno(
                    solicitud_id=solicitud_id,
                    origen="agente",
                    contenido=respuesta_agente,
                    tipo_contenido="texto",
                ))
                await db.commit()
    except Exception as e:
        logger.error(f"_procesar_texto_encargada error (sol={solicitud_id}): {e}", exc_info=True)


# ─────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────


@router.get("/stats", response_model=StatsOut)
async def get_stats(db: AsyncSession = Depends(get_db)):
    now = datetime.datetime.utcnow()
    mes_inicio = datetime.datetime(now.year, now.month, 1)

    conv_activas = await db.scalar(
        select(func.count(Conversacion.id)).where(Conversacion.estado == "activa")
    )
    cot_total = await db.scalar(select(func.count(Cotizacion.id)))
    cot_mes = await db.scalar(
        select(func.count(Cotizacion.id)).where(Cotizacion.created_at >= mes_inicio)
    )
    ingresos_total = await db.scalar(
        select(func.coalesce(func.sum(Cotizacion.total), 0)).where(
            Cotizacion.estado.in_(["enviada", "aceptada"])
        )
    )
    ingresos_mes = await db.scalar(
        select(func.coalesce(func.sum(Cotizacion.total), 0)).where(
            Cotizacion.estado.in_(["enviada", "aceptada"]),
            Cotizacion.created_at >= mes_inicio,
        )
    )
    sol_pendientes = await db.scalar(
        select(func.count(SolicitudAgente.id)).where(SolicitudAgente.estado == "pendiente")
    )
    clientes_total = await db.scalar(select(func.count(Cliente.id)))

    return StatsOut(
        conversaciones_activas=conv_activas or 0,
        cotizaciones_total=cot_total or 0,
        cotizaciones_este_mes=cot_mes or 0,
        ingresos_total=float(ingresos_total or 0),
        ingresos_este_mes=float(ingresos_mes or 0),
        solicitudes_pendientes=sol_pendientes or 0,
        clientes_total=clientes_total or 0,
    )


@router.get("/conversaciones", response_model=PaginatedResponse[ConversacionOut])
async def get_conversaciones(
    estado: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Conversacion).options(selectinload(Conversacion.cliente))

    if estado:
        stmt = stmt.where(Conversacion.estado == estado)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(
            Conversacion.nombre_temporal.ilike(like)
            | Conversacion.telefono_whatsapp.ilike(like)
        )

    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    stmt = stmt.order_by(Conversacion.ultimo_mensaje_at.desc().nullslast())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    rows = result.scalars().all()

    data = []
    for c in rows:
        out = ConversacionOut(
            id=c.id,
            cliente_id=c.cliente_id,
            cliente_nombre=c.cliente.nombre_empresa if c.cliente else None,
            nombre_temporal=c.nombre_temporal,
            telefono_whatsapp=c.telefono_whatsapp,
            estado=c.estado,
            ultimo_mensaje_preview=c.ultimo_mensaje_preview,
            ultimo_mensaje_at=c.ultimo_mensaje_at,
            mensajes_no_leidos=c.mensajes_no_leidos,
            created_at=c.created_at,
        )
        data.append(out)

    return PaginatedResponse(data=data, meta=_paginate(total or 0, page, page_size))


@router.get("/conversaciones/{conv_id}/mensajes", response_model=MensajesResponse)
async def get_mensajes(
    conv_id: int,
    limit: int = Query(50, ge=1, le=200),
    before_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    conv_result = await db.execute(
        select(Conversacion)
        .options(selectinload(Conversacion.cliente))
        .where(Conversacion.id == conv_id)
    )
    conv = conv_result.scalar_one_or_none()
    if not conv:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Conversación no encontrada")

    stmt = select(Mensaje).where(Mensaje.conversacion_id == conv_id)
    if before_id:
        stmt = stmt.where(Mensaje.id < before_id)

    total_stmt = select(func.count(Mensaje.id)).where(Mensaje.conversacion_id == conv_id)
    if before_id:
        total_stmt = total_stmt.where(Mensaje.id < before_id)
    total = await db.scalar(total_stmt)

    stmt = stmt.order_by(Mensaje.id.asc()).limit(limit)
    result = await db.execute(stmt)
    mensajes = result.scalars().all()

    return MensajesResponse(
        conversacion=ConversacionDetalleOut(
            id=conv.id,
            nombre_temporal=conv.nombre_temporal,
            telefono_whatsapp=conv.telefono_whatsapp,
            estado=conv.estado,
            cliente_nombre=conv.cliente.nombre_empresa if conv.cliente else None,
        ),
        mensajes=[MensajeOut.model_validate(m) for m in mensajes],
        has_more=(total or 0) > limit,
    )


@router.patch("/conversaciones/{conv_id}/leer")
async def marcar_leida(conv_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Conversacion).where(Conversacion.id == conv_id))
    conv = result.scalar_one_or_none()
    if conv:
        conv.mensajes_no_leidos = 0
        await db.commit()
    return {"ok": True}


@router.get("/clientes", response_model=PaginatedResponse[ClienteOut])
async def get_clientes(
    search: Optional[str] = None,
    es_recurrente: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Cliente)

    if search:
        stmt = stmt.where(Cliente.nombre_empresa.ilike(f"%{search}%"))
    if es_recurrente is not None:
        stmt = stmt.where(Cliente.es_recurrente == es_recurrente)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    stmt = stmt.order_by(Cliente.nombre_empresa.asc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    clientes = result.scalars().all()

    # contactos_count por cliente en una sola query
    cliente_ids = [c.id for c in clientes]
    count_result = await db.execute(
        select(Contacto.cliente_id, func.count(Contacto.id).label("cnt"))
        .where(Contacto.cliente_id.in_(cliente_ids))
        .group_by(Contacto.cliente_id)
    )
    counts = {row.cliente_id: row.cnt for row in count_result}

    data = []
    for c in clientes:
        out = ClienteOut(
            id=c.id,
            nombre_empresa=c.nombre_empresa,
            tipo_cliente=c.tipo_cliente,
            nit=c.nit,
            es_recurrente=c.es_recurrente,
            ciudad=c.ciudad,
            nivel_precio=c.nivel_precio,
            exento_iva=c.exento_iva,
            servicios_confirmados=c.servicios_confirmados,
            ultima_cotizacion=c.ultima_cotizacion,
            contactos_count=counts.get(c.id, 0),
        )
        data.append(out)

    return PaginatedResponse(data=data, meta=_paginate(total or 0, page, page_size))


@router.get("/clientes/{cliente_id}/contactos")
async def get_contactos(cliente_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Contacto)
        .where(Contacto.cliente_id == cliente_id)
        .order_by(Contacto.es_principal.desc(), Contacto.id)
    )
    contactos = result.scalars().all()
    return {"data": [ContactoOut.model_validate(c) for c in contactos]}


@router.get("/servicios")
async def get_servicios(
    tipo: Optional[str] = Query(None, description="servicio | equipo"),
    categoria: Optional[str] = None,
    activo: Optional[bool] = True,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    if tipo == "equipo":
        stmt = select(TarifaAlquilerEquipo)
        if activo is not None:
            stmt = stmt.where(TarifaAlquilerEquipo.activo == activo)
        total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
        stmt = stmt.order_by(TarifaAlquilerEquipo.tipo_equipo).offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(stmt)
        equipos = result.scalars().all()
        data = [
            EquipoOut(
                id=e.id,
                tipo_equipo=e.tipo_equipo,
                cantidad_min=e.cantidad_min,
                cantidad_max=e.cantidad_max,
                num_dias=e.num_dias,
                precio_proveedor=float(e.precio_proveedor),
                precio_cliente=float(e.precio_cliente),
                descripcion=e.descripcion,
                activo=e.activo,
            )
            for e in equipos
        ]
        return PaginatedResponse(data=data, meta=_paginate(total or 0, page, page_size))
    else:
        stmt = select(Servicio)
        if activo is not None:
            stmt = stmt.where(Servicio.activo == activo)
        if categoria:
            stmt = stmt.where(Servicio.categoria == categoria)
        total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
        stmt = stmt.order_by(Servicio.categoria, Servicio.nombre).offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(stmt)
        servicios = result.scalars().all()
        data = [
            ServicioOut(
                id=s.id,
                nombre=s.nombre,
                categoria=s.categoria,
                unidad_cobro=s.unidad_cobro,
                idioma_origen=s.idioma_origen,
                idioma_destino=s.idioma_destino,
                precio_base=float(s.precio_base),
                precio_cliente=float(s.precio_cliente),
                es_presencial=s.es_presencial,
                activo=s.activo,
            )
            for s in servicios
        ]
        return PaginatedResponse(data=data, meta=_paginate(total or 0, page, page_size))


@router.get("/solicitudes", response_model=PaginatedResponse[SolicitudOut])
async def get_solicitudes(
    estado: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(SolicitudAgente).options(
        selectinload(SolicitudAgente.cliente),
        selectinload(SolicitudAgente.cotizacion),
    )
    if estado:
        stmt = stmt.where(SolicitudAgente.estado == estado)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    stmt = stmt.order_by(SolicitudAgente.created_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    solicitudes = result.scalars().all()

    data = []
    for s in solicitudes:
        out = SolicitudOut(
            id=s.id,
            tipo=s.tipo,
            estado=s.estado,
            prioridad=s.prioridad,
            titulo=s.titulo,
            descripcion=s.descripcion,
            cliente_nombre=s.cliente.nombre_empresa if s.cliente else None,
            numero_cotizacion=s.cotizacion.numero_cotizacion if s.cotizacion else None,
            created_at=s.created_at,
        )
        data.append(out)

    return PaginatedResponse(data=data, meta=_paginate(total or 0, page, page_size))


def _build_solicitud_detalle(s: SolicitudAgente) -> SolicitudDetalleOut:
    cliente = s.cliente
    cot = s.cotizacion
    contacto = cot.contacto if cot and cot.contacto else None
    return SolicitudDetalleOut(
        id=s.id,
        tipo=s.tipo,
        estado=s.estado,
        prioridad=s.prioridad,
        titulo=s.titulo,
        descripcion=s.descripcion,
        datos_formulario=s.datos_formulario or {},
        respuesta_encargada=s.respuesta_encargada,
        created_at=s.created_at,
        resuelta_at=s.resuelta_at,
        cliente_id=cliente.id if cliente else None,
        cliente_nombre=cliente.nombre_empresa if cliente else None,
        cliente_nivel_precio=cliente.nivel_precio if cliente else None,
        cliente_descuento_min=float(cliente.descuento_min_porcentaje) if cliente and cliente.descuento_min_porcentaje is not None else None,
        cliente_descuento_max=float(cliente.descuento_max_porcentaje) if cliente and cliente.descuento_max_porcentaje is not None else None,
        cliente_markup=float(cliente.markup_personalizado) if cliente and cliente.markup_personalizado is not None else None,
        cliente_notas_pricing=cliente.notas_pricing if cliente else None,
        contacto_id=contacto.id if contacto else None,
        contacto_nombre=contacto.nombre_completo if contacto else None,
        contacto_email=contacto.email if contacto else None,
        contacto_telefono=contacto.telefono if contacto else None,
        contacto_cargo=contacto.cargo if contacto else None,
        cotizacion_id=cot.id if cot else None,
        numero_cotizacion=cot.numero_cotizacion if cot else None,
        cotizacion_total=float(cot.total) if cot and cot.total is not None else None,
        cotizacion_estado=cot.estado if cot else None,
    )


@router.get("/solicitudes/{solicitud_id}", response_model=SolicitudDetalleOut)
async def get_solicitud_detalle(solicitud_id: int, db: AsyncSession = Depends(get_db)):
    from fastapi import HTTPException
    result = await db.execute(
        select(SolicitudAgente)
        .options(
            selectinload(SolicitudAgente.cliente),
            selectinload(SolicitudAgente.cotizacion).selectinload(Cotizacion.contacto),
        )
        .where(SolicitudAgente.id == solicitud_id)
    )
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    return _build_solicitud_detalle(s)


@router.get("/solicitudes/{solicitud_id}/mensajes", response_model=MensajesInternosResponse)
async def get_mensajes_internos(solicitud_id: int, db: AsyncSession = Depends(get_db)):
    from fastapi import HTTPException
    sol = await db.scalar(select(SolicitudAgente).where(SolicitudAgente.id == solicitud_id))
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    result = await db.execute(
        select(MensajeInterno)
        .where(MensajeInterno.solicitud_id == solicitud_id)
        .order_by(MensajeInterno.id.asc())
    )
    mensajes = result.scalars().all()
    return MensajesInternosResponse(
        mensajes=[MensajeInternoOut.model_validate(m) for m in mensajes],
        solicitud_estado=sol.estado,
    )


@router.post("/solicitudes/{solicitud_id}/mensajes", response_model=MensajeInternoOut, status_code=201)
async def post_mensaje_interno(
    solicitud_id: int, body: MensajeInternoIn, db: AsyncSession = Depends(get_db)
):
    from fastapi import HTTPException
    sol = await db.scalar(select(SolicitudAgente).where(SolicitudAgente.id == solicitud_id))
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    msg = MensajeInterno(
        solicitud_id=solicitud_id,
        origen="encargada",
        contenido=body.contenido,
        tipo_contenido="texto",
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    # Interpretar mensaje en background (solo si solicitud aún pendiente)
    if sol.estado == "pendiente":
        asyncio.create_task(_procesar_texto_encargada(solicitud_id, body.contenido))

    return MensajeInternoOut.model_validate(msg)


@router.patch("/solicitudes/{solicitud_id}/resolver", response_model=SolicitudDetalleOut)
async def resolver_solicitud(
    solicitud_id: int, body: ResolverSolicitudIn, db: AsyncSession = Depends(get_db)
):
    from fastapi import HTTPException
    result = await db.execute(
        select(SolicitudAgente)
        .options(
            selectinload(SolicitudAgente.cliente),
            selectinload(SolicitudAgente.cotizacion).selectinload(Cotizacion.contacto),
        )
        .where(SolicitudAgente.id == solicitud_id)
    )
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    if s.estado in ("aprobada", "rechazada", "modificada"):
        raise HTTPException(
            status_code=409,
            detail=f"Solicitud ya fue resuelta ({s.estado}). No se puede cambiar."
        )

    estado_map = {"aprobar": "aprobada", "rechazar": "rechazada", "modificar": "modificada"}
    s.estado = estado_map.get(body.accion, body.accion)
    s.respuesta_encargada = body.respuesta
    s.resuelta_at = datetime.datetime.utcnow()

    # Actualizar pricing del cliente si se proveen campos
    if s.cliente and any([
        body.nivel_precio, body.descuento_min is not None,
        body.descuento_max is not None, body.markup_personalizado is not None,
        body.notas_pricing,
    ]):
        if body.nivel_precio:
            s.cliente.nivel_precio = body.nivel_precio
        if body.descuento_min is not None:
            s.cliente.descuento_min_porcentaje = body.descuento_min
        if body.descuento_max is not None:
            s.cliente.descuento_max_porcentaje = body.descuento_max
        if body.markup_personalizado is not None:
            s.cliente.markup_personalizado = body.markup_personalizado
        if body.notas_pricing:
            s.cliente.notas_pricing = body.notas_pricing

    # Crear mensaje interno de confirmación
    etiqueta = {"aprobar": "✅ Aprobada", "rechazar": "❌ Rechazada", "modificar": "✏️ Modificada"}.get(body.accion, body.accion)
    texto = f"{etiqueta}" + (f": {body.respuesta}" if body.respuesta else "")
    msg = MensajeInterno(
        solicitud_id=solicitud_id,
        origen="encargada",
        contenido=texto,
        tipo_contenido="accion",
    )
    db.add(msg)
    await db.commit()
    await db.refresh(s)

    # Ejecutar acción de aprobación en background (WhatsApp + PDF si aplica)
    phone = (s.datos_formulario or {}).get("phone", "")
    cot_id = s.cotizacion_id
    if not phone:
        logger.warning(f"resolver_solicitud sol={solicitud_id}: sin phone en datos_formulario, no se enviará WhatsApp")
    if not cot_id:
        logger.warning(f"resolver_solicitud sol={solicitud_id}: sin cotizacion_id, no se ejecutará acción")
    if phone and cot_id:
        datos = s.datos_formulario or {}
        cliente_label = datos.get("empresa") or datos.get("nombre") or "cliente"
        cot_numero = s.cotizacion.numero_cotizacion if s.cotizacion else ""
        cot_total = float(s.cotizacion.total) if s.cotizacion and s.cotizacion.total else 0.0
        asyncio.create_task(_ejecutar_accion_aprobacion(
            solicitud_id=solicitud_id,
            accion=body.accion,
            phone=phone,
            cliente_nombre=cliente_label,
            cotizacion_id=cot_id,
            numero_cotizacion=cot_numero,
            total=cot_total,
            descuento_min=body.descuento_min,
            markup_personalizado=body.markup_personalizado,
            respuesta=body.respuesta,
        ))

    return _build_solicitud_detalle(s)


@router.patch("/clientes/{cliente_id}/pricing", response_model=ClienteOut)
async def update_cliente_pricing(
    cliente_id: int, body: UpdatePricingIn, db: AsyncSession = Depends(get_db)
):
    from fastapi import HTTPException
    result = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
    cliente = result.scalar_one_or_none()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    if body.nivel_precio is not None:
        cliente.nivel_precio = body.nivel_precio
    if body.descuento_min_porcentaje is not None:
        cliente.descuento_min_porcentaje = body.descuento_min_porcentaje
    if body.descuento_max_porcentaje is not None:
        cliente.descuento_max_porcentaje = body.descuento_max_porcentaje
    if body.markup_personalizado is not None:
        cliente.markup_personalizado = body.markup_personalizado
    if body.notas_pricing is not None:
        cliente.notas_pricing = body.notas_pricing

    await db.commit()
    await db.refresh(cliente)

    count_result = await db.scalar(
        select(func.count(Contacto.id)).where(Contacto.cliente_id == cliente_id)
    )
    out = ClienteOut.model_validate(cliente)
    out.contactos_count = count_result or 0
    return out


@router.patch("/contactos/{contacto_id}", response_model=ContactoOut)
async def update_contacto(
    contacto_id: int, body: UpdateContactoIn, db: AsyncSession = Depends(get_db)
):
    from fastapi import HTTPException
    result = await db.execute(select(Contacto).where(Contacto.id == contacto_id))
    contacto = result.scalar_one_or_none()
    if not contacto:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")

    if body.nombre_completo is not None:
        contacto.nombre_completo = body.nombre_completo
    if body.email is not None:
        contacto.email = body.email
    if body.telefono is not None:
        contacto.telefono = body.telefono
    if body.cargo is not None:
        contacto.cargo = body.cargo
    if body.puede_aprobar_cotizacion is not None:
        contacto.puede_aprobar_cotizacion = body.puede_aprobar_cotizacion

    await db.commit()
    await db.refresh(contacto)
    return ContactoOut.model_validate(contacto)


@router.get("/cotizaciones/{cotizacion_id}/lineas", response_model=list[LineaCotizacionOut])
async def get_lineas_cotizacion(cotizacion_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LineaCotizacion)
        .options(selectinload(LineaCotizacion.servicio))
        .where(LineaCotizacion.cotizacion_id == cotizacion_id)
        .order_by(LineaCotizacion.orden, LineaCotizacion.id)
    )
    lineas = result.scalars().all()

    out = []
    for linea in lineas:
        nombre = linea.servicio.nombre if linea.servicio else (linea.descripcion_generada or "Ítem")
        idioma = f" ({linea.servicio.idioma_destino})" if linea.servicio and linea.servicio.idioma_destino else ""
        detalles = []
        if linea.fecha_servicio_inicio:
            fecha_str = linea.fecha_servicio_inicio.strftime("%d/%m/%Y")
            if linea.fecha_servicio_fin and linea.fecha_servicio_fin != linea.fecha_servicio_inicio:
                fecha_str += f" – {linea.fecha_servicio_fin.strftime('%d/%m/%Y')}"
            detalles.append(fecha_str)
        if linea.horario:
            detalles.append(linea.horario)
        if linea.num_interpretes and linea.num_interpretes > 1:
            detalles.append(f"{linea.num_interpretes} intérpretes")
        if linea.num_equipos:
            detalles.append(f"{linea.num_equipos} equipos")

        descripcion = f"{nombre}{idioma}"
        if detalles:
            descripcion += f" — {' · '.join(detalles)}"

        out.append(LineaCotizacionOut(
            id=linea.id,
            descripcion=descripcion,
            precio_total=float(linea.precio_total),
            fecha_inicio=str(linea.fecha_servicio_inicio) if linea.fecha_servicio_inicio else None,
            fecha_fin=str(linea.fecha_servicio_fin) if linea.fecha_servicio_fin else None,
            horario=linea.horario,
        ))

    return out


@router.post("/solicitudes/{solicitud_id}/modificar-lineas", response_model=SolicitudDetalleOut)
async def modificar_lineas_cotizacion(
    solicitud_id: int, body: ModificarLineasIn, db: AsyncSession = Depends(get_db)
):
    from decimal import Decimal
    from fastapi import HTTPException

    result = await db.execute(
        select(SolicitudAgente)
        .options(
            selectinload(SolicitudAgente.cliente),
            selectinload(SolicitudAgente.cotizacion).selectinload(Cotizacion.contacto),
        )
        .where(SolicitudAgente.id == solicitud_id)
    )
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    cot_id = s.cotizacion_id
    if not cot_id:
        raise HTTPException(status_code=400, detail="Solicitud sin cotización asociada")

    # Actualizar precio_total de cada línea
    nuevo_subtotal = Decimal("0")
    for item in body.lineas:
        linea = await db.get(LineaCotizacion, item.linea_id)
        if linea and linea.cotizacion_id == cot_id:
            linea.precio_total = Decimal(str(item.nuevo_precio))
            nuevo_subtotal += linea.precio_total

    # Recalcular totales de la cotización
    cot = await db.get(Cotizacion, cot_id)
    if cot:
        cot.subtotal = nuevo_subtotal
        if not cot.exento_iva:
            cot.iva = nuevo_subtotal * Decimal("0.19")
            cot.total = nuevo_subtotal + cot.iva
        else:
            cot.iva = Decimal("0")
            cot.total = nuevo_subtotal

    # Marcar solicitud como modificada
    s.estado = "modificada"
    s.respuesta_encargada = body.respuesta
    s.resuelta_at = datetime.datetime.utcnow()

    total_fmt = f"${float(cot.total):,.0f}".replace(",", ".") if cot and cot.total else "—"
    db.add(MensajeInterno(
        solicitud_id=solicitud_id,
        origen="encargada",
        contenido=(
            f"✏️ Precios ajustados manualmente — Nuevo total: {total_fmt}"
            + (f"\n{body.respuesta}" if body.respuesta else "")
        ),
        tipo_contenido="accion",
    ))

    await db.commit()
    await db.refresh(s)

    # Regenerar PDF y enviar al cliente en background
    phone = (s.datos_formulario or {}).get("phone", "")
    if phone and cot:
        asyncio.create_task(_regenerar_y_enviar_pdf(
            solicitud_id=solicitud_id,
            cotizacion_id=cot_id,
            phone=phone,
            numero_cotizacion=cot.numero_cotizacion,
            total=float(cot.total) if cot.total else 0.0,
            respuesta=body.respuesta,
        ))

    return _build_solicitud_detalle(s)
