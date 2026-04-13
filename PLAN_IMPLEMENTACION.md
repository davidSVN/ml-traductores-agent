# Plan de Implementación — Agente Comercial ML Traductores

## 1. Estado Actual

### Lo que YA existe
| Recurso | Estado | Notas |
|---------|--------|-------|
| WhatsApp Business API | ✅ Configurada | Meta Cloud API funcionando |
| AWS RDS PostgreSQL | ✅ Con datos reales | Tablas de clientes, precios, servicios, cotizaciones |
| API key Anthropic | ✅ Activa | Claude como motor principal |
| Plantilla .docx cotización | ✅ Disponible | Formato_Cotizaciones_v2.docx — tabla de servicios, totales, IVA, firma |
| Skill: agente-comercial | ✅ Definida | Fases 1-6 del ciclo comercial, personalidad, SQL, escalamiento |
| Skill: cotizacion-generator | ❌ No existe | Referenciada en agente-comercial pero no creada |
| LangSmith (observabilidad) | ❌ Por configurar | Cuenta necesaria en smith.langchain.com |

### Lo que FALTA construir
| Componente | Prioridad |
|------------|-----------|
| Backend API (FastAPI) | P0 |
| Capa de abstracción de IA (LLM Router) | P0 |
| Motor de conversación (orquestador de skills/tools) | P0 |
| Generador de cotizaciones Word→PDF | P0 |
| Webhook WhatsApp (recibir/enviar mensajes) | P0 |
| LangSmith: tracing de todas las llamadas al LLM | P0 |
| Dashboard de conversaciones en vivo | P1 |
| Dashboard de historial de cotizaciones | P1 |
| Sistema de seguimiento automático (cron/scheduler) | P2 |
| Infraestructura AWS (ECS o Lambda) | P1 |

---

## 2. Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────┐
│                    CLIENTE (WhatsApp)                    │
└────────────────────────┬────────────────────────────────┘
                         │ Meta Cloud API (webhook)
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  BACKEND (FastAPI)                       │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │  WhatsApp     │  │  Orquestador │  │  Dashboard    │ │
│  │  Webhook      │──│  de Agente   │  │  API (REST)   │ │
│  │  Controller   │  │              │  │               │ │
│  └──────────────┘  └──────┬───────┘  └───────────────┘ │
│                           │                             │
│           ┌───────────────┼───────────────┐             │
│           ▼               ▼               ▼             │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │  LLM Router  │  │  Tool        │  │  Doc          │ │
│  │  (Anthropic/  │  │  Executor    │  │  Generator    │ │
│  │   OpenAI/etc) │  │              │  │  (docx→pdf)   │ │
│  └───────┬──────┘  └──────┬───────┘  └───────┬───────┘ │
│          │                │                  │          │
│          ▼                ▼                  ▼          │
│  ┌──────────────┐  ┌──────────────┐   ┌──────────────┐ │
│  │  LangSmith   │  │  PostgreSQL  │   │  S3 Bucket   │ │
│  │  (tracing)   │  │  (AWS RDS)   │   │  (PDFs)      │ │
│  └──────────────┘  └──────────────┘   └──────────────┘ │
└─────────────────────────────────────────────────────────┘
         │                   │
         ▼    ┌──────────────┼──────────────┐
┌──────────────────┐                       │
│  smith.langchain │          ▼             ▼
│  .com (David)    │ ┌──────────────┐ ┌──────────────┐
│  Ve: trazas,     │ │  Dashboard   │ │  Dashboard   │
│  tokens, costos, │ │  Conversac.  │ │  Cotizaciones│
│  latencia, tools │ │  (Next.js)   │ │  (Next.js)   │
└──────────────────┘ └──────────────┘ └──────────────┘
```

**Quién ve qué:**
- **David (tú):** LangSmith → trazas completas de cada llamada al LLM, tokens usados, tools invocadas, latencia, errores.
- **María Luisa:** Dashboards Next.js → conversaciones en vivo, historial de cotizaciones, estados.
```

---

## 3. Diferencia Crítica: Skills vs Tools

Esto es clave para controlar costos de tokens y cómputo.

### Skills = Prompts de sistema (consumen tokens)
- Son instrucciones en texto que se inyectan en el prompt del LLM.
- Se envían en CADA llamada al modelo donde apliquen.
- **Costo:** Tokens de entrada. A más texto en la skill, más tokens por llamada.
- **Dónde viven:** En archivos `.md` o `.txt` que el orquestador carga dinámicamente.
- **Regla:** Solo cargar la skill que aplica para la fase actual. NUNCA cargar todas las skills en cada llamada.

### Tools = Funciones Python (consumen cómputo, NO tokens extra)
- Son funciones que el LLM puede invocar mediante tool_use/function_calling.
- El LLM solo recibe la **definición** de la tool (nombre, parámetros, descripción).
- La **ejecución** ocurre en tu servidor Python — no en el LLM.
- **Costo:** Tokens mínimos (solo la definición ~50-100 tokens por tool) + cómputo de servidor.
- **Dónde viven:** En módulos Python dentro del backend.

### Tabla de decisión

| Componente | Tipo | Razón | Costo principal |
|------------|------|-------|-----------------|
| Personalidad del agente | Skill | Es texto que define cómo habla el LLM | Tokens (inyectar solo al inicio) |
| Reglas de recopilación de datos | Skill | El LLM necesita saber qué preguntar | Tokens (cargar en fases 1-2) |
| Manejo de objeciones | Skill | El LLM necesita saber cómo responder | Tokens (cargar solo en fase 5) |
| Buscar cliente en DB | Tool | Es una query SQL ejecutada en Python | Cómputo (casi nulo) |
| Consultar historial cotizaciones | Tool | Es una query SQL | Cómputo (casi nulo) |
| Consultar tarifas/precios | Tool | Es una query SQL + lógica de pricing | Cómputo (casi nulo) |
| Calcular cotización | Tool | Es matemática pura en Python | Cómputo (casi nulo) |
| Generar Word/PDF | Tool | Es generación de archivo en servidor | Cómputo (moderado) |
| Enviar PDF por WhatsApp | Tool | Es una llamada HTTP a Meta API | Cómputo (casi nulo) |
| Registrar cotización en DB | Tool | Es un INSERT SQL | Cómputo (casi nulo) |
| Crear seguimiento | Tool | Es un INSERT SQL | Cómputo (casi nulo) |
| Escalar a María Luisa | Tool | Es un INSERT en solicitudes_agente | Cómputo (casi nulo) |
| Enviar mensaje WhatsApp | Tool | Es una llamada HTTP a Meta API | Cómputo (casi nulo) |

### Regla de oro para ahorrar tokens

```
FASE 1-2 → Cargar: skill_personalidad + skill_recopilacion + tools [buscar_cliente, historial]
FASE 3   → Cargar: skill_cotizacion_minima + tools [consultar_tarifas, calcular, generar_pdf, enviar_whatsapp]
FASE 4   → Cargar: skill_presentacion + tools [enviar_whatsapp, registrar_seguimiento]
FASE 5   → Cargar: skill_objeciones + tools [escalar, registrar_seguimiento]
FASE 6   → Cargar: skill_cierre + tools [registrar_aprobacion, crear_orden, notificar_ml]
```

**Nunca cargar todo junto.** El orquestador determina la fase y carga solo lo necesario.

---

## 4. Observabilidad con LangSmith

### Qué es y para qué lo usamos

LangSmith es la plataforma de observabilidad de LangChain. Te permite ver, en smith.langchain.com, cada interacción que el agente tiene con el LLM: qué prompt se envió, qué respondió, qué tools se invocaron, cuántos tokens consumió, cuánto tardó, y si hubo errores.

**No es un componente que el usuario final ve.** Es tu herramienta de desarrollo y monitoreo.

### Qué vas a poder ver en LangSmith

| Dato | Para qué sirve |
|------|----------------|
| Traza completa de cada conversación | Ver el flujo: mensaje → skill cargada → tools invocadas → respuesta |
| Tokens de entrada y salida por llamada | Controlar costos, detectar skills que consumen demasiado |
| Latencia por llamada | Detectar si alguna tool o el LLM están lentos |
| Tool calls (nombre, parámetros, resultado) | Verificar que las tools se invocaron correctamente |
| Errores y excepciones | Debug rápido cuando algo falla |
| Historial por conversación | Reconstruir una conversación completa con todos sus detalles técnicos |

### Requisitos para implementar LangSmith

**Cuenta y API key:**
1. Crear cuenta en https://smith.langchain.com (gratis).
2. Generar una API key desde el dashboard de LangSmith.
3. Agregar las variables de entorno al proyecto.

**Plan recomendado:** Developer (gratis). Incluye 1 seat y 5,000 trazas/mes con retención de 14 días. Para el volumen de ML Traductores (~100-200 cotizaciones/mes, ~600-2,000 trazas/mes) es más que suficiente. Si necesitas más: Plus a $39/mes con 10,000 trazas incluidas.

**Variables de entorno necesarias:**

```
LANGSMITH_API_KEY=lsv2_pt_xxxxx          # API key de LangSmith
LANGSMITH_TRACING=true                    # Activar tracing
LANGSMITH_PROJECT=ml-traductores-agent    # Nombre del proyecto en LangSmith
LANGSMITH_ENDPOINT=https://api.smith.langchain.com  # (default)
```

### Dependencias Python

```
langchain-anthropic>=0.3.21    # Wrapper de Claude con tracing automático
langsmith>=0.1.0               # SDK de LangSmith
```

### Cómo se integra en el código

La integración es **en el LLM Router**, no en cada tool ni en cada skill. Esto es clave: solo instrumentas la capa que habla con el LLM.

**Archivo afectado:** `src/llm/anthropic_provider.py`

```python
# En lugar de usar anthropic directamente:
# from anthropic import Anthropic
# client = Anthropic()

# Usamos el wrapper de LangChain que tiene tracing automático:
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(
    model="claude-sonnet-4-20250514",
    temperature=0.3,
    max_tokens=1024,
)
# Cada llamada a llm.invoke() se traza automáticamente en LangSmith.
# No necesitas código adicional. Solo tener las env vars configuradas.
```

**Importante sobre consumo:** LangSmith NO consume tokens extra. Solo envía los metadatos de la llamada (prompt, respuesta, tiempos) a sus servidores vía HTTP después de cada llamada al LLM. El overhead es mínimo (~5-10ms por traza).

### Qué se traza y qué NO se traza

| Componente | ¿Se traza en LangSmith? | Razón |
|------------|------------------------|-------|
| Llamadas al LLM (Claude) | ✅ Sí, automático | Es el punto central de observabilidad |
| Tool definitions enviadas al LLM | ✅ Sí, incluido en la traza | Son parte del prompt |
| Ejecución de tools (Python) | ❌ No automático | Son funciones locales, no pasan por LangSmith |
| Resultado de tools devuelto al LLM | ✅ Sí, si usas el ciclo tool_use | El resultado se envía como mensaje |
| Queries SQL a PostgreSQL | ❌ No | Son ejecución local, no son llamadas al LLM |
| Generación de Word/PDF | ❌ No | Es cómputo local |
| Envío de WhatsApp | ❌ No | Es una llamada HTTP a Meta, no al LLM |
| Skills cargadas (prompt de sistema) | ✅ Sí, dentro de la traza | Son el system prompt |

### Tracing personalizado opcional (fase avanzada)

Si en el futuro quieres trazar también las tools y el flujo completo, puedes agregar decoradores:

```python
from langsmith import traceable

@traceable(name="buscar_cliente")
def buscar_cliente(empresa: str):
    # tu query SQL
    pass
```

Esto es opcional y solo si necesitas debug profundo. No es necesario en la Fase 0.

### Dónde viven los archivos de LangSmith en el repo

No hay un directorio dedicado. LangSmith se configura en 3 puntos:

| Archivo | Qué se configura |
|---------|-----------------|
| `.env.example` | Variables `LANGSMITH_*` |
| `src/llm/anthropic_provider.py` | Usar `ChatAnthropic` de langchain-anthropic |
| `pyproject.toml` | Dependencias `langchain-anthropic`, `langsmith` |

### Decisión arquitectónica: ¿LangChain completo o solo LangSmith?

**Solo LangSmith + langchain-anthropic.** No usamos LangChain completo (chains, agents, memory de LangChain). Razones:

1. LangChain completo agrega complejidad innecesaria — ya tenemos nuestro propio orquestador.
2. Solo necesitamos el wrapper `ChatAnthropic` que envía trazas automáticamente.
3. Si en el futuro cambias a OpenAI, usarás `langchain-openai` con `ChatOpenAI` — misma interfaz, mismo tracing.
4. Esto mantiene la capa de abstracción limpia y el proyecto ligero.

**Dependencias mínimas (NO instalar langchain completo):**
```
langchain-core          # Tipos base (mensajes, tools)
langchain-anthropic     # Wrapper de Claude con tracing
langsmith               # SDK de observabilidad
```

---

## 5. Estructura del Repositorio

```
ml-traductores-agent/
│
├── README.md
├── .env.example                    # Variables de entorno (nunca commitear .env)
├── .gitignore
├── docker-compose.yml              # Para desarrollo local
├── Dockerfile
├── pyproject.toml                  # Dependencias Python
│
├── alembic/                        # Migraciones de DB
│   ├── alembic.ini
│   └── versions/
│
├── src/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app entry point
│   ├── config.py                   # Settings, env vars
│   │
│   ├── api/                        # Endpoints HTTP
│   │   ├── __init__.py
│   │   ├── webhooks.py             # POST /webhook/whatsapp (recibe mensajes Meta)
│   │   ├── conversations.py        # GET /conversations (dashboard conversaciones)
│   │   └── quotes.py               # GET /quotes (dashboard cotizaciones)
│   │
│   ├── agent/                      # Núcleo del agente
│   │   ├── __init__.py
│   │   ├── orchestrator.py         # Determina fase, carga skills/tools, llama al LLM
│   │   ├── phase_detector.py       # Clasifica en qué fase está la conversación
│   │   └── conversation.py         # Gestión de estado de conversación
│   │
│   ├── llm/                        # Capa de abstracción de modelos IA
│   │   ├── __init__.py
│   │   ├── router.py               # Interface común: send_message(messages, tools, skill)
│   │   ├── anthropic_provider.py   # Implementación para Claude
│   │   ├── openai_provider.py      # Implementación para GPT (futuro)
│   │   └── schemas.py              # Tipos compartidos: Message, ToolCall, Response
│   │
│   ├── skills/                     # Prompts de sistema (archivos .md)
│   │   ├── personalidad.md         # Tono, reglas de comunicación (~300 tokens)
│   │   ├── recopilacion.md         # Qué datos pedir, cómo preguntar (~400 tokens)
│   │   ├── cualificacion.md        # Evaluación interna del cliente (~200 tokens)
│   │   ├── cotizacion.md           # Instrucciones mínimas para fase 3 (~200 tokens)
│   │   ├── presentacion.md         # Cómo presentar la cotización (~150 tokens)
│   │   ├── objeciones.md           # Manejo de "muy caro", "déjeme pensarlo" (~400 tokens)
│   │   ├── cierre.md               # Detección de aprobación, orden de servicio (~300 tokens)
│   │   ├── seguimiento.md          # Cadencia de seguimiento (~200 tokens)
│   │   └── propuesta_valor.md      # Diferenciadores (solo cuando aplica) (~150 tokens)
│   │
│   ├── tools/                      # Funciones Python invocables por el LLM
│   │   ├── __init__.py
│   │   ├── registry.py             # Registro central: mapea nombre → función + definición
│   │   ├── db_cliente.py           # buscar_cliente, crear_cliente
│   │   ├── db_cotizacion.py        # consultar_historial, registrar_cotizacion, actualizar_estado
│   │   ├── db_tarifas.py           # consultar_tarifas, calcular_precio
│   │   ├── db_seguimiento.py       # crear_seguimiento, listar_seguimientos
│   │   ├── db_ordenes.py           # crear_orden_servicio
│   │   ├── db_solicitudes.py       # escalar_a_ml (crear solicitud para María Luisa)
│   │   ├── doc_generator.py        # generar_cotizacion_docx, convertir_a_pdf
│   │   └── whatsapp_sender.py      # enviar_mensaje, enviar_pdf, enviar_template
│   │
│   ├── templates/                  # Plantillas de documentos
│   │   └── cotizacion_v2.docx      # Plantilla base de ML Traductores
│   │
│   ├── db/                         # Base de datos
│   │   ├── __init__.py
│   │   ├── engine.py               # SQLAlchemy engine + session
│   │   ├── models.py               # ORM models (clientes, cotizaciones, etc.)
│   │   └── queries.py              # Queries reutilizables
│   │
│   ├── whatsapp/                   # Integración con Meta API
│   │   ├── __init__.py
│   │   ├── client.py               # Clase WhatsAppClient (enviar mensajes, media)
│   │   ├── webhook_handler.py      # Parsear eventos de webhook entrantes
│   │   └── media.py                # Upload/download de archivos media
│   │
│   └── storage/                    # Almacenamiento de archivos
│       ├── __init__.py
│       └── s3.py                   # Upload/download de PDFs a S3
│
├── frontend/                       # Dashboard Next.js
│   ├── package.json
│   ├── next.config.js
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx                    # Home → redirige a /conversations
│   │   │   ├── conversations/
│   │   │   │   ├── page.tsx                # Lista de conversaciones activas
│   │   │   │   └── [id]/page.tsx           # Detalle de conversación en vivo
│   │   │   └── quotes/
│   │   │       ├── page.tsx                # Historial de cotizaciones
│   │   │       └── [id]/page.tsx           # Detalle de cotización
│   │   ├── components/
│   │   │   ├── ChatWindow.tsx              # Ventana de chat en vivo
│   │   │   ├── ConversationList.tsx        # Lista lateral
│   │   │   ├── QuoteTable.tsx              # Tabla de cotizaciones
│   │   │   ├── QuoteDetail.tsx             # Detalle con PDF preview
│   │   │   └── StatusBadge.tsx             # Badge de estado
│   │   └── lib/
│   │       ├── api.ts                      # Fetch wrapper para backend
│   │       └── websocket.ts                # WS para conversaciones en vivo
│   └── tailwind.config.js
│
└── tests/
    ├── test_orchestrator.py
    ├── test_tools.py
    ├── test_doc_generator.py
    └── test_whatsapp.py
```

---

## 6. Fases de Implementación

### Fase 0 — Cimientos (Semana 1)
**Objetivo:** Proyecto funcional de extremo a extremo con un flujo mínimo.

| Paso | Qué hacer | Archivos |
|------|-----------|----------|
| 0.1 | Inicializar repo, pyproject.toml, .env.example, docker-compose (FastAPI + PostgreSQL local) | raíz |
| 0.2 | Configurar SQLAlchemy + Alembic. Copiar tus models existentes a `src/db/models.py`. Correr primera migración. | `src/db/`, `alembic/` |
| 0.3 | Crear `src/llm/router.py` con interface abstracta y `anthropic_provider.py` usando `ChatAnthropic` de langchain-anthropic (tracing automático a LangSmith). | `src/llm/` |
| 0.4 | Configurar LangSmith: crear cuenta en smith.langchain.com, generar API key, agregar variables `LANGSMITH_*` a `.env.example`. | `.env.example` |
| 0.5 | Crear `src/tools/registry.py` — registro que convierte funciones Python en definiciones de tools para el LLM. | `src/tools/` |
| 0.6 | Crear la primera tool: `buscar_cliente` en `src/tools/db_cliente.py`. | `src/tools/` |
| 0.7 | Crear `src/skills/personalidad.md` — extraer solo la sección de identidad/tono de la skill agente-comercial. | `src/skills/` |
| 0.8 | Crear `src/agent/orchestrator.py` — versión mínima que: recibe mensaje, carga skill personalidad, llama al LLM con tools disponibles, devuelve respuesta. | `src/agent/` |
| 0.9 | Crear `src/api/webhooks.py` — recibe webhook de WhatsApp, pasa al orquestador, responde. | `src/api/` |
| 0.10 | **Verificar en LangSmith** que las trazas aparecen: enviar un mensaje de prueba por WhatsApp y confirmar que la traza completa (prompt, respuesta, tokens, tool calls) es visible en smith.langchain.com. | LangSmith dashboard |

**Resultado:** Puedes enviar un WhatsApp → el agente responde con personalidad y puede buscar si el cliente existe. **Y en LangSmith ves cada detalle de lo que pasó internamente.**

**Cuidado con tokens:** En esta fase solo cargas `personalidad.md` (~300 tokens) + 1 tool definition (~80 tokens). Total por llamada: ~380 tokens de sistema.

**Cuidado con LangSmith:** El plan Developer gratuito incluye 5,000 trazas/mes. Una conversación de 8 mensajes genera ~6-10 trazas (una por llamada al LLM). Con 100 cotizaciones/mes = ~600-1,000 trazas. Estás dentro del límite gratis.

---

### Fase 1 — Recopilación Inteligente (Semana 2)
**Objetivo:** El agente hace las preguntas correctas según la fase de conversación.

| Paso | Qué hacer | Archivos |
|------|-----------|----------|
| 1.1 | Crear `src/skills/recopilacion.md` — campos necesarios, estrategia de preguntas. | `src/skills/` |
| 1.2 | Crear `src/agent/phase_detector.py` — analiza la conversación y determina la fase (1-6). | `src/agent/` |
| 1.3 | Crear `src/agent/conversation.py` — estado de conversación: datos recopilados, fase actual, datos faltantes. | `src/agent/` |
| 1.4 | Crear tools: `consultar_historial`, `consultar_tarifas` en `src/tools/db_cotizacion.py` y `db_tarifas.py`. | `src/tools/` |
| 1.5 | Actualizar orquestador: cargar skills según fase detectada. Fase 1-2 = personalidad + recopilacion. | `src/agent/orchestrator.py` |

**Cuidado con tokens:** Ahora cargas personalidad (~300) + recopilacion (~400) + 3 tool defs (~240). Total: ~940 tokens de sistema. Aceptable.

**Cuidado con tools:** `phase_detector.py` NO es un tool del LLM — es lógica Python pura que corre antes de llamar al LLM. No consume tokens extra.

---

### Fase 2 — Cotización Automática (Semana 3-4)
**Objetivo:** El agente calcula precios, genera Word/PDF, y lo envía por WhatsApp.

| Paso | Qué hacer | Archivos |
|------|-----------|----------|
| 2.1 | Crear `src/tools/db_tarifas.py` — `calcular_precio`: recibe servicios, consulta tarifas en DB, aplica lógica de descuentos por historial, devuelve desglose. | `src/tools/` |
| 2.2 | Copiar plantilla a `src/templates/cotizacion_v2.docx`. | `src/templates/` |
| 2.3 | Crear `src/tools/doc_generator.py` — `generar_cotizacion_docx`: usa python-docx para rellenar la plantilla con datos del cliente y servicios. Luego convierte a PDF con LibreOffice headless. | `src/tools/` |
| 2.4 | Crear `src/storage/s3.py` — sube el PDF a S3, devuelve URL. | `src/storage/` |
| 2.5 | Crear `src/tools/whatsapp_sender.py` — `enviar_pdf`: descarga de S3, sube como media a Meta API, envía al cliente. | `src/tools/` |
| 2.6 | Crear `src/skills/cotizacion.md` — instrucciones mínimas para que el LLM sepa cuándo invocar las tools de cotización. | `src/skills/` |
| 2.7 | Crear `src/tools/db_cotizacion.py` — `registrar_cotizacion`: INSERT en DB con número, total, estado. | `src/tools/` |

**Cuidado con tokens:** En fase 3, cargas cotizacion.md (~200) + personalidad (~300) + 5 tool defs (~400). Total: ~900 tokens. El PDF se genera en Python, NO en el LLM.

**Cuidado con tools:**
- `doc_generator.py` usa **python-docx** (NO docx-js). Es Python puro, se ejecuta en tu servidor.
- La conversión a PDF usa LibreOffice headless: `libreoffice --headless --convert-to pdf archivo.docx`
- El upload a S3 usa boto3. Necesitas un bucket S3 con permisos de escritura.
- El envío por WhatsApp requiere primero subir el media a Meta API y luego enviar el mensaje con el media_id.

---

### Fase 3 — Dashboards (Semana 5-6)
**Objetivo:** María Luisa puede ver conversaciones en vivo y cotizaciones.

| Paso | Qué hacer | Archivos |
|------|-----------|----------|
| 3.1 | Inicializar proyecto Next.js en `frontend/`. Instalar Tailwind, shadcn/ui. | `frontend/` |
| 3.2 | Crear endpoints REST en FastAPI: `GET /api/conversations`, `GET /api/conversations/{id}`, `GET /api/quotes`, `GET /api/quotes/{id}`. | `src/api/` |
| 3.3 | Implementar WebSocket en FastAPI para conversaciones en vivo: cuando llega un mensaje de WhatsApp, se emite por WS al dashboard. | `src/api/` |
| 3.4 | Crear `ConversationList.tsx` — lista de conversaciones con último mensaje, estado, cliente. | `frontend/src/components/` |
| 3.5 | Crear `ChatWindow.tsx` — muestra la conversación completa. Solo lectura (María Luisa observa, no interviene). | `frontend/src/components/` |
| 3.6 | Crear `QuoteTable.tsx` — tabla con filtros por estado, fecha, cliente. | `frontend/src/components/` |
| 3.7 | Crear `QuoteDetail.tsx` — detalle de cotización con preview del PDF. | `frontend/src/components/` |

**Cuidado:** Estos dashboards NO consumen tokens. Son puro frontend + queries a PostgreSQL.

---

### Fase 4 — Seguimiento y Objeciones (Semana 7)
**Objetivo:** El agente hace follow-up automático y maneja objeciones.

| Paso | Qué hacer | Archivos |
|------|-----------|----------|
| 4.1 | Crear `src/skills/seguimiento.md` y `src/skills/objeciones.md`. | `src/skills/` |
| 4.2 | Crear `src/tools/db_seguimiento.py` — `crear_seguimiento`, `listar_pendientes`. | `src/tools/` |
| 4.3 | Crear scheduler (APScheduler o cron): cada hora revisa seguimientos pendientes, envía mensaje de follow-up por WhatsApp. | `src/scheduler.py` |
| 4.4 | Crear `src/tools/db_solicitudes.py` — `escalar_a_ml`: crea solicitud para María Luisa cuando el descuento excede el rango. | `src/tools/` |

**Cuidado con tokens:** El scheduler es Python puro. Solo invoca al LLM cuando necesita generar el mensaje de follow-up personalizado. En ese momento carga seguimiento.md (~200) + personalidad (~300) = ~500 tokens.

---

### Fase 5 — Cierre y Deploy (Semana 8)
**Objetivo:** El agente detecta aprobaciones, genera órdenes, y todo corre en AWS.

| Paso | Qué hacer | Archivos |
|------|-----------|----------|
| 5.1 | Crear `src/skills/cierre.md` — detección de aprobación, flujo de orden de servicio. | `src/skills/` |
| 5.2 | Crear `src/tools/db_ordenes.py` — `crear_orden_servicio`. | `src/tools/` |
| 5.3 | Desplegar backend en AWS ECS Fargate (contenedor Docker). | `Dockerfile`, `docker-compose.yml` |
| 5.4 | Desplegar frontend en Vercel o AWS Amplify. | `frontend/` |
| 5.5 | Configurar dominio, HTTPS, variables de entorno en producción. | Infra |
| 5.6 | Conectar webhook de WhatsApp al endpoint público del backend. | Meta Business |

---

## 7. Stack Tecnológico Definitivo

### Backend
| Tecnología | Uso | Justificación |
|------------|-----|---------------|
| Python 3.12 | Lenguaje principal | Tu preferencia, ecosistema maduro para IA |
| FastAPI | Framework web | Async nativo, auto-docs OpenAPI, WebSocket support |
| SQLAlchemy 2.0 | ORM | Async support, tipado fuerte, Alembic para migraciones |
| Alembic | Migraciones DB | Estándar con SQLAlchemy |
| python-docx | Generación Word | Rellena la plantilla existente de ML Traductores |
| LibreOffice headless | Word→PDF | Conversión fiel, gratis, corre en Docker |
| boto3 | AWS S3 | Upload de PDFs generados |
| httpx | HTTP client (async) | Para llamadas a Meta API y APIs de IA |
| APScheduler | Scheduler | Seguimientos automáticos sin infraestructura extra |
| Pydantic v2 | Validación | Ya integrado en FastAPI |

### IA
| Tecnología | Uso | Justificación |
|------------|-----|---------------|
| Anthropic Claude (Sonnet) | Motor principal | Activo, excelente en español, tool_use nativo |
| langchain-anthropic | Wrapper de Claude | Tracing automático a LangSmith, interfaz compatible con langchain-openai |
| langchain-core | Tipos base | Mensajes, tools, schemas — NO el framework completo de LangChain |
| Capa de abstracción propia | Router LLM | Permite cambiar a OpenAI/otro sin tocar el orquestador |

### Observabilidad
| Tecnología | Uso | Justificación |
|------------|-----|---------------|
| LangSmith | Tracing de LLM | Ver inputs/outputs, tokens, latencia, tool calls, errores |
| langsmith (SDK Python) | Envío de trazas | Integración automática vía langchain-anthropic |
| Plan: Developer (gratis) | 5,000 trazas/mes | Suficiente para ~100-200 cotizaciones/mes |

### Frontend
| Tecnología | Uso | Justificación |
|------------|-----|---------------|
| Next.js 14 (App Router) | Framework | SSR, excelente DX, deploy fácil |
| Tailwind CSS | Estilos | Rápido, consistente, shadcn/ui compatible |
| shadcn/ui | Componentes | UI profesional y pulida para María Luisa |
| WebSocket (native) | Tiempo real | Conversaciones en vivo sin polling |

### Infraestructura
| Tecnología | Uso | Justificación |
|------------|-----|---------------|
| AWS ECS Fargate | Backend | Contenedores sin gestionar servidores, escala automáticamente |
| AWS RDS PostgreSQL | Base de datos | Ya existe |
| AWS S3 | Almacenamiento PDFs | Barato, integrado con el ecosistema |
| Vercel | Frontend | Deploy automático, CDN global, gratis para este volumen |
| Docker | Contenedores | Desarrollo local idéntico a producción |

### Cuentas / servicios necesarios

| Servicio | ¿Ya lo tienes? | Acción |
|----------|----------------|--------|
| Meta WhatsApp Business API | ✅ Sí | — |
| AWS (RDS, S3, ECS) | ✅ Parcial (RDS) | Crear bucket S3, configurar ECS |
| Anthropic API | ✅ Sí | — |
| LangSmith | ❌ Por crear | Registro gratuito en smith.langchain.com |
| Vercel | ❓ Verificar | Crear cuenta gratuita si no existe |
| Dominio propio (opcional) | ❓ Verificar | Para el dashboard |

---

## 8. Estimación de Consumo de Tokens por Conversación

Conversación típica: 8-12 mensajes del cliente → 5-7 llamadas al LLM.

| Fase | Llamadas LLM | Tokens sistema/llamada | Tokens conversación/llamada | Total estimado |
|------|-------------|----------------------|---------------------------|----------------|
| Fase 1-2 (recopilar) | 3-4 | ~940 | ~500-2000 | ~4,000-12,000 |
| Fase 3 (cotizar) | 1 | ~900 | ~1000 | ~1,900 |
| Fase 4 (presentar) | 1 | ~600 | ~500 | ~1,100 |
| Fase 5 (seguimiento) | 0-3 | ~500 | ~500 | 0-3,000 |
| Fase 6 (cierre) | 1 | ~600 | ~500 | ~1,100 |
| **Total por conversación** | **6-10** | | | **~8,000-19,000 tokens** |

Con Claude Sonnet a ~$3/MTok input, ~$15/MTok output, una conversación completa cuesta aproximadamente **$0.05 - $0.15 USD**.

---

## 9. Próximos Pasos Inmediatos

1. **Tú:** Sube los models/esquemas de la base de datos actual para que los integre al proyecto.
2. **Tú:** Confirma si ya tienes cuenta de AWS con acceso a S3 y ECS, o solo RDS.
3. **Tú:** Crea tu cuenta gratuita en https://smith.langchain.com y genera una API key.
4. **Yo:** Creo la estructura del repositorio y los archivos base de la Fase 0 (incluyendo configuración de LangSmith).
5. **Yo:** Fragmento la skill `agente-comercial` actual en las skills modulares (`personalidad.md`, `recopilacion.md`, etc.) para optimizar tokens.
6. **Yo:** Diseño el `cotizacion-generator` como conjunto de tools (que es lo que le faltaba al proyecto).
