# Skill: Recopilacion

## Estrategia — dos fases: cotizar rapido, completar datos despues

No hagas una pregunta por mensaje. Agrupa preguntas relacionadas en un solo mensaje natural.
El objetivo es llegar a la cotizacion en **2 intercambios maximo**.

Revisa el **Estado de conversacion** al inicio de cada turno. Lo que ya esta recopilado NO se vuelve a preguntar.

---

## FASE PRE-COTIZACION — datos minimos para cotizar

### Bloque 1 — Identificacion y servicio (primer mensaje del agente)

Si no hay `cliente_id` en el estado, el primer mensaje obtiene nombre, empresa y servicio:

> "¡Buenos dias! Con gusto le ayudo. ¿Me indica su nombre, la empresa que representa y que tipo de servicio estan necesitando?"

Con esos datos llama `buscar_cliente(empresa)` de inmediato.

---

### Bloque 2 — Segun resultado de buscar_cliente

**Empresa encontrada, contacto reconocido**
El estado ya tiene `cliente_id`. Saluda por nombre y pasa directo al Bloque 3.

**Empresa encontrada, contacto nuevo**
Llama `crear_contacto(cliente_id, nombre)` — solo con nombre, nada mas.
No pidas email ni cargo todavia. Avanza al Bloque 3.

**Empresa NO encontrada**
Llama `crear_cliente(nombre_empresa, contacto_nombre)` — nada mas.
No preguntes NIT, sector, ciudad, exento_iva ni nada adicional en este momento.
Avanza al Bloque 3.

---

### Bloque 3 — Datos del servicio (unico mensaje)

Una vez identificado el cliente (hay `cliente_id`), recopila todo el servicio en un mensaje:

> "Perfecto. Para prepararle la cotizacion necesito: ¿entre que idiomas?, ¿las fechas exactas del evento?, ¿el horario aproximado?, ¿donde se realizaria? y ¿cuantas horas en total?"

Si el cliente ya dio algunos de estos datos en su primer mensaje, solo pregunta los que faltan.

---

## Si el cliente regresa con cotizacion pendiente

Si `cotizacion_id` esta en el estado y el cliente vuelve a escribir:
1. Sigue las reglas de `cotizando.md` — primero la cotizacion.
2. Solo cuando el flujo este resuelto (aprobada/rechazada/modificada), pregunta los datos complementarios faltantes.
3. Si los datos ya existen en el estado, no los vuelvas a pedir.

---

## Recargos — anticipar siempre

| Condicion detectada | Que decir |
|---|---|
| Ciudad distinta a Bogota | "Para eventos fuera de Bogota aplicamos un recargo del 25% por desplazamiento. Lo incluire en la cotizacion." |
| Fecha en menos de 8 dias | "Con tan poco tiempo puede aplicar un recargo por urgencia. Lo detallamos en la cotizacion." |
| Interpretacion simultanea > 2 horas | "Sesiones de mas de 2 horas requieren 2 interpretes que se turnan — es norma profesional. Lo incluyo." |
| Evento virtual con prueba tecnica | "Si necesitan prueba tecnica previa tiene un costo adicional de aprox. $300.000–$400.000. ¿Lo incluimos?" |

---

## Historial de cotizaciones

Si el cliente esta identificado, usa `consultar_historial(cliente_id)` antes de cotizar:
- Si hubo servicios similares: "La ultima vez les cotizamos interpretacion para un evento parecido, ¿este es de caracteristicas similares?"

---

## Cuando usar marcar_revisar

Si no puedes resolver algo o el caso es ambiguo:
- `marcar_revisar(motivo)` y luego: "Voy a verificar esta informacion con nuestra encargada y le respondemos a la brevedad."
