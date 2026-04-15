import json
import logging

from langchain_core.tools import tool
from sqlalchemy import select

from src.db.engine import async_session_factory
from src.db.models import Cliente, Contacto

logger = logging.getLogger(__name__)


@tool
async def buscar_cliente(empresa: str) -> str:
    """
    Busca un cliente en la base de datos por nombre de empresa.
    Devuelve datos del cliente y TODOS sus contactos registrados,
    ya que un mismo cliente puede tener múltiples contactos con diferentes roles.
    Usa esta tool cuando tengas el nombre de la empresa pero no el ID del cliente.
    """
    async with async_session_factory() as db:
        stmt = (
            select(Cliente)
            .where(Cliente.nombre_empresa.ilike(f"%{empresa}%"))
            .limit(1)
        )
        result = await db.execute(stmt)
        cliente = result.scalar_one_or_none()

        if not cliente:
            return json.dumps({"encontrado": False})

        stmt_contactos = (
            select(Contacto)
            .where(Contacto.cliente_id == cliente.id)
            .order_by(Contacto.es_principal.desc(), Contacto.id)
        )
        result_c = await db.execute(stmt_contactos)
        contactos = result_c.scalars().all()

        return json.dumps({
            "encontrado": True,
            "cliente_id": cliente.id,
            "nombre_empresa": cliente.nombre_empresa,
            "tipo_cliente": cliente.tipo_cliente,
            "nivel_precio": cliente.nivel_precio,
            "es_recurrente": cliente.es_recurrente,
            "servicios_confirmados": cliente.servicios_confirmados,
            "exento_iva": cliente.exento_iva,
            "descuento_max_porcentaje": float(cliente.descuento_max_porcentaje),
            "notas_pricing": cliente.notas_pricing,
            "contactos": [
                {
                    "id": c.id,
                    "nombre": c.nombre_completo,
                    "email": c.email,
                    "telefono": c.telefono,
                    "cargo": c.cargo,
                    "es_principal": c.es_principal,
                }
                for c in contactos
            ],
        }, ensure_ascii=False)


@tool
async def buscar_contacto_por_telefono(telefono: str) -> str:
    """
    Busca un contacto y su empresa por número de teléfono.
    Úsala al inicio de la conversación para identificar si quien escribe
    ya está registrado como contacto de un cliente existente.
    Si lo encuentra, evita pedir datos que ya conocemos.
    """
    numero_limpio = telefono.lstrip("+")
    if numero_limpio.startswith("57") and len(numero_limpio) > 10:
        numero_limpio = numero_limpio[2:]

    async with async_session_factory() as db:
        stmt = (
            select(Contacto)
            .where(Contacto.telefono.ilike(f"%{numero_limpio}%"))
            .limit(1)
        )
        result = await db.execute(stmt)
        contacto = result.scalar_one_or_none()

        if not contacto:
            return json.dumps({"encontrado": False})

        stmt_cliente = select(Cliente).where(Cliente.id == contacto.cliente_id)
        result_c = await db.execute(stmt_cliente)
        cliente = result_c.scalar_one_or_none()

        if not cliente:
            return json.dumps({"encontrado": False})

        stmt_todos = (
            select(Contacto)
            .where(Contacto.cliente_id == cliente.id)
            .order_by(Contacto.es_principal.desc(), Contacto.id)
        )
        result_todos = await db.execute(stmt_todos)
        todos_contactos = result_todos.scalars().all()

        return json.dumps({
            "encontrado": True,
            "contacto_id": contacto.id,
            "nombre": contacto.nombre_completo,
            "email": contacto.email,
            "cargo": contacto.cargo,
            "cliente_id": cliente.id,
            "nombre_empresa": cliente.nombre_empresa,
            "nivel_precio": cliente.nivel_precio,
            "es_recurrente": cliente.es_recurrente,
            "servicios_confirmados": cliente.servicios_confirmados,
            "exento_iva": cliente.exento_iva,
            "descuento_max_porcentaje": float(cliente.descuento_max_porcentaje),
            "notas_pricing": cliente.notas_pricing,
            "otros_contactos_de_la_empresa": [
                {
                    "id": c.id,
                    "nombre": c.nombre_completo,
                    "cargo": c.cargo,
                    "es_principal": c.es_principal,
                }
                for c in todos_contactos
                if c.id != contacto.id
            ],
        }, ensure_ascii=False)


@tool
async def crear_cliente(
    nombre_empresa: str,
    contacto_nombre: str,
    tipo_cliente: str = "Empresa",
    contacto_email: str = "",
    contacto_telefono: str = "",
    contacto_cargo: str = "",
    nit: str = "",
    ciudad: str = "Bogotá",
    direccion: str = "",
    sector: str = "",
    exento_iva: bool = False,
    puede_aprobar_cotizacion: bool = False,
) -> str:
    """
    Crea un nuevo cliente y su contacto principal en la base de datos.
    Úsala solo cuando confirmes que el cliente NO existe (buscar_cliente devolvió encontrado=false)
    y tengas al menos nombre_empresa y nombre del contacto.

    nombre_empresa: Razón social o nombre de la empresa.
    contacto_nombre: Nombre completo del contacto que escribe.
    tipo_cliente: "Empresa" (default) o "Persona Natural".
    contacto_email: Email del contacto.
    contacto_telefono: Teléfono del contacto (el de WhatsApp si aplica).
    contacto_cargo: Cargo del contacto en la empresa.
    nit: NIT de la empresa (con dígito verificador si lo sabe, ej: "900123456-7").
    ciudad: Ciudad sede de la empresa (default Bogotá).
    direccion: Dirección de la empresa (opcional).
    sector: Sector económico (ej: "Salud", "Educación", "Gobierno").
    exento_iva: True si es entidad gubernamental o cliente extranjero exento de IVA.
    puede_aprobar_cotizacion: True si este contacto puede aprobar la cotización directamente.
    """
    async with async_session_factory() as db:
        cliente = Cliente(
            nombre_empresa=nombre_empresa,
            tipo_cliente=tipo_cliente,
            nit=nit or None,
            ciudad=ciudad or "Bogotá",
            direccion=direccion or None,
            sector=sector or None,
            exento_iva=exento_iva,
        )
        db.add(cliente)
        await db.flush()

        contacto = Contacto(
            cliente_id=cliente.id,
            nombre_completo=contacto_nombre.strip().title(),
            email=contacto_email or None,
            telefono=contacto_telefono or None,
            cargo=contacto_cargo or None,
            es_principal=True,
            puede_aprobar_cotizacion=puede_aprobar_cotizacion,
        )
        db.add(contacto)
        await db.commit()

        logger.info(f"Cliente creado: {nombre_empresa} (id={cliente.id})")
        return json.dumps({
            "cliente_id": cliente.id,
            "contacto_id": contacto.id,
            "nombre_empresa": nombre_empresa,
            "exento_iva": exento_iva,
        })


@tool
async def crear_contacto(
    cliente_id: int,
    nombre_completo: str,
    contacto_email: str = "",
    contacto_telefono: str = "",
    contacto_cargo: str = "",
    puede_aprobar_cotizacion: bool = False,
) -> str:
    """
    Crea un nuevo contacto para un cliente que YA EXISTE en la base de datos.
    Úsala cuando buscar_cliente encontró la empresa pero el contacto que escribe
    no está registrado (su número de WhatsApp no aparece en los contactos de esa empresa).

    cliente_id: ID del cliente existente (retornado por buscar_cliente).
    nombre_completo: Nombre completo del contacto.
    contacto_email: Email del contacto.
    contacto_telefono: Teléfono del contacto.
    contacto_cargo: Cargo del contacto en la empresa.
    puede_aprobar_cotizacion: True si puede tomar decisión de compra directamente.
    """
    async with async_session_factory() as db:
        contacto = Contacto(
            cliente_id=cliente_id,
            nombre_completo=nombre_completo.strip().title(),
            email=contacto_email or None,
            telefono=contacto_telefono or None,
            cargo=contacto_cargo or None,
            es_principal=False,
            puede_aprobar_cotizacion=puede_aprobar_cotizacion,
        )
        db.add(contacto)
        await db.commit()
        await db.refresh(contacto)

        logger.info(f"Contacto creado: {nombre_completo} para cliente_id={cliente_id} (contacto_id={contacto.id})")
        return json.dumps({
            "contacto_id": contacto.id,
            "nombre_completo": contacto.nombre_completo,
            "cliente_id": cliente_id,
            "puede_aprobar_cotizacion": puede_aprobar_cotizacion,
        })
