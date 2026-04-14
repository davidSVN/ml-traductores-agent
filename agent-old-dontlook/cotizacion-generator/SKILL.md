---
name: cotizacion-generator
description: "Genera cotizaciones para ML Traductores. Usa esta skill SIEMPRE que necesites: armar una cotización, calcular precios de interpretación/traducción/transcripción, consultar tarifas de servicios o equipos, validar datos de un cliente, o generar el documento Word/PDF final. También úsala cuando el cliente pregunte cuánto cuesta un servicio, cuando llegue una solicitud por WhatsApp, o cuando necesites consultar el historial de un cliente. Triggers: cotización, cotizar, precio, tarifa, cuánto cuesta, generar PDF, interpretación, traducción, alquiler de equipos, cliente nuevo."
---

# Skill: Generador de Cotizaciones ML Traductores

## Arquitectura

Esta skill tiene dos capas:

1. **Este documento (SKILL.md)**: Te enseña qué consultar en la DB, cómo interpretar cada campo, cómo calcular precios, y cuándo pedir aprobación. Tú (el agente) eres el cerebro.
2. **El script `scripts/generar_cotizacion.py`**: Recibe un JSON con datos ya decididos y produce el Word/PDF. Es la impresora. No toma decisiones.

Hay **dos frentes de comunicación** que debes manejar:
- **Frente 1 (Cliente ↔ Agente)**: WhatsApp en producción, terminal en pruebas. Aquí recoges la solicitud.
- **Frente 2 (Encargada ↔ Agente)**: Terminal por ahora, web en el futuro. Aquí validas cliente y pides aprobación.

---

## PASO 1: Recoger solicitud del cliente (Frente 1)

Del cliente necesitas obtener en conversación natural:

| Campo | Obligatorio | Ejemplo |
|-------|------------|---------|
| Nombre completo | Sí | "Carlos Mendoza" |
| Empresa | Sí | "Banco de la República" |
| Cargo | No | "Director de Comunicaciones" |
| Email | Sí | "cmendoza@banrep.gov.co" |
| Teléfono | Sí | "3209876543" |
| Qué servicio(s) necesita | Sí | "Interpretación simultánea presencial" |
| Idioma(s) | Sí para interp/trad | "Español-Inglés" |
| Fecha(s) del evento | Sí | "20 y 21 de mayo 2026" |
| Horario | Sí para interp | "9am a 4pm" |
| Ubicación | Sí para presencial | "Bogotá, Auditorio León de Greiff" |
| Cantidad | Sí | 2 días, 200 equipos, 5000 palabras |
| Número de intérpretes | Si aplica | 1 o 2 |

No preguntes todo de golpe. Guía la conversación naturalmente.

---

## PASO 2: Buscar o crear cliente en DB (Frente 2 si es necesario)

### 2a. Buscar cliente existente

```sql
SELECT c.id, c.nombre_empresa, c.nit, c.nivel_precio, 
       c.descuento_min_porcentaje, c.descuento_max_porcentaje,
       c.markup_personalizado, c.notas_pricing, c.exento_iva, 
       c.es_recurrente, c.servicios_confirmados, c.ciudad, c.direccion
FROM clientes c 
WHERE c.nombre_empresa ILIKE '%{empresa}%'
LIMIT 1;
```

### 2b. Interpretar los campos del cliente

Cuando obtengas el resultado, esto es lo que significa cada campo:

- **`nivel_precio`**: `'premium'` = cliente de alto valor, siempre dar mejor tarifa. `'estandar'` = cliente regular. `'nuevo'` = primera vez, precio completo.
- **`descuento_min_porcentaje`**: Descuento mínimo que PUEDES aplicar. Para premium típicamente es 5-10%. Para nuevo es 0%.
- **`descuento_max_porcentaje`**: Techo de descuento SIN aprobación de la encargada. Si el cliente pide más, debes escalar.
- **`markup_personalizado`**: Si NO es NULL, este cliente tiene un markup especial. Debes recalcular el precio desde `servicios.precio_base` usando este % en vez del 30% estándar. Si es NULL, usa `servicios.precio_cliente` directamente.
- **`notas_pricing`**: **LEE ESTO CON ATENCIÓN.** Son instrucciones de María Luisa sobre cómo tratar a este cliente. Ejemplos: "Siempre ofrecer tarifa preferencial", "ONG sin ánimo de lucro, aplicar descuento especial", "Compara con la competencia, ser agresivo en precio".
- **`exento_iva`**: Si es TRUE, el IVA es $0. No cobrar 19%.
- **`servicios_confirmados`**: Cuántas cotizaciones se han convertido en servicios reales. Más historial = más confianza para dar descuento.
- **`es_recurrente`**: TRUE si ha contratado 3+ veces.

### 2c. Si el cliente NO existe o tiene datos incompletos → FRENTE 2

**PAUSA OBLIGATORIA.** No avances sin completar esto.

Envía a la encargada (por terminal) un mensaje así:

```
══════════════════════════════════════════
⚠️  CLIENTE NUEVO O DATOS INCOMPLETOS
══════════════════════════════════════════
Cliente: {empresa}
Contacto: {nombre}

Se requiere completar la siguiente información:

1. NIT: ___
2. Nivel de precio (premium/estandar/nuevo): ___
3. Descuento mínimo %: ___
4. Descuento máximo %: ___
5. Markup personalizado % (o dejar 30% estándar): ___
6. ¿Exento de IVA? (sí/no): ___
7. Dirección: ___
8. Ciudad: ___
9. Notas de pricing: ___

Responda con los valores o escriba "estándar" para
usar valores por defecto (nuevo, 0%, 0%, 30%, no).
══════════════════════════════════════════
```

**Valores por defecto si la encargada dice "estándar":**
- nivel_precio = 'nuevo'
- descuento_min = 0, descuento_max = 0
- markup_personalizado = NULL (usa 30% estándar)
- exento_iva = FALSE

Espera la respuesta. Cuando llegue, inserta/actualiza en DB:

```sql
INSERT INTO clientes (nombre_empresa, nit, nivel_precio, descuento_min_porcentaje, 
                      descuento_max_porcentaje, markup_personalizado, exento_iva,
                      ciudad, direccion, notas_pricing, tipo_cliente)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Empresa')
ON CONFLICT (nombre_empresa) DO UPDATE SET
  nit = EXCLUDED.nit,
  nivel_precio = EXCLUDED.nivel_precio,
  descuento_min_porcentaje = EXCLUDED.descuento_min_porcentaje,
  descuento_max_porcentaje = EXCLUDED.descuento_max_porcentaje,
  markup_personalizado = EXCLUDED.markup_personalizado,
  notas_pricing = EXCLUDED.notas_pricing;
```

Luego inserta el contacto:

```sql
INSERT INTO contactos (cliente_id, nombre_completo, email, telefono, cargo, puede_aprobar_cotizacion)
VALUES (%s, %s, %s, %s, %s, FALSE)
ON CONFLICT DO NOTHING;
```

---

## PASO 3: Consultar tarifas y calcular precios

### 3a. Servicios de interpretación, traducción, transcripción

```sql
SELECT id, nombre, precio_base, precio_cliente, unidad_cobro, 
       markup_porcentaje, notas, num_interpretes_default, es_presencial
FROM servicios 
WHERE nombre ILIKE '%{servicio}%' 
  AND idioma_destino = '{idioma}'
  AND activo = TRUE;
```

**Cómo interpretar las columnas:**

- **`precio_base`**: Costo real del servicio (lo que ML Traductores paga). NO mostrar al cliente.
- **`precio_cliente`**: Precio de lista para el cliente, con markup del 30% ya incluido. ESTE es el punto de partida.
- **`unidad_cobro`**: Define cómo multiplicar. `'por_hora'` = precio × horas. `'por_palabra'` = precio × palabras. `'por_minuto'` = precio × minutos.
- **`notas`**: Texto que va en la sección "Notas y condiciones" de la cotización. Separado por saltos de línea.
- **`num_interpretes_default`**: 2 para presencial (conferencia), 1 para virtual/señas. NULL para traducción.

### 3b. Equipos de alquiler

```sql
SELECT id, tipo_equipo, precio_proveedor, precio_cliente, 
       descripcion, notas, cantidad_min, cantidad_max, num_dias
FROM tarifas_alquiler_equipos 
WHERE tipo_equipo = '{tipo}'
  AND cantidad_min <= {cantidad} AND cantidad_max >= {cantidad}
  AND num_dias = {dias}
  AND activo = TRUE;
```

**Tipos de equipo válidos:** `'receptores_simultanea'`, `'portatiles'`, `'transmisor_portatil_adicional'`, `'cabina_relay'`, `'microfono_inalambrico'`, `'montaje_nocturno'`, `'montaje_fin_semana'`, `'montaje_dia_anterior'`

**IMPORTANTE:** Para receptores de simultánea, el precio ya incluye el paquete completo (cabina + consola + receptores + técnico + personal). Para portátiles, si son más de 1 día, multiplicar el precio de 1 día × número de días (no hay tabla de descuento por múltiples días como en simultánea).

Si necesitan más de 500 receptores o más de 5 días, no hay tarifa en la tabla. Escalar a la encargada.

### 3c. Servicios de montaje (si aplica)

Preguntar al cliente si necesita montaje especial. Si el montaje es en horario laboral estándar (lunes a viernes antes de 6pm), está incluido sin cargo adicional. Si es fuera de horario:

```sql
SELECT precio_cliente, descripcion 
FROM tarifas_alquiler_equipos 
WHERE tipo_equipo IN ('montaje_nocturno', 'montaje_fin_semana', 'montaje_dia_anterior')
  AND activo = TRUE;
```

---

## PASO 4: Calcular el precio final — FÓRMULAS

### Fórmula para servicios (interpretación / traducción / transcripción):

```
SI cliente.markup_personalizado IS NOT NULL:
    PRECIO_UNITARIO = servicios.precio_base × (1 + cliente.markup_personalizado / 100)
SINO:
    PRECIO_UNITARIO = servicios.precio_cliente  (ya tiene markup 30%)

CANTIDAD = según unidad_cobro:
    por_hora   → número de horas del evento
    por_palabra → número de palabras del documento
    por_minuto  → minutos de audio/video

DESCUENTO = tú decides entre 0% y cliente.descuento_max_porcentaje
    Lee cliente.notas_pricing para orientarte.
    Si nivel_precio='premium' → empieza con descuento_min como base
    Si nivel_precio='nuevo' → normalmente 0%
    Si el cliente negocia → puedes subir hasta descuento_max

PRECIO_LINEA = PRECIO_UNITARIO × CANTIDAD × (1 - DESCUENTO / 100)
```

### Fórmula para equipos de alquiler:

```
PRECIO_EQUIPOS = tarifas_alquiler_equipos.precio_cliente
    (ya tiene markup 25%, ya contempla cantidad + días)

DESCUENTO_EQUIPOS = normalmente 0% (es costo de proveedor)
    EXCEPTO si: cliente es premium + servicios_confirmados > 5 + notas_pricing lo sugiere
    En ese caso puedes aplicar hasta cliente.descuento_max_porcentaje
    Pero si aplicas descuento a equipos → requiere aprobación (ver Paso 5)
```

### Fórmula de totales:

```
SUBTOTAL = Σ todos los PRECIO_LINEA (servicios + equipos + montaje)
IVA = SUBTOTAL × 0.19       (0 si cliente.exento_iva = TRUE)
TOTAL = SUBTOTAL + IVA
```

**No redondear. Dejar precios exactos.**

### Formato de montos (COP):

Siempre mostrar como `$1.600.300` (puntos como separador de miles, sin decimales).

---

## PASO 5: Registrar borrador y pedir aprobación (Frente 2) — OBLIGATORIO

### 5a. ANTES de mostrar el resumen, registrar el borrador en DB

Cada cotización se registra desde el primer momento, en estado `'borrador'`. Esto garantiza que toda versión quede trazada.

```sql
-- Obtener siguiente número de cotización
SELECT COALESCE(MAX(CAST(numero_cotizacion AS INTEGER)), 0) + 1 
FROM cotizaciones WHERE numero_cotizacion ~ '^\d+$';
```

```sql
-- Insertar cotización en estado borrador
INSERT INTO cotizaciones (cliente_id, contacto_id, numero_cotizacion, version,
  fecha, ubicacion_evento, es_fuera_de_bogota, subtotal, iva, total, exento_iva,
  validez_oferta, forma_pago, estado, notas_internas)
VALUES (%s, %s, %s, NULL, CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s, %s, 
  'borrador', 'Primera versión generada por el agente')
RETURNING id;
```

```sql
-- Insertar TODAS las líneas de esta versión
INSERT INTO lineas_cotizacion (cotizacion_id, servicio_id, cantidad, 
  precio_unitario, precio_total, fecha_servicio_inicio, fecha_servicio_fin,
  horario, num_interpretes, num_equipos, descripcion_generada, notas_linea, orden)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
```

### 5b. Mostrar resumen a la encargada y esperar

**PAUSA OBLIGATORIA.** Enviar por terminal:

```
══════════════════════════════════════════════════
📋 COTIZACIÓN PARA APROBACIÓN — COT {número}
══════════════════════════════════════════════════
Cliente: {empresa} ({nivel_precio})
Contacto: {nombre} — {email}
Ubicación: {ubicacion}
Descuento aplicado: {descuento}%
══════════════════════════════════════════════════

# │ Servicio                     │ Detalle              │ Precio
──┼──────────────────────────────┼──────────────────────┼───────────
1 │ Interp. sim. presencial      │ ES-EN, 2 int, 2 días │ $3.200.600
2 │ Equipos trad. simultánea     │ 200 rec, 2 días      │ $2.062.500
3 │ Montaje día anterior         │ 19 mayo, 2pm-6pm     │ $237.500
──┼──────────────────────────────┼──────────────────────┼───────────
                                         Subtotal:  $5.500.600
                                         IVA 19%:   $1.045.114
                                         TOTAL:     $6.545.714

Notas que se incluirán:
♦ Para conferencia se requieren 2 intérpretes a partir de 1.5 hrs.
♦ Un día de equipos = 8 horas o fracción.
♦ Transporte, instalación y desmantelamiento incluido.

Validez: Confirmación a más tardar 1 mes antes
Pago: A 30 días
══════════════════════════════════════════════════

Opciones:
  [A] Aprobar y generar PDF
  [M] Modificar (especificar qué cambiar)
  [R] Rechazar (especificar motivo)

Respuesta:
```

### 5c. Procesar la respuesta de la encargada

**Si responde "A" o "Aprobar":**

Actualizar estado en DB y continuar al Paso 6:
```sql
UPDATE cotizaciones SET estado = 'enviada', fecha_envio = CURRENT_DATE
WHERE id = {cotizacion_id};
```

**Si responde "M" o describe cambios:**

REGISTRAR LA VERSIÓN ACTUAL antes de modificar:

```sql
-- Registrar la versión que está siendo reemplazada
INSERT INTO versiones_cotizacion (cotizacion_id, letra_version, fecha,
  total_anterior, total_nuevo, cambios, aprobada)
VALUES (
  {cotizacion_id}, 
  {siguiente_letra},  -- 'A' para la primera modificación, 'B' para la segunda, etc.
  CURRENT_DATE,
  {total_actual},      -- Total ANTES del cambio
  NULL,                -- Se llena después con el nuevo total
  {texto_cambios},     -- Lo que la encargada pidió, textual. Ej: "Bajar interpretación a $2.800.000"
  FALSE
);
```

Para calcular `{siguiente_letra}`:
```sql
SELECT COALESCE(
  CHR(ASCII('A') + COUNT(*)),
  'A'
) FROM versiones_cotizacion WHERE cotizacion_id = {cotizacion_id};
```

Luego:
1. Aplicar los cambios solicitados (recalcular precios, ajustar líneas)
2. ELIMINAR las líneas anteriores y insertar las nuevas:
```sql
DELETE FROM lineas_cotizacion WHERE cotizacion_id = {cotizacion_id};
-- Insertar nuevas líneas con precios actualizados (mismo INSERT de paso 5a)
```
3. Actualizar los totales de la cotización:
```sql
UPDATE cotizaciones 
SET subtotal = %s, iva = %s, total = %s, version = {letra_actual},
    notas_internas = COALESCE(notas_internas, '') || E'\n' || 
      '[' || NOW()::text || '] Modificación ' || {letra} || ': ' || {texto_cambios}
WHERE id = {cotizacion_id};
```
4. Actualizar el `total_nuevo` en la versión:
```sql
UPDATE versiones_cotizacion 
SET total_nuevo = {nuevo_total}
WHERE cotizacion_id = {cotizacion_id} AND letra_version = {letra_actual};
```
5. **VOLVER al paso 5b** — Mostrar el resumen actualizado para nueva aprobación.

**Si responde "R" o "Rechazar":**

REGISTRAR el rechazo con el motivo:

```sql
-- Actualizar estado a rechazada con motivo
UPDATE cotizaciones 
SET estado = 'rechazada',
    razon_perdida = {motivo_textual},  -- Lo que la encargada dijo. Ej: "Precio fuera de presupuesto del cliente"
    notas_internas = COALESCE(notas_internas, '') || E'\n' || 
      '[' || NOW()::text || '] RECHAZADA: ' || {motivo_textual}
WHERE id = {cotizacion_id};
```

Luego informar al cliente (Frente 1) de forma profesional SIN revelar el motivo interno:
```
Estamos revisando su solicitud internamente. Le informaremos a la brevedad con una propuesta actualizada.
```

**IMPORTANTE:** Las líneas de cotización NO se eliminan en caso de rechazo. Quedan como registro histórico de lo que se propuso y fue rechazado.

### 5d. Historial que se acumula en `notas_internas`

Cada interacción se concatena en `cotizaciones.notas_internas` con timestamp. Ejemplo de cómo se ve después de varias iteraciones:

```
[2026-04-08 10:30:00] Primera versión generada por el agente
[2026-04-08 10:35:00] Modificación A: Bajar interpretación de $1.600.300 a $1.400.000, encargada considera que es cliente de alto valor
[2026-04-08 10:40:00] Modificación B: Agregar descuento del 5% en equipos, cliente tiene más de 10 servicios confirmados
[2026-04-08 10:42:00] APROBADA versión B
```

Este historial es CONTEXTO VALIOSO. En futuras cotizaciones para el mismo cliente, el agente debe consultar:

```sql
SELECT c.numero_cotizacion, c.version, c.total, c.estado, c.razon_perdida, c.notas_internas
FROM cotizaciones c
WHERE c.cliente_id = {cliente_id}
ORDER BY c.fecha DESC
LIMIT 5;
```

Esto le permite al agente aprender que para este cliente la encargada siempre baja el precio de interpretación, o que siempre agrega descuento en equipos, y ANTICIPAR esos ajustes en la primera versión de la próxima cotización.

---

## PASO 6: Generar el documento Word/PDF

**Solo después de que el estado sea `'enviada'` (aprobación recibida).** Preparar el JSON con esta estructura exacta y llamar al script:

```json
{
  "numero_cotizacion": "050",
  "fecha": "8 de abril de 2026",
  "cliente": {
    "nombre_contacto": "Carlos Mendoza",
    "cargo": "Director de Comunicaciones",
    "empresa": "Banco de la República",
    "email": "cmendoza@banrep.gov.co",
    "telefono": "3209876543",
    "nombre_corto": "Carlos"
  },
  "evento": {
    "tipo": "presencial",
    "ubicacion": "Bogotá, sede principal",
    "referencia": "Cotización interpretación simultánea y equipos"
  },
  "lineas": [
    {
      "numero": 1,
      "servicio": "Interp. simultánea presencial",
      "idioma_origen": "Español",
      "idioma_destino": "Inglés",
      "fechas": "20-21 mayo 2026",
      "horario": "9am a 4pm",
      "cantidad": 2,
      "unidad": "Día",
      "precio_unitario": 1600300,
      "precio_total": 3200600,
      "notas_detalle": "2 intérpretes de conferencia, 7 hrs/día"
    }
  ],
  "totales": {
    "subtotal": 5500600,
    "iva": 1045114,
    "total": 6545714,
    "exento_iva": false
  },
  "condiciones": {
    "notas": ["♦ Nota 1...", "♦ Nota 2..."],
    "validez_oferta": "Confirmación a más tardar 20 de abril 2026",
    "forma_pago": "A 30 días"
  },
  "template_path": "{ruta al assets/Formato_Cotizaciones_v2.docx}",
  "output_dir": "{ruta donde guardar los PDFs}"
}
```

Ejecutar:

```bash
python {ruta}/scripts/generar_cotizacion.py --datos '{JSON}'
# O guardar el JSON en archivo y usar:
python {ruta}/scripts/generar_cotizacion.py --archivo datos.json
```

El script retorna:
```json
{
  "success": true,
  "docx_path": "cotizaciones/COT_050_Banco_de_la_República.docx",
  "pdf_path": "cotizaciones/COT_050_Banco_de_la_República.pdf",
  "numero_cotizacion": "050",
  "total_formateado": "$6.545.714"
}
```

---

## PASO 7: Registrar envío e informar a ambos frentes

La cotización ya está en DB desde el Paso 5a. Ahora solo actualizar el estado y notificar.

### 7a. Actualizar cotización (ya existe en DB)

```sql
UPDATE cotizaciones 
SET estado = 'enviada', fecha_envio = CURRENT_DATE
WHERE id = {cotizacion_id};
```

### 7b. Actualizar contador del cliente

```sql
UPDATE clientes SET ultima_cotizacion = CURRENT_DATE WHERE id = {cliente_id};
```

### 7c. Informar a ambos frentes

**Al cliente (Frente 1):** Enviar el PDF y un mensaje como:
```
Adjunto encontrará la cotización COT-050 por un valor de $6.545.714 COP (IVA incluido).
La oferta es válida hasta [fecha]. Quedamos atentos a su confirmación.
```

**A la encargada (Frente 2):**
```
✓ Cotización COT-050 enviada a Carlos Mendoza (Banco de la República)
  Total: $6.545.714 | Versión: {version o 'Original'}
  PDF: cotizaciones/COT_050_Banco_de_la_República.pdf
```

---

## PASO 8: Seguimiento post-envío

Después de enviar la cotización, el agente debe estar atento a la respuesta del cliente. Actualizar el estado según corresponda:

**Si el cliente aprueba** (formal o informal: "ok", "aprobado", "dale", "listo"):
```sql
UPDATE cotizaciones 
SET estado = 'aprobada', fecha_respuesta = CURRENT_DATE, fecha_cierre = CURRENT_DATE
WHERE id = {cotizacion_id};

UPDATE clientes 
SET servicios_confirmados = servicios_confirmados + 1,
    es_recurrente = CASE WHEN servicios_confirmados + 1 >= 3 THEN TRUE ELSE es_recurrente END
WHERE id = {cliente_id};
```

**Si el cliente pide cambios** (negocia precio, cambia fechas, agrega servicios):
```sql
UPDATE cotizaciones SET estado = 'negociando' WHERE id = {cotizacion_id};
```
Luego volver al Paso 4 (recalcular) → Paso 5 (nueva aprobación de encargada) → Paso 6 (nuevo PDF). Esto genera una nueva versión (A, B, C...) con trazabilidad completa.

**Si el cliente no responde** después del periodo configurado:
```sql
UPDATE cotizaciones SET estado = 'en_seguimiento' WHERE id = {cotizacion_id};
```
El agente debe hacer seguimiento automático según las reglas de la tabla `recargos` o la configuración del sistema.

**Si la cotización se pierde** (el cliente elige a otro proveedor, cancela el evento, etc.):
```sql
UPDATE cotizaciones 
SET estado = 'perdida', razon_perdida = {motivo}, fecha_respuesta = CURRENT_DATE
WHERE id = {cotizacion_id};
```

**IMPORTANTE:** La `razon_perdida` es información de altísimo valor. El agente debe intentar obtenerla del cliente de forma profesional: "¿Hubo algo que podamos mejorar para futuras ocasiones?" Esto alimenta el aprendizaje del sistema.

### Consultar historial para futuras cotizaciones

Antes de armar cualquier cotización nueva, el agente DEBE consultar el historial del cliente:

```sql
-- Últimas 5 cotizaciones del cliente con sus versiones
SELECT c.numero_cotizacion, c.version, c.total, c.estado, 
       c.razon_perdida, c.notas_internas, c.fecha
FROM cotizaciones c
WHERE c.cliente_id = {cliente_id}
ORDER BY c.fecha DESC
LIMIT 5;

-- Versiones de negociación (muestra cómo se ajustaron precios)
SELECT v.letra_version, v.total_anterior, v.total_nuevo, v.cambios
FROM versiones_cotizacion v
JOIN cotizaciones c ON c.id = v.cotizacion_id
WHERE c.cliente_id = {cliente_id}
ORDER BY c.fecha DESC, v.letra_version;
```

Con este historial el agente puede anticipar: "Las últimas 3 cotizaciones de Compensar fueron modificadas para agregar 5% de descuento. Voy a aplicar ese descuento desde la primera versión esta vez."

---

## Mapeo de servicios

Cuando el cliente dice algo informal, mapea al nombre correcto en la DB:

| El cliente dice | Buscar como |
|----------------|-------------|
| "interpretación presencial", "intérpretes para evento", "simultánea" | `nombre ILIKE '%simultánea presencial%'` |
| "interpretación virtual", "por zoom", "remota" | `nombre ILIKE '%remota%Zoom%'` |
| "traducción", "traducir documento", "traducción escrita" | `nombre ILIKE '%Traducción de documentos%'` |
| "transcripción de audio", "transcribir audio" | `nombre ILIKE '%Transcripción de audio%'` |
| "transcripción de video" | `nombre ILIKE '%Transcripción de video%'` |
| "señas", "lenguaje de señas" | `nombre ILIKE '%remota%Zoom%' AND idioma_destino = 'lenguaje_de_señas'` |
| "equipos", "receptores", "cabina" | Tabla `tarifas_alquiler_equipos` tipo `'receptores_simultanea'` |
| "equipos portátiles" | Tabla `tarifas_alquiler_equipos` tipo `'portatiles'` |
| "micrófono adicional" | Tabla `tarifas_alquiler_equipos` tipo `'microfono_inalambrico'` |
| "montaje nocturno", "montaje después de las 6" | Tabla `tarifas_alquiler_equipos` tipo `'montaje_nocturno'` |
| "montaje fin de semana", "montaje sábado" | Tabla `tarifas_alquiler_equipos` tipo `'montaje_fin_semana'` |
| "montaje día anterior" | Tabla `tarifas_alquiler_equipos` tipo `'montaje_dia_anterior'` |

## Idiomas disponibles en DB

`ingles`, `frances`, `portugues`, `italiano`, `aleman`, `lenguaje_de_señas`

## Recargos automáticos

Consultar siempre:
```sql
SELECT nombre, porcentaje, monto_fijo, condicion, es_automatico
FROM recargos WHERE activo = TRUE;
```

El recargo de 25% fuera de Bogotá (`es_automatico = TRUE`) se aplica automáticamente si `ubicacion` no es Bogotá. Los demás requieren evaluación caso por caso.

---

## Placeholders del template Word

Estos son los campos que el script reemplaza en `Formato_Cotizaciones_v2.docx`:

| Placeholder | Dato |
|-------------|------|
| `COT-___` | `COT-{numero}` |
| `DD de mes de AAAA` | Fecha en texto |
| `{nombre_contacto}` | Nombre completo |
| `{cargo}` | Cargo del contacto |
| `{empresa}` | Nombre de la empresa |
| `{email}` | Email |
| `{telefono}` | Teléfono |
| `{nombre_corto}` | Primer nombre |
| `{referencia_servicio}` | Descripción corta del servicio principal |
| `{presencial/virtual}` | "presencial" o "virtual" |
| `{ubicacion_evento}` | Ciudad y lugar |
| `{subtotal}` | Monto sin $ (el template ya tiene $) |
| `{iva}` | Monto o "EXENTO" |
| `{total}` | Monto |
| `{notas_servicio_1}` | Primera nota |
| `{notas_servicio_2}` | Segunda nota |
| `{notas_servicio_3}` | Tercera nota |
| `{validez_oferta}` | Texto de validez |
| `{forma_pago}` | Texto de forma de pago |

La tabla de servicios tiene 11 columnas: #, Servicio, Idioma Or., Idioma Dest., Fecha(s), Horario, Cant., Unidad, P. Unit., Total s/IVA, Notas/Detalle. Se llenan filas 2-6 (máximo 5 líneas).

## Archivos de la skill

```
cotizacion-skill/
├── SKILL.md                              ← Este archivo
├── scripts/
│   └── generar_cotizacion.py             ← Generador de Word/PDF
└── assets/
    └── Formato_Cotizaciones_v2.docx      ← Template con branding ML Traductores
```
