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
    nombre_empresa: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, unique=True)
    tipo_cliente: Mapped[Optional[str]] = mapped_column(String(50), default="Empresa")
    nit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    es_recurrente: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    ciudad: Mapped[Optional[str]] = mapped_column(String(100), default="Bogotá")
    direccion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notas_relacion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    servicios_confirmados: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    ultima_cotizacion: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    exento_iva: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    nivel_precio: Mapped[Optional[str]] = mapped_column(String(20), default="nuevo")
    descuento_min_porcentaje: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(5, 2), default=0)
    descuento_max_porcentaje: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(5, 2), default=0)
    markup_personalizado: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    notas_pricing: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tiene_rut: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default="false")
    numero_rut: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    correo_facturacion: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=False), server_default=func.now())
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now())

    contactos: Mapped[list["Contacto"]] = relationship("Contacto", back_populates="cliente", cascade="all, delete-orphan")
    cotizaciones: Mapped[list["Cotizacion"]] = relationship("Cotizacion", back_populates="cliente")
    conversaciones: Mapped[list["Conversacion"]] = relationship("Conversacion", back_populates="cliente")
    solicitudes: Mapped[list["SolicitudAgente"]] = relationship("SolicitudAgente", back_populates="cliente")


class Contacto(Base):
    __tablename__ = "contactos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(Integer, ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False)
    nombre_completo: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    telefono: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    cargo: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    es_principal: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    notas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    puede_aprobar_cotizacion: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    notas_negociacion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=False), server_default=func.now())
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now())

    cliente: Mapped["Cliente"] = relationship("Cliente", back_populates="contactos")
    cotizaciones: Mapped[list["Cotizacion"]] = relationship("Cotizacion", back_populates="contacto")


class Servicio(Base):
    __tablename__ = "servicios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    categoria: Mapped[str] = mapped_column(String(50), nullable=False)
    unidad_cobro: Mapped[str] = mapped_column(String(30), nullable=False)
    idioma_origen: Mapped[str] = mapped_column(String(50), nullable=False, default="español")
    idioma_destino: Mapped[str] = mapped_column(String(50), nullable=False)
    precio_base: Mapped[decimal.Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    aumento_porcentaje: Mapped[decimal.Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    markup_porcentaje: Mapped[decimal.Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=30)
    precio_cliente: Mapped[decimal.Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    es_presencial: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    num_interpretes_default: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=False), server_default=func.now())
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now())

    lineas: Mapped[list["LineaCotizacion"]] = relationship("LineaCotizacion", back_populates="servicio")


class TarifaAlquilerEquipo(Base):
    __tablename__ = "tarifas_alquiler_equipos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipo_equipo: Mapped[str] = mapped_column(String(50), nullable=False)
    cantidad_min: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    cantidad_max: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    num_dias: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    precio_proveedor: Mapped[decimal.Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    markup_porcentaje: Mapped[decimal.Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=25)
    precio_cliente: Mapped[decimal.Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=False), server_default=func.now())
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now())

    lineas: Mapped[list["LineaCotizacion"]] = relationship("LineaCotizacion", back_populates="equipo_alquiler")


class Recargo(Base):
    __tablename__ = "recargos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    porcentaje: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    monto_fijo: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    condicion: Mapped[str] = mapped_column(Text, nullable=False)
    es_automatico: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    activo: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=False), server_default=func.now())
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now())


class Cotizacion(Base):
    __tablename__ = "cotizaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(Integer, ForeignKey("clientes.id"), nullable=False)
    contacto_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("contactos.id"), nullable=True)
    numero_cotizacion: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    version: Mapped[Optional[str]] = mapped_column(String(1), nullable=True)
    fecha: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    ubicacion_evento: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, default="Bogotá")
    es_fuera_de_bogota: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    subtotal: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    iva: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    total: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    exento_iva: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    validez_oferta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    forma_pago: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, default="A 30 días")
    estado: Mapped[Optional[str]] = mapped_column(String(30), default="borrador")
    fecha_envio: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    fecha_respuesta: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    fecha_cierre: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    razon_perdida: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    numero_orden_compra: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    incluir_terminos_corporativos: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    descripcion_generada: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notas_internas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cotizacion_padre_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("cotizaciones.id"), nullable=True)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=False), server_default=func.now())
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now())

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
    letra_version: Mapped[str] = mapped_column(String(1), nullable=False)
    fecha: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    total_anterior: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    total_nuevo: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    cambios: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    aprobada: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=False), server_default=func.now())

    cotizacion: Mapped["Cotizacion"] = relationship("Cotizacion", back_populates="versiones")


class LineaCotizacion(Base):
    __tablename__ = "lineas_cotizacion"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cotizacion_id: Mapped[int] = mapped_column(Integer, ForeignKey("cotizaciones.id", ondelete="CASCADE"), nullable=False)
    servicio_id: Mapped[int] = mapped_column(Integer, ForeignKey("servicios.id"), nullable=False)
    equipo_alquiler_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("tarifas_alquiler_equipos.id"), nullable=True)
    cantidad: Mapped[decimal.Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=1)
    precio_unitario: Mapped[decimal.Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    precio_total: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    fecha_servicio_inicio: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    fecha_servicio_fin: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    horario: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    num_interpretes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    num_dias: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    num_equipos: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    nombre_documento: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    num_palabras: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    descripcion_generada: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notas_linea: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    orden: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=False), server_default=func.now())
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now())

    cotizacion: Mapped["Cotizacion"] = relationship("Cotizacion", back_populates="lineas")
    servicio: Mapped["Servicio"] = relationship("Servicio", back_populates="lineas")
    equipo_alquiler: Mapped[Optional["TarifaAlquilerEquipo"]] = relationship("TarifaAlquilerEquipo", back_populates="lineas")


class OrdenServicio(Base):
    __tablename__ = "ordenes_servicio"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cotizacion_id: Mapped[int] = mapped_column(Integer, ForeignKey("cotizaciones.id"), nullable=False)
    numero_os: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True)
    fecha_emision: Mapped[Optional[datetime.date]] = mapped_column(Date, server_default=func.current_date())
    estado: Mapped[Optional[str]] = mapped_column(String(20), default="pendiente")
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now())

    cotizacion: Mapped["Cotizacion"] = relationship("Cotizacion", back_populates="ordenes")


class Seguimiento(Base):
    __tablename__ = "seguimientos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cotizacion_id: Mapped[int] = mapped_column(Integer, ForeignKey("cotizaciones.id"), nullable=False)
    fecha_seguimiento: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now())
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
    mensajes_no_leidos: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

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
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now())

    conversacion: Mapped["Conversacion"] = relationship("Conversacion", back_populates="mensajes")


class SolicitudAgente(Base):
    __tablename__ = "solicitudes_agente"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("clientes.id", ondelete="SET NULL"), nullable=True)
    cotizacion_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("cotizaciones.id", ondelete="SET NULL"), nullable=True)
    conversacion_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("conversaciones.id", ondelete="SET NULL"), nullable=True)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="pendiente")
    prioridad: Mapped[Optional[str]] = mapped_column(String(10), default="normal")
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    datos_formulario: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    respuesta_encargada: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    archivo_adjunto: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now())
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
    tipo_contenido: Mapped[Optional[str]] = mapped_column(String(20), default="texto")
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now())

    solicitud: Mapped["SolicitudAgente"] = relationship("SolicitudAgente", back_populates="mensajes_internos")
