"""
Lógica de cálculo de cotizaciones.
Consulta tarifas reales de la DB, aplica reglas de pricing y crea el borrador.
NO depende de LangGraph — es Python puro invocable desde tools o tests.
"""
import logging
import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import cast, Date, func, or_, select

from src.db.engine import async_session_factory
from src.db.models import (
    Cliente,
    Cotizacion,
    LineaCotizacion,
    Recargo,
    Servicio,
    TarifaAlquilerEquipo,
)

logger = logging.getLogger(__name__)

VALIDEZ_OFERTA = "30 días calendario"
FORMA_PAGO = "50% anticipo, 50% al finalizar el servicio"
IVA_RATE = Decimal("0.19")

# Mapeo tipo_servicio → fragmentos ILIKE para buscar en Servicio.nombre
TIPO_SERVICIO_ILIKE: dict[str, list[str]] = {
    "interpretacion_simultanea_presencial": ["%simult%presencial%", "%presencial%simult%"],
    "interpretacion_simultanea_virtual": ["%simult%virtual%", "%simult%remot%", "%remot%simult%"],
    "interpretacion_consecutiva": ["%consecutiva%"],
    "traduccion_documentos": ["%traducci%document%", "%document%traducci%"],
    "transcripcion": ["%transcripci%"],
}

UNIDAD_LABEL: dict[str, str] = {
    "por_hora": "Hora(s)",
    "por_dia": "Día(s)",
    "por_palabra": "Palabra(s)",
    "por_minuto": "Minuto(s)",
    "por_pagina": "Página(s)",
    "por_evento": "Evento",
}


# ─── Helpers públicos ──────────────────────────────────────────────────────────

def formato_cop(monto) -> str:
    """$1.600.300 — formato colombiano sin decimales."""
    return f"${int(monto):,}".replace(",", ".")


def formato_cop_sin_signo(monto) -> str:
    """1.600.300 — sin signo $ (para celdas de la plantilla que ya tienen $)."""
    return f"{int(monto):,}".replace(",", ".")


# ─── Función principal ─────────────────────────────────────────────────────────

async def calcular_borrador(
    *,
    cliente_id: int,
    contacto_id: int | None,
    conversacion_id: int | None,
    tipo_servicio: str,
    idioma_destino: str,
    idioma_origen: str = "español",
    cantidad: float,
    num_interpretes: int = 2,
    num_receptores: int = 0,
    num_dias: int = 1,
    ubicacion: str = "",
    horario: str = "",
    fecha_inicio: str = "",
    fecha_fin: str = "",
) -> dict:
    """
    Calcula el precio de la cotización y persiste el borrador en DB.

    Notas sobre lineas_cotizacion:
    - servicio_id es NOT NULL en RDS → toda línea referencia un servicio.
    - Líneas de equipos: usan el servicio_id del servicio principal + equipo_alquiler_id.
    - Recargos: se suman al subtotal y se registran en notas_internas (sin línea separada).

    Returns:
        dict con cotizacion_id, numero_cotizacion, lineas, subtotal, iva, total,
        total_formateado, exento_iva, validez_oferta, forma_pago.
        En caso de error retorna {"error": True, "mensaje": str}.
    """
    nota_dos_interpretes = ""

    # ── Parseo de fechas (YYYY-MM-DD) ─────────────────────────────────────────
    fecha_inicio_date: date | None = _parsear_fecha(fecha_inicio)
    fecha_fin_date: date | None = _parsear_fecha(fecha_fin) or fecha_inicio_date

    # ── Corrección de año si el LLM usó año pasado ────────────────────────────
    hoy = date.today()
    if fecha_inicio_date and fecha_inicio_date < hoy:
        corrected = fecha_inicio_date.replace(year=hoy.year)
        fecha_inicio_date = corrected if corrected >= hoy else fecha_inicio_date.replace(year=hoy.year + 1)
    if fecha_fin_date and fecha_fin_date < hoy:
        corrected = fecha_fin_date.replace(year=hoy.year)
        fecha_fin_date = corrected if corrected >= hoy else fecha_fin_date.replace(year=hoy.year + 1)

    async with async_session_factory() as db:
        # 1. Cargar cliente
        cliente = await db.get(Cliente, cliente_id)
        if not cliente:
            return {"error": True, "mensaje": f"Cliente {cliente_id} no encontrado en DB."}

        # 2. Buscar tarifa del servicio principal
        servicio = await _buscar_servicio(db, tipo_servicio, idioma_origen, idioma_destino)
        if not servicio:
            return {
                "error": True,
                "mensaje": (
                    f"No encontré tarifa en el catálogo para '{tipo_servicio}' "
                    f"({idioma_origen} → {idioma_destino}). "
                    "Usa crear_solicitud(tipo='servicio_no_catalogado') para escalar."
                ),
            }

        # 3. Precio unitario con markup del cliente
        if cliente.markup_personalizado is not None:
            precio_unitario = servicio.precio_base * (1 + cliente.markup_personalizado / 100)
        else:
            precio_unitario = servicio.precio_cliente  # markup_porcentaje ya incluido

        # 4. Descuento automático para clientes premium
        descuento = Decimal("0")
        if cliente.nivel_precio == "premium" and cliente.descuento_min_porcentaje:
            descuento = cliente.descuento_min_porcentaje
        precio_con_descuento = precio_unitario * (1 - descuento / 100)

        # 5. Línea principal del servicio profesional
        es_interpretacion = servicio.unidad_cobro == "por_dia"

        if es_interpretacion:
            # ── Bandas de precio por horas/día ────────────────────────────────
            horas_por_dia_calc = cantidad / max(num_dias, 1)
            if horas_por_dia_calc <= 2:
                num_interpretes = 1
                precio_dia_banda = Decimal("1200000")
                banda = "sesion corta (hasta 2h)"
            elif horas_por_dia_calc <= 4:
                num_interpretes = 2
                precio_dia_banda = precio_unitario * Decimal("0.75")  # 1.950.000
                banda = "medio tiempo (2h-4h)"
            else:
                num_interpretes = 2
                precio_dia_banda = precio_unitario  # 2.600.000
                banda = "dia completo (> 4h)"

            precio_dia_con_descuento = precio_dia_banda * (1 - descuento / 100)
            precio_linea_principal = precio_dia_con_descuento * Decimal(str(num_dias))
            cantidad_display = Decimal(str(num_dias))
            precio_unitario_display = precio_dia_con_descuento
            unidad_label = "Día(s)"
            nota_dos_interpretes = f"({banda})" if num_interpretes == 2 else ""
        else:
            # ── Traducción / transcripción: precio por unidad ─────────────────
            precio_linea_principal = precio_con_descuento * Decimal(str(cantidad))
            cantidad_display = Decimal(str(cantidad))
            precio_unitario_display = precio_con_descuento
            unidad_label = UNIDAD_LABEL.get(servicio.unidad_cobro, servicio.unidad_cobro)

        descripcion_principal = (
            f"{servicio.nombre} — {idioma_origen.capitalize()} / {idioma_destino.capitalize()}"
        )
        if num_interpretes > 1:
            descripcion_principal += f" ({num_interpretes} intérpretes)"
        if nota_dos_interpretes:
            descripcion_principal += f" | {nota_dos_interpretes}"

        # lineas_data: lista de dicts para construir LineaCotizacion
        # IMPORTANTE: servicio_id es NOT NULL en RDS → siempre se hereda del servicio principal
        lineas_data: list[dict] = [
            {
                "servicio_id": servicio.id,       # siempre presente
                "equipo_alquiler_id": None,
                "descripcion_generada": descripcion_principal,
                "nombre_display": servicio.nombre,
                "idioma_origen": idioma_origen.capitalize(),
                "idioma_destino": idioma_destino.capitalize(),
                "horario": horario,
                "cantidad": cantidad_display,
                "unidad": unidad_label,
                "precio_unitario": precio_unitario_display,
                "precio_total": precio_linea_principal,
                "num_interpretes": num_interpretes,
                "num_dias": num_dias,
                "num_equipos": None,
                "fecha_inicio": fecha_inicio_date,
                "fecha_fin": fecha_fin_date,
            }
        ]

        # 6. Línea de equipos (receptores de simultánea)
        # La tabla tiene precio total por rango de cantidad + núm. de días (ya incluye todo).
        # servicio_id = servicio principal (constraint NOT NULL en RDS), equipo_alquiler_id = equipo real.
        equipo_notas = ""
        if num_receptores > 0:
            equipo = await _buscar_equipo_receptores(db, num_receptores, num_dias)
            if equipo:
                # precio_cliente ya es el total para el rango + días (no multiplicar)
                precio_equipos = equipo.precio_cliente
                lineas_data.append({
                    "servicio_id": servicio.id,        # hereda servicio principal (NOT NULL constraint)
                    "equipo_alquiler_id": equipo.id,
                    "descripcion_generada": (
                        f"Receptores de simultánea — {num_receptores} unidades × {num_dias} día(s)"
                    ),
                    "nombre_display": "Receptores de simultánea",
                    "idioma_origen": "",
                    "idioma_destino": "",
                    "horario": "",
                    "cantidad": Decimal(str(num_receptores)),
                    "unidad": "Global",
                    "precio_unitario": precio_equipos,
                    "precio_total": precio_equipos,
                    "num_interpretes": None,
                    "num_dias": num_dias,
                    "num_equipos": num_receptores,
                    "fecha_inicio": fecha_inicio_date,
                    "fecha_fin": fecha_fin_date,
                })
            else:
                equipo_notas = (
                    f"{num_receptores} receptores de simultánea × {num_dias} día(s): "
                    "tarifa no encontrada en catálogo"
                )

        # 7. Recargo fuera de Bogotá
        # NO se crea una LineaCotizacion separada (servicio_id NOT NULL hace esto complejo).
        # Se suma al subtotal y se registra en notas_internas de la Cotizacion.
        es_fuera_de_bogota = _detectar_fuera_de_bogota(ubicacion)
        monto_recargo = Decimal("0")
        recargo_nota = ""
        if es_fuera_de_bogota:
            recargo = await _buscar_recargo(db, "bogot")
            if recargo and recargo.porcentaje:
                subtotal_sin_recargo = sum(l["precio_total"] for l in lineas_data)
                monto_recargo = subtotal_sin_recargo * recargo.porcentaje / 100
                recargo_nota = (
                    f"Recargo desplazamiento fuera de Bogotá: "
                    f"{recargo.porcentaje}% = {formato_cop(monto_recargo)}"
                )

        # 8. Totales
        subtotal = sum(l["precio_total"] for l in lineas_data) + monto_recargo
        iva = Decimal("0") if cliente.exento_iva else subtotal * IVA_RATE
        total = subtotal + iva

        # 9. Número de cotización
        numero = await _generar_numero_cotizacion(db)

        # 10. Notas internas (recargo + equipo faltante)
        notas_partes = [p for p in [recargo_nota, equipo_notas] if p]
        notas_internas = " | ".join(notas_partes) if notas_partes else None

        # 11. Persistir Cotizacion en DB
        cotizacion = Cotizacion(
            cliente_id=cliente_id,
            contacto_id=contacto_id,
            numero_cotizacion=numero,
            fecha=date.today(),
            ubicacion_evento=ubicacion or "Bogotá",
            es_fuera_de_bogota=es_fuera_de_bogota,
            subtotal=subtotal,
            iva=iva,
            total=total,
            exento_iva=cliente.exento_iva,
            validez_oferta=VALIDEZ_OFERTA,
            forma_pago=FORMA_PAGO,
            estado="borrador",
            notas_internas=notas_internas,
        )
        db.add(cotizacion)
        await db.flush()  # obtiene cotizacion.id

        # 12. Persistir líneas
        for i, l in enumerate(lineas_data):
            db.add(LineaCotizacion(
                cotizacion_id=cotizacion.id,
                servicio_id=l["servicio_id"],
                equipo_alquiler_id=l.get("equipo_alquiler_id"),
                cantidad=l["cantidad"],
                precio_unitario=l["precio_unitario"],
                precio_total=l["precio_total"],
                horario=l["horario"] or None,
                num_interpretes=l.get("num_interpretes"),
                num_dias=l.get("num_dias"),
                num_equipos=l.get("num_equipos"),
                descripcion_generada=l["descripcion_generada"],
                fecha_servicio_inicio=l.get("fecha_inicio"),
                fecha_servicio_fin=l.get("fecha_fin"),
                orden=i,
            ))

        await db.commit()

        logger.info(
            f"Cotización creada: {numero} | cliente_id={cliente_id} | "
            f"subtotal={formato_cop(subtotal)} | total={formato_cop(total)}"
        )

        # 13. Preparar output enriquecido para chatbot y Word
        lineas_output = []
        for i, l in enumerate(lineas_data):
            lineas_output.append({
                "numero": i + 1,
                "servicio": l["nombre_display"],
                "idioma_origen": l["idioma_origen"],
                "idioma_destino": l["idioma_destino"],
                "horario": l["horario"],
                "cantidad": float(l["cantidad"]),
                "unidad": l["unidad"],
                "precio_unitario": float(l["precio_unitario"]),
                "precio_total": float(l["precio_total"]),
                "descripcion": l["descripcion_generada"],
            })

        # Agregar recargo como línea de resumen para el chatbot (sin ir a DB)
        if monto_recargo > 0:
            lineas_output.append({
                "numero": len(lineas_output) + 1,
                "servicio": "Recargo fuera de Bogotá",
                "idioma_origen": "",
                "idioma_destino": "",
                "horario": "",
                "cantidad": 1,
                "unidad": "%",
                "precio_unitario": float(monto_recargo),
                "precio_total": float(monto_recargo),
                "descripcion": recargo_nota,
            })

        return {
            "cotizacion_id": cotizacion.id,
            "numero_cotizacion": numero,
            "lineas": lineas_output,
            "subtotal": float(subtotal),
            "iva": float(iva),
            "total": float(total),
            "total_formateado": formato_cop(total),
            "exento_iva": cliente.exento_iva,
            "validez_oferta": VALIDEZ_OFERTA,
            "forma_pago": FORMA_PAGO,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "nota_interpretes": nota_dos_interpretes or None,
        }


# ─── Helpers privados ──────────────────────────────────────────────────────────

def _parsear_fecha(fecha_str: str) -> date | None:
    """Parsea fecha en formato YYYY-MM-DD. Retorna None si no es válida."""
    if not fecha_str:
        return None
    try:
        return datetime.strptime(fecha_str.strip(), "%Y-%m-%d").date()
    except ValueError:
        # Intento alternativo con otros separadores comunes
        limpia = re.sub(r"[/.]", "-", fecha_str.strip())
        try:
            return datetime.strptime(limpia, "%Y-%m-%d").date()
        except ValueError:
            logger.warning(f"No se pudo parsear fecha: {fecha_str!r}")
            return None


def _normalizar(texto: str) -> str:
    """Quita tildes y pasa a minúsculas para comparación sin acento."""
    return "".join(
        c for c in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(c) != "Mn"
    )


async def _buscar_servicio(
    db, tipo_servicio: str, idioma_origen: str, idioma_destino: str
) -> Servicio | None:
    patrones = TIPO_SERVICIO_ILIKE.get(tipo_servicio, [f"%{tipo_servicio}%"])
    condiciones = [Servicio.nombre.ilike(p) for p in patrones]

    q = (
        select(Servicio)
        .where(Servicio.activo.is_(True))
        .where(or_(*condiciones))
    )
    # Filtro de idioma destino: comparar sin acentos (DB puede tener "ingles" vs "inglés")
    if idioma_destino:
        destino_norm = _normalizar(idioma_destino)
        # Buscar con y sin tilde: ej. "ingles" y "inglés"
        q = q.where(
            or_(
                Servicio.idioma_destino.ilike(f"%{idioma_destino}%"),
                Servicio.idioma_destino.ilike(f"%{destino_norm}%"),
                Servicio.idioma_destino == "",
            )
        )
    result = await db.execute(q.limit(1))
    return result.scalar_one_or_none()


async def _buscar_equipo_receptores(
    db, num_receptores: int, num_dias: int
) -> TarifaAlquilerEquipo | None:
    """
    Busca la tarifa de receptores de simultánea según rango de cantidad y número de días.
    La tabla tiene precio total por evento (no por unidad).
    """
    result = await db.execute(
        select(TarifaAlquilerEquipo)
        .where(TarifaAlquilerEquipo.tipo_equipo == "receptores_simultanea")
        .where(TarifaAlquilerEquipo.activo.is_(True))
        .where(TarifaAlquilerEquipo.cantidad_min <= num_receptores)
        .where(TarifaAlquilerEquipo.cantidad_max >= num_receptores)
        .where(TarifaAlquilerEquipo.num_dias == num_dias)
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _buscar_recargo(db, nombre_fragmento: str) -> Recargo | None:
    result = await db.execute(
        select(Recargo)
        .where(
            or_(
                Recargo.nombre.ilike(f"%{nombre_fragmento}%"),
                Recargo.condicion.ilike(f"%{nombre_fragmento}%"),
            )
        )
        .where(Recargo.activo.is_(True))
        .limit(1)
    )
    return result.scalar_one_or_none()


def _detectar_fuera_de_bogota(ubicacion: str) -> bool:
    if not ubicacion:
        return False
    u = ubicacion.lower()
    bogota_keywords = {"bogotá", "bogota", "bldc", "cundinamarca"}
    return not any(kw in u for kw in bogota_keywords)


async def _generar_numero_cotizacion(db) -> str:
    hoy = date.today()
    result = await db.execute(
        select(func.count(Cotizacion.id)).where(
            cast(Cotizacion.created_at, Date) == hoy
        )
    )
    count = result.scalar() or 0
    return f"COT-{hoy.strftime('%Y%m%d')}-{count + 1:03d}"
