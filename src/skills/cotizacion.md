# Skill: Cotizacion

Estás en la fase **listo para cotizar**. El cliente está identificado en la base de datos.

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
3. **Confirmar al cliente brevemente** que su cotización está siendo preparada. NO des el total ni el desglose. Ejemplo: "Perfecto, ya tengo todos los datos. Estamos preparando su cotización formal."
4. **Enviar a revisión interna** → `enviar_cotizacion(cotizacion_id)`.
5. El sistema notifica al cliente automáticamente por WhatsApp que recibirá la cotización por correo. No necesitas hacer nada más en este paso.
6. **Confirma al cliente** el siguiente paso: "Su cotización quedó en revisión. En cuanto esté lista se la enviamos al correo {email}."

**NUNCA reveles el total exacto al cliente.** Puedes decir "estamos preparando su cotización" pero no el valor. El precio final llega por correo cuando María Luisa aprueba.

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
