import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Cliente, Contacto
from src.tools.registry import register_tool

logger = logging.getLogger(__name__)


@register_tool(
    name="buscar_cliente",
    description="Busca un cliente en la base de datos por nombre de empresa. Devuelve datos del cliente y su contacto principal si existe.",
    parameters={
        "type": "object",
        "properties": {
            "empresa": {
                "type": "string",
                "description": "Nombre o parte del nombre de la empresa a buscar",
            }
        },
        "required": ["empresa"],
    },
)
async def buscar_cliente(empresa: str, db: AsyncSession) -> dict:
    stmt = (
        select(Cliente)
        .where(Cliente.nombre_empresa.ilike(f"%{empresa}%"))
        .limit(1)
    )
    result = await db.execute(stmt)
    cliente = result.scalar_one_or_none()

    if not cliente:
        return {"encontrado": False}

    # Buscar contacto principal
    stmt_contacto = (
        select(Contacto)
        .where(Contacto.cliente_id == cliente.id, Contacto.es_principal == True)  # noqa: E712
        .limit(1)
    )
    result_c = await db.execute(stmt_contacto)
    contacto = result_c.scalar_one_or_none()

    return {
        "encontrado": True,
        "cliente_id": cliente.id,
        "nombre_empresa": cliente.nombre_empresa,
        "tipo_cliente": cliente.tipo_cliente,
        "nivel_precio": cliente.nivel_precio,
        "es_recurrente": cliente.es_recurrente,
        "servicios_confirmados": cliente.servicios_confirmados,
        "exento_iva": cliente.exento_iva,
        "contacto_principal": {
            "id": contacto.id,
            "nombre": contacto.nombre_completo,
            "email": contacto.email,
            "telefono": contacto.telefono,
            "cargo": contacto.cargo,
        }
        if contacto
        else None,
    }


@register_tool(
    name="crear_cliente",
    description="Crea un nuevo cliente y su contacto principal en la base de datos.",
    parameters={
        "type": "object",
        "properties": {
            "nombre_empresa": {
                "type": "string",
                "description": "Nombre de la empresa",
            },
            "contacto_nombre": {
                "type": "string",
                "description": "Nombre completo del contacto principal",
            },
            "tipo_cliente": {
                "type": "string",
                "description": "Tipo de cliente: Empresa o Persona Natural",
                "default": "Empresa",
            },
            "contacto_email": {
                "type": "string",
                "description": "Email del contacto",
            },
            "contacto_telefono": {
                "type": "string",
                "description": "Teléfono del contacto",
            },
            "contacto_cargo": {
                "type": "string",
                "description": "Cargo del contacto en la empresa",
            },
        },
        "required": ["nombre_empresa", "contacto_nombre"],
    },
)
async def crear_cliente(
    nombre_empresa: str,
    contacto_nombre: str,
    db: AsyncSession,
    tipo_cliente: str = "Empresa",
    contacto_email: str | None = None,
    contacto_telefono: str | None = None,
    contacto_cargo: str | None = None,
) -> dict:
    cliente = Cliente(
        nombre_empresa=nombre_empresa,
        tipo_cliente=tipo_cliente,
    )
    db.add(cliente)
    await db.flush()  # Get ID without committing

    contacto = Contacto(
        cliente_id=cliente.id,
        nombre_completo=contacto_nombre,
        email=contacto_email,
        telefono=contacto_telefono,
        cargo=contacto_cargo,
        es_principal=True,
    )
    db.add(contacto)
    await db.flush()

    logger.info(f"Cliente creado: {nombre_empresa} (id={cliente.id})")

    return {"cliente_id": cliente.id, "contacto_id": contacto.id}
