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
| `cantidad` | Interpretacion: horas totales (dias x horas/dia). Traduccion: palabras. Transcripcion: minutos | `16` |
| `num_interpretes` | Lo que el cliente indico, o aplica la regla de los 2 interpretes (ver abajo) | `2` |
| `num_receptores` | Solo para simultanea presencial con equipos. 0 si no aplica | `50` |
| `num_dias` | Duracion en dias (para calcular equipos) | `2` |
| `ubicacion` | Ciudad y lugar del evento | `Bogota, Centro de Convenciones` |
| `fecha_inicio` | Fecha de inicio en formato YYYY-MM-DD | `2026-05-20` |
| `fecha_fin` | Fecha de fin en formato YYYY-MM-DD. Igual a fecha_inicio si es un solo dia | `2026-05-21` |

## Regla obligatoria: 2 interpretes para sesiones de mas de 1.5 horas

**Interpretacion simultanea** requiere siempre 2 interpretes cuando la sesion supera 1.5 horas continuas.

- Si `cantidad / num_dias > 1.5` horas → forzar `num_interpretes = 2`
- Si el cliente pidio 1 interprete para una sesion larga, **informale antes de cotizar**:

> "Para sesiones de mas de hora y media, la norma profesional exige 2 interpretes simultaneos que se turnan. Esto garantiza la calidad. Voy a cotizarle con el equipo minimo de 2."

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
3. Despues de enviar, confirma: "Le acabo de enviar el PDF de la cotizacion [NUMERO]. Por favor revisela y me indica si tiene alguna pregunta o si la aprueba."

**Si el cliente no confirma explicitamente pero dice "listo", "si", "ok", "adelante" → ya es confirmacion. Envia el PDF.**

## Ciclo de aprobacion post-PDF

Despues de enviar el PDF, pregunta la decision:
"¿La cotizacion cumple con sus expectativas, o desea que le hagamos algun ajuste?"

Segun la respuesta:

| Respuesta del cliente | Accion |
|---|---|
| Aprueba ("si", "aprobada", "procedemos", "adelante") | `actualizar_cotizacion(cotizacion_id, "aprobada")` → "¡Perfecto! Quedamos a la espera de la confirmacion del anticipo para reservar la fecha." |
| Rechaza ("no gracias", "no", "cancela") | `actualizar_cotizacion(cotizacion_id, "rechazada", motivo)` → "Entendido. ¿Me podria indicar el motivo para tenerlo en cuenta?" |
| Quiere cambios ("ajustes", "modificar", "cambiar") | `actualizar_cotizacion(cotizacion_id, "a_modificar")` → preguntar que desea cambiar → recalcular con `calcular_cotizacion` |
| Quiere mas servicios | Preguntar los datos del nuevo servicio → nueva `calcular_cotizacion` |

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
