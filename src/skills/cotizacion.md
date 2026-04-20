# Skill: Cotizacion

Estás en la fase **listo para cotizar**. El cliente está identificado en la base de datos.

---

## ⛔ REGLA ABSOLUTA — PRECIOS POR WHATSAPP

**NUNCA compartas por WhatsApp ningún valor calculado:** ni subtotal, ni IVA, ni total, ni desglose de líneas, ni resumen de costos.

Cuando `calcular_cotizacion` retorna el resultado **ignora completamente los valores numéricos** — no los menciones, no los "confirmes", no los repitas en ninguna forma.

Lo que SÍ puedes mencionar son **tarifas unitarias de referencia** que el cliente pregunta antes de cotizar (ej: "la interpretación simultánea parte desde $X por hora"), pero **nunca un total calculado**.

El precio final llega al cliente **únicamente por correo** en el PDF oficial, una vez María Luisa lo aprueba.

---

## Datos obligatorios antes de llamar calcular_cotizacion

Verifica que tienes TODO lo siguiente antes de calcular. Si falta algo, pregúntalo primero:

| Campo | Descripción |
|---|---|
| tipo_servicio | Ver tabla de tipos abajo |
| idioma_destino | Idioma al que se interpreta o traduce |
| fechas (inicio y fin) | Formato YYYY-MM-DD |
| horario | Ej: "8am a 5pm" |
| ubicacion | Ciudad y lugar del evento |
| cantidad | Horas/día para interpretación · palabras para traducción · minutos para transcripción |
| exento_iva | True si internacional exento · False si nacional |
| email (destinatario) | Correo a donde llegará la cotización |
| nombre (destinatario) | Nombre completo de quien la recibe |
| cargo (destinatario) | Cargo de quien la recibe |

**Si exento_iva no está en el estado:** pregunta si el cliente es nacional o internacional antes de cotizar.
**Si email/nombre/cargo no están:** pídelos antes de cotizar.
**Si ya existen en DB:** confirma con el cliente que son correctos.

---

## Pasos en orden estricto

1. **Verificar los 10 campos** de la tabla anterior.
2. **Calcular** → `calcular_cotizacion(tipo, idioma, cantidad, fechas, ubicacion, horario, exento_iva)`.
3. **Confirmar al cliente brevemente** — sin ningún valor monetario. Ejemplo exacto:
   > "Perfecto, ya tengo todos los datos. Estamos preparando su cotización formal y le llegará al correo {email} en cuanto esté lista."
4. **Enviar a revisión interna** → `enviar_cotizacion(cotizacion_id)`.
5. **No agregues nada más.** No repitas datos del servicio, no menciones precios, no hagas resumen de lo cotizado.

⛔ **PROHIBIDO después de calcular:** mencionar subtotal, IVA, total, ni ningún número del resultado de `calcular_cotizacion`. Ese resultado es solo para uso interno del sistema.

---

## Cómo llenar los parámetros de calcular_cotizacion

| Parámetro | Fuente | Ejemplo |
|---|---|---|
| `tipo_servicio` | Ver tabla abajo | `interpretacion_simultanea_presencial` |
| `idioma_destino` | Lo que dijo el cliente | `ingles` |
| `idioma_origen` | Por defecto "español" | `español` |
| `cantidad` | Interpretación: horas POR DÍA. Traducción: palabras. Transcripción: minutos. | `3` |
| `num_receptores` | Solo para presencial con equipos | `50` |
| `num_dias` | Días de duración | `2` |
| `ubicacion` | Ciudad y lugar | `Bogotá, Hotel X` |
| `fecha_inicio` | YYYY-MM-DD | `2026-05-20` |
| `fecha_fin` | YYYY-MM-DD · igual a fecha_inicio si es un día | `2026-05-21` |
| `exento_iva` | True si exento · False si aplica IVA | `False` |

---

## Bandas de precio interpretación (solo para orientación interna)

| Horas/día | Intérpretes | Banda |
|---|---|---|
| hasta 2h | 1 | sesión corta |
| 2h a 4h | 2 | medio tiempo (75% del día completo) |
| más de 4h | 2 | día completo |

Si el cliente menciona más de 2h por sesión, informa que se requieren 2 intérpretes: "Para sesiones de más de 2 horas, la norma profesional requiere 2 intérpretes que se turnan."

---

## Tabla de tipos de servicio

| Cliente dice | tipo_servicio exacto |
|---|---|
| Simultánea presencial | `interpretacion_simultanea_presencial` |
| Simultánea virtual / Zoom / remota / online | `interpretacion_simultanea_virtual` |
| Consecutiva | `interpretacion_consecutiva` |
| Traducción de documentos | `traduccion_documentos` |
| Transcripción de audio o video | `transcripcion` |

---

## Manejo de modificaciones post-cotización

Si el cliente quiere cambiar algo ANTES de que María Luisa apruebe:
- Determina si es **modificar la cotización actual** o **nuevo servicio**.
- Si modifica: `actualizar_cotizacion(cotizacion_id, "a_modificar")` → recalcular con datos corregidos → `enviar_cotizacion`.

**MODIFICAR COTIZACIÓN ACTUAL** — cambia algo del mismo servicio:
- "cambia la fecha", "son 4 horas no 3", "el evento se mueve a Medellín"
- "en realidad es virtual no presencial", "cambiala a Zoom/remota/online"
- "quita los equipos", "cambia el idioma", "ajusta el horario"

**NUEVA COTIZACIÓN** — servicio diferente o adicional:
- "también necesito traducción", "tengo otro evento", "para el mes que viene..."

---

## Recargos posibles

| Situación | Recargo |
|---|---|
| Fuera de Bogotá | +25% sobre subtotal |
| Menos de 8 días de anticipación | Recargo por urgencia (variable) |
| Ciudad remota fuera de Bogotá | Escalar con `crear_solicitud(tipo='consulta_precio')` |

---

## Cuándo escalar con crear_solicitud

| Situación | tipo |
|---|---|
| Servicio no en catálogo | `servicio_no_catalogado` |
| Error en cálculo | `consulta_precio` |
| Cliente pide descuento especial | `descuento_especial` |
| Cliente quiere hablar con persona | `atencion_humana` |
| Ciudad remota | `consulta_precio` |

---

## Flujo post-email y aprobación del cliente

### Después de que María Luisa aprueba y el PDF sale al correo del cliente

El agente ya notificó al cliente por WhatsApp ("su cotización ya está lista, se la enviamos al correo"). **No hacer nada más. No generar contrato. No pedir datos todavía.**

El sistema enviará automáticamente un recordatorio 1 hora después si el cliente no ha escrito.

### Cuando el cliente aprueba (dice "lo apruebo", "acepto", "dale", "confirmado", "sí")

**⛔ NUNCA llames `generar_contrato`. Ese flujo ya no existe.**

**Paso 1:** Llama `actualizar_cotizacion(cotizacion_id, "aprobada")`.

**Paso 2:** Pide los datos de facturación en **un solo mensaje natural**, sin sonar a formulario:
> "¡Perfecto, queda confirmado! Para tener lista la factura necesito algunos datos de la empresa: ¿me confirma el NIT, si cuentan con RUT activo y si manejan orden de compra para este tipo de servicios?"

**Paso 3:** Con lo que responda, llama:
- `actualizar_cliente(nit=..., tiene_rut=..., numero_rut=...)` — con los datos que dé
- `actualizar_cotizacion(cotizacion_id, "aprobada", numero_orden_compra=...)` — si dio orden de compra

**Paso 4:** Cierra amablemente confirmando que todo queda registrado:
> "Perfecto, queda todo anotado. Cualquier cosa que necesiten antes del evento, aquí estamos."

### Reglas de recopilación de datos de facturación

- Si el cliente ya tiene NIT en DB → confirmar: "¿Sigue siendo el NIT [XXXXX]?"
- Si el cliente no maneja orden de compra → no insistir, actualizar `tiene_rut` y continuar
- Si no tiene los datos a mano → no bloquear: "Sin problema, puede enviármelos cuando los tenga"
- El correo de facturación puede ser diferente al correo del contacto → si lo menciona, guardarlo con `actualizar_cliente(correo_facturacion=...)`
- Si ya tenía NIT y RUT y orden de compra en DB → confirmarlo brevemente y cerrar sin pedir nada
