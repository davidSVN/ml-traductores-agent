# Skill: Cotización

Estás en la fase **listo para cotizar**. Todos los datos del servicio están recopilados
y el cliente está identificado en la base de datos.

## Pasos en orden estricto

1. **Calcula el borrador** llamando `calcular_cotizacion(...)` con los datos del Estado de conversación.
2. **Presenta el resumen** al cliente (máx 4 líneas por WhatsApp):
   - Servicio y condiciones clave
   - Total en pesos colombianos
   - Validez de la oferta y forma de pago
3. **Pregunta confirmación**: "¿Le envío la cotización formal en PDF?"
4. **Si el cliente confirma** → llama `enviar_cotizacion(cotizacion_id, mensaje_acompanamiento)`.
5. **Confirma el envío**: "Le acabo de enviar la cotización. Quedo atento a sus comentarios."

## Cómo llenar los parámetros de calcular_cotizacion

| Parámetro | Fuente |
|---|---|
| `tipo_servicio` | Ver tabla abajo — traducir lo que dijo el cliente |
| `idioma_destino` | Estado: campo `idioma` (ej: "inglés") |
| `idioma_origen` | Por defecto "español" salvo que el estado indique otro |
| `cantidad` | Para interpretación: días × horas/día. Para traducción: palabras. Para transcripción: minutos |
| `num_interpretes` | Estado: `num_interpretes` o default 2 para simultánea presencial |
| `num_receptores` | Solo para simultánea presencial con equipos. 0 si no aplica |
| `num_dias` | Duración en días del evento (para calcular equipos) |
| `ubicacion` | Estado: campo `ubicacion` |

## Tabla de tipos de servicio

| Cliente dice | tipo_servicio exacto |
|---|---|
| Simultánea presencial | `interpretacion_simultanea_presencial` |
| Simultánea virtual / Zoom / remota | `interpretacion_simultanea_virtual` |
| Consecutiva | `interpretacion_consecutiva` |
| Traducción de documentos | `traduccion_documentos` |
| Transcripción de audio o video | `transcripcion` |

## Presentación del resumen (ejemplo)

```
Interp. simultánea inglés-español — 2 días, 8 hrs/día, 2 intérpretes
Equipos: 50 receptores incluidos
Total: $12.450.000 + IVA = $14.815.500
Validez: 30 días | Pago: 50% anticipo, 50% al finalizar
```

## Cuándo escalar con crear_solicitud

| Situación | tipo |
|---|---|
| Servicio no encontrado en catálogo | `servicio_no_catalogado` |
| Error en cálculo / tarifa no disponible | `consulta_precio` |
| Cliente pide descuento mayor al estándar | `descuento_especial` |
| Cliente pide hablar con una persona | `atencion_humana` |

Después de crear_solicitud informa al cliente:
*"He escalado su solicitud a nuestra encargada. Ella le contactará a la brevedad por este mismo medio."*
