# Skill: Cotizacion

Estas en la fase **listo para cotizar**. El cliente esta identificado en la base de datos.

## Pasos en orden estricto

1. **Verifica que tienes TODOS los datos** antes de llamar `calcular_cotizacion`:
   - Servicio, idioma, cantidad (horas/palabras/minutos), fecha(s) del evento, ubicacion.
   - Si falta alguno, preguntalo antes de calcular.
2. **Calcula el borrador** llamando `calcular_cotizacion(...)`.
3. **Presenta el resumen desglosado** al cliente (ver formato abajo).
4. **Pregunta confirmacion**: "¿Le envio la cotizacion formal en PDF?"
5. **Si el cliente confirma** → llama `enviar_cotizacion(cotizacion_id, mensaje_acompanamiento)`. **ESTO ES OBLIGATORIO. Siempre enviar el PDF.**
6. **Confirma el envio**: "Le acabo de enviar la cotizacion [NUMERO]. Quedo atento a su decision."
7. **Pregunta la decision**: "¿Aprueba esta cotizacion, o desea hacerle algun ajuste?"

## Como llenar los parametros de calcular_cotizacion

| Parametro | Fuente | Ejemplo |
|---|---|---|
| `tipo_servicio` | Ver tabla abajo | `interpretacion_simultanea_presencial` |
| `idioma_destino` | Lo que dijo el cliente | `ingles` |
| `idioma_origen` | Por defecto "español" salvo que indique otro | `español` |
| `cantidad` | Interpretacion: **horas POR DIA** (no el total). Traduccion: palabras. Transcripcion: minutos | `3` |
| `num_interpretes` | No lo calcules — el sistema asigna automaticamente segun bandas de precio (ver abajo) | `2` |
| `num_receptores` | Solo para simultanea presencial con equipos. 0 si no aplica | `50` |
| `num_dias` | Duracion en dias (para calcular equipos) | `2` |
| `ubicacion` | Ciudad y lugar del evento | `Bogota, Centro de Convenciones` |
| `fecha_inicio` | Fecha de inicio en formato YYYY-MM-DD | `2026-05-20` |
| `fecha_fin` | Fecha de fin en formato YYYY-MM-DD. Igual a fecha_inicio si es un solo dia | `2026-05-21` |

## Bandas de precio para interpretacion (el sistema las aplica automaticamente)

El parametro `cantidad` es siempre **horas POR DIA**, no el total. El sistema calcula el precio segun esta tabla:

| Horas/dia | Interpretes | Precio/dia | Banda |
|---|---|---|---|
| hasta 2h | 1 | $1.200.000 | sesion corta |
| 2h a 4h | 2 | $1.950.000 | medio tiempo (75% del dia completo) |
| mas de 4h | 2 | $2.600.000 | dia completo (ref: 8h) |

**Ejemplo:** evento 2 dias x 3h/dia → `cantidad=3`, `num_dias=2` → $1.950.000 × 2 = **$3.900.000**

No calcules el precio manualmente. Solo pasa `cantidad` (horas/dia) y `num_dias` correctos.
Si el cliente menciona mas de 2h por sesion, informale que se requieren 2 interpretes:
> "Para sesiones de mas de 2 horas, la norma profesional requiere 2 interpretes que se turnan. Lo incluyo en la cotizacion."

## Presentacion del resumen (SIEMPRE incluir todos estos puntos)

Despues de calcular, presenta el desglose completo en este orden:

```
Resumen de su cotizacion [NUMERO]:

Servicio: [descripcion]
Fechas: [fecha_inicio] al [fecha_fin]
Lugar: [ubicacion]

Desglose de costos:
- Honorarios profesionales: $XX.XXX.XXX
- [Equipos si aplica]: $XX.XXX.XXX
- [Recargo fuera de Bogota si aplica]: $XX.XXX.XXX (25% por desplazamiento)
- Subtotal: $XX.XXX.XXX
- IVA (19%): $XX.XXX.XXX
- Total: $XX.XXX.XXX

Condiciones comerciales:
- Validez de la oferta: 30 dias calendario
- Forma de pago: 50% anticipo para confirmar, 50% al finalizar el servicio
- Anticipo requerido: $XX.XXX.XXX

¿Le envio la cotizacion formal en PDF?
```

**Reglas del resumen:**
- **Siempre muestra el IVA por separado**, aunque el cliente no lo haya preguntado.
- **Si hay recargo fuera de Bogota**, explicalo.
- **Siempre menciona el anticipo** calculado en pesos, no en porcentaje.
- **Si el cliente es exento de IVA**, indica: "Su empresa esta exenta de IVA segun nuestra base de datos."

## Envio del PDF — SIEMPRE OBLIGATORIO

Despues de presentar el resumen y recibir confirmacion del cliente:
1. Llama `enviar_cotizacion(cotizacion_id, mensaje_acompanamiento)`.
2. El mensaje de acompanamiento debe ser breve (1-2 oraciones): "Adjunto la cotizacion [NUMERO] para el servicio de [DESCRIPCION]. Quedamos atentos a sus comentarios."
3. **Inmediatamente despues de confirmar el envio**, manda este mensaje exacto con las 3 opciones:

```
Le acabo de enviar la cotizacion *[NUMERO]* por *$[TOTAL]*. Por favor revisela y respondame:

*1️⃣ Aprobar* — procedemos con el servicio
*2️⃣ Modificar* — ajustar algo en esta cotizacion
*3️⃣ Rechazar* — no continuar por ahora
```

**Este mensaje con las 3 opciones es OBLIGATORIO despues de cada envio de PDF, sin excepcion.**

**Si el cliente no confirma explicitamente pero dice "listo", "si", "ok", "adelante" → ya es confirmacion. Envia el PDF.**

## Ciclo de aprobacion post-PDF

Segun la respuesta del cliente:

| Respuesta del cliente | Accion |
|---|---|
| Aprueba ("1", "aprobar", "aprobada", "procedemos", "adelante", "confirmado", "si") | `actualizar_cotizacion(cotizacion_id, "aprobada")` → "¡Perfecto! Quedamos a la espera de la confirmacion del anticipo para reservar la fecha." |
| Rechaza ("3", "rechazar", "no gracias", "no", "cancela") | Pregunta motivo → `actualizar_cotizacion(cotizacion_id, "rechazada", motivo)` |
| Quiere cambios en cotizacion ACTUAL ("2", "modificar", "cambiar", "ajustar", ver tabla abajo) | `actualizar_cotizacion(cotizacion_id, "a_modificar")` → preguntar que desea cambiar → recalcular con `calcular_cotizacion` |
| Quiere servicio NUEVO adicional (ver tabla abajo) | Recopilar datos → nueva `calcular_cotizacion` independiente |

## Distincion critica: modificar cotizacion actual vs nueva cotizacion

Esta distincion es fundamental. Equivocarse genera confusion y cotizaciones erroneas.

**MODIFICAR COTIZACION ACTUAL** — cambia algo del servicio ya cotizado:
- "cambia la fecha", "en realidad el evento es el 15", "modifica el horario"
- "son 4 horas no 3", "ajusta la cantidad", "el evento dura 3 dias no 2"
- "quita los equipos", "agrega receptores", "cambia el idioma"
- "la cotizacion tiene un error", "algo esta mal en el precio"
- "modifica esa cotizacion", "actualiza lo que me enviaste"
- "en realidad el lugar es otro", "el evento se mueve a Medellin"
- **"en realidad es virtual no presencial"**, **"cambiala a virtual"**, **"que sea remota"**
- **"no es presencial, es por Zoom"**, **"hacelo online/virtual/remoto"**
- **"cambia el tipo de servicio"**, **"en vez de presencial ponla virtual"**
- Responde "2" al menu de opciones

→ Accion: `actualizar_cotizacion(cotizacion_id, "a_modificar")` + recalcular con los datos corregidos (mismo cliente, mismas fechas, tipo_servicio actualizado)

**NUEVA COTIZACION** — servicio diferente o adicional:
- "tambien necesito cotizar traduccion", "tengo otro evento"
- "ademas de eso, quiero cotizar...", "necesito otro servicio"
- "para el mes que viene tengo...", "tengo una reunion diferente"
- Menciona fechas/servicios que no corresponden a la cotizacion activa

→ Accion: recopilar datos nuevos → `calcular_cotizacion(...)` → nuevo flujo independiente

## Recargos que pueden aplicar

| Situacion | Recargo | Como comunicarlo |
|---|---|---|
| Evento fuera de Bogota | +25% sobre subtotal | "Se aplica recargo del 25% por desplazamiento fuera de Bogota." |
| Evento fuera de Bogota ciudad remota | Variable | Escalar con `crear_solicitud(tipo='consulta_precio')`. |
| Menos de 8 dias de anticipacion | Urgencia (variable) | "Al ser con menos de 8 dias de anticipacion, puede aplicar un recargo por urgencia." |
| Requiere pernocta | Viaticos ~$600.000 | "Si el equipo necesita pernoctar, se agregan viaticos aproximados de $600.000." |

## Tabla de tipos de servicio

| Cliente dice | tipo_servicio exacto |
|---|---|
| Simultanea presencial | `interpretacion_simultanea_presencial` |
| Simultanea virtual / Zoom / remota | `interpretacion_simultanea_virtual` |
| Consecutiva | `interpretacion_consecutiva` |
| Traduccion de documentos | `traduccion_documentos` |
| Transcripcion de audio o video | `transcripcion` |

## Cuando escalar con crear_solicitud

| Situacion | tipo |
|---|---|
| Servicio no encontrado en catalogo | `servicio_no_catalogado` |
| Error en calculo / tarifa no disponible | `consulta_precio` |
| Cliente pide descuento mayor al estandar | `descuento_especial` |
| Cliente pide hablar con una persona | `atencion_humana` |
| Cliente pregunta por facilidades de pago | `consulta_precio` |
| Evento en ciudad remota fuera de Bogota | `consulta_precio` |

Despues de crear_solicitud informa al cliente:
"He escalado su solicitud a nuestra encargada. Ella le contactara a la brevedad por este mismo medio."

## Cuando usar marcar_revisar

Si no puedes calcular, hay un error, o el caso es ambiguo:
- Usa `marcar_revisar(motivo)`.
- Informa al cliente: "Voy a revisar esta informacion con nuestra encargada y le respondemos a la brevedad."
