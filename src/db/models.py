import datetime
import decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ==========================================
# ESQUEMA CORE (10 TABLAS)
# ==========================================


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre_empresa: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    tipo_cliente: Mapped[str] = mapped_column(String(50), default="Empresa")
    nivel_precio: Mapped[str] = mapped_column(String(20), default="nuevo")
    descuento_min_porcentaje: Mapped[decimal.Decimal] = mapped_column(Numeric(5, 2), default=0)
    descuento_max_porcentaje: Mapped[decimal.Decimal] = mapped_column(Numeric(5, 2), default=0)
    markup_personalizado: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    exento_iva: Mapped[bool] = mapped_column(Boolean, default=False)
    notas_pricing: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    es_recurrente: Mapped[bool] = mapped_column(Boolean, default=False)
    servicios_confirmados: Mapped[int] = mapped_column(Integer, default=0)
    ultima_cotizacion: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    contactos: Mapped[list["Contacto"]] = relationship("Contacto", back_populates="cliente", cascade="all, delete-orphan")
    cotizaciones: Mapped[list["Cotizacion"]] = relationship("Cotizacion", back_populates="cliente")
    conversaciones: Mapped[list["Conversacion"]] = relationship("Conversacion", back_populates="cliente")
    solicitudes: Mapped[list["SolicitudAgente"]] = relationship("SolicitudAgente", back_populates="cliente")


class Contacto(Base):
    __tablename__ = "contactos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(Integer, ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False)
    nombre_completo: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    telefono: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    cargo: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    es_principal: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    cliente: Mapped["Cliente"] = relationship("Cliente", back_populates="contactos")
    cotizaciones: Mapped[list["Cotizacion"]] = relationship("Cotizacion", back_populates="contacto")


class Servicio(Base):
    __tablename__ = "servicios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    idioma_origen: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    idioma_destino: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    precio_base: Mapped[decimal.Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    precio_cliente: Mapped[decimal.Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    unidad_cobro: Mapped[str] = mapped_column(String(20), nullable=False)
    num_interpretes_default: Mapped[int] = mapped_column(Integer, default=1)
    notas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    lineas: Mapped[list["LineaCotizacion"]] = relationship("LineaCotizacion", back_populates="servicio")


class TarifaAlquilerEquipo(Base):
    __tablename__ = "tarifas_alquiler_equipos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipo_equipo: Mapped[str] = mapped_column(String(50), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cantidad_min: Mapped[int] = mapped_column(Integer, default=1)
    cantidad_max: Mapped[int] = mapped_column(Integer, default=9999)
    num_dias: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    precio_base: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    precio_cliente: Mapped[decimal.Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    notas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    lineas: Mapped[list["LineaCotizacion"]] = relationship("LineaCotizacion", back_populates="equipo_alquiler")


class Recargo(Base):
    __tablename__ = "recargos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    porcentaje: Mapped[decimal.Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class Cotizacion(Base):
    __tablename__ = "cotizaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("clientes.id"), nullable=True)
    contacto_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("contactos.id"), nullable=True)
    numero_cotizacion: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    fecha: Mapped[datetime.date] = mapped_column(Date, server_default=func.current_date())
    ubicacion_evento: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    es_fuera_de_bogota: Mapped[bool] = mapped_column(Boolean, default=False)
    subtotal: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    iva: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    total: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    exento_iva: Mapped[bool] = mapped_column(Boolean, default=False)
    validez_oferta: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    forma_pago: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), default="borrador")
    notas_internas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    cliente: Mapped[Optional["Cliente"]] = relationship("Cliente", back_populates="cotizaciones")
    contacto: Mapped[Optional["Contacto"]] = relationship("Contacto", back_populates="cotizaciones")
    versiones: Mapped[list["VersionCotizacion"]] = relationship("VersionCotizacion", back_populates="cotizacion", cascade="all, delete-orphan")
    lineas: Mapped[list["LineaCotizacion"]] = relationship("LineaCotizacion", back_populates="cotizacion", cascade="all, delete-orphan")
    ordenes: Mapped[list["OrdenServicio"]] = relationship("OrdenServicio", back_populates="cotizacion")
    seguimientos: Mapped[list["Seguimiento"]] = relationship("Seguimiento", back_populates="cotizacion")
    solicitudes: Mapped[list["SolicitudAgente"]] = relationship("SolicitudAgente", back_populates="cotizacion")


class VersionCotizacion(Base):
    __tablename__ = "versiones_cotizacion"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cotizacion_id: Mapped[int] = mapped_column(Integer, ForeignKey("cotizaciones.id", ondelete="CASCADE"), nullable=False)
    version_label: Mapped[str] = mapped_column(String(10), nullable=False)
    total_anterior: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    total_nuevo: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    motivo_cambio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    cotizacion: Mapped["Cotizacion"] = relationship("Cotizacion", back_populates="versiones")


class LineaCotizacion(Base):
    __tablename__ = "lineas_cotizacion"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cotizacion_id: Mapped[int] = mapped_column(Integer, ForeignKey("cotizaciones.id", ondelete="CASCADE"), nullable=False)
    servicio_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("servicios.id"), nullable=True)
    equipo_alquiler_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("tarifas_alquiler_equipos.id"), nullable=True)
    cantidad: Mapped[decimal.Decimal] = mapped_column(Numeric(10, 2), default=1)
    precio_unitario: Mapped[decimal.Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    precio_total: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    fecha_servicio_inicio: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    fecha_servicio_fin: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    horario: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    num_interpretes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    num_equipos: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    descripcion_generada: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    orden: Mapped[int] = mapped_column(Integer, default=0)

    cotizacion: Mapped["Cotizacion"] = relationship("Cotizacion", back_populates="lineas")
    servicio: Mapped[Optional["Servicio"]] = relationship("Servicio", back_populates="lineas")
    equipo_alquiler: Mapped[Optional["TarifaAlquilerEquipo"]] = relationship("TarifaAlquilerEquipo", back_populates="lineas")


class OrdenServicio(Base):
    __tablename__ = "ordenes_servicio"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cotizacion_id: Mapped[int] = mapped_column(Integer, ForeignKey("cotizaciones.id"), nullable=False)
    numero_os: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True)
    fecha_emision: Mapped[datetime.date] = mapped_column(Date, server_default=func.current_date())
    estado: Mapped[str] = mapped_column(String(20), default="pendiente")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    cotizacion: Mapped["Cotizacion"] = relationship("Cotizacion", back_populates="ordenes")


class Seguimiento(Base):
    __tablename__ = "seguimientos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cotizacion_id: Mapped[int] = mapped_column(Integer, ForeignKey("cotizaciones.id"), nullable=False)
    fecha_seguimiento: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    metodo: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    resultado: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    proximo_seguimiento: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)

    cotizacion: Mapped["Cotizacion"] = relationship("Cotizacion", back_populates="seguimientos")


# ==========================================
# ESQUEMA PANEL (4 TABLAS)
# ==========================================


class Conversacion(Base):
    __tablename__ = "conversaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("clientes.id", ondelete="SET NULL"), nullable=True)
    canal: Mapped[str] = mapped_column(String(20), nullable=False, default="whatsapp")
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="activa")
    telefono_whatsapp: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    nombre_temporal: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ultimo_mensaje_preview: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ultimo_mensaje_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    mensajes_no_leidos: Mapped[int] = mapped_column(Integer, default=0)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    cliente: Mapped[Optional["Cliente"]] = relationship("Cliente", back_populates="conversaciones")
    mensajes: Mapped[list["Mensaje"]] = relationship("Mensaje", back_populates="conversacion", cascade="all, delete-orphan")
    solicitudes: Mapped[list["SolicitudAgente"]] = relationship("SolicitudAgente", back_populates="conversacion")


class Mensaje(Base):
    __tablename__ = "mensajes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversacion_id: Mapped[int] = mapped_column(Integer, ForeignKey("conversaciones.id", ondelete="CASCADE"), nullable=False)
    origen: Mapped[str] = mapped_column(String(20), nullable=False)
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    tipo_contenido: Mapped[str] = mapped_column(String(20), nullable=False, default="texto")
    url_archivo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    whatsapp_message_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, unique=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    conversacion: Mapped["Conversacion"] = relationship("Conversacion", back_populates="mensajes")


class SolicitudAgente(Base):
    __tablename__ = "solicitudes_agente"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("clientes.id", ondelete="SET NULL"), nullable=True)
    cotizacion_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("cotizaciones.id", ondelete="SET NULL"), nullable=True)
    conversacion_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("conversaciones.id", ondelete="SET NULL"), nullable=True)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="pendiente")
    prioridad: Mapped[str] = mapped_column(String(10), default="normal")
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    datos_formulario: Mapped[dict] = mapped_column(JSONB, default=dict)
    respuesta_encargada: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    archivo_adjunto: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resuelta_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    cliente: Mapped[Optional["Cliente"]] = relationship("Cliente", back_populates="solicitudes")
    cotizacion: Mapped[Optional["Cotizacion"]] = relationship("Cotizacion", back_populates="solicitudes")
    conversacion: Mapped[Optional["Conversacion"]] = relationship("Conversacion", back_populates="solicitudes")
    mensajes_internos: Mapped[list["MensajeInterno"]] = relationship("MensajeInterno", back_populates="solicitud", cascade="all, delete-orphan")


class MensajeInterno(Base):
    __tablename__ = "mensajes_internos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    solicitud_id: Mapped[int] = mapped_column(Integer, ForeignKey("solicitudes_agente.id", ondelete="CASCADE"), nullable=False)
    origen: Mapped[str] = mapped_column(String(20), nullable=False)
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    tipo_contenido: Mapped[str] = mapped_column(String(20), default="texto")
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    solicitud: Mapped["SolicitudAgente"] = relationship("SolicitudAgente", back_populates="mensajes_internos")
