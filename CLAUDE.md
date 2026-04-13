# CLAUDE.md — ML Traductores Agent

## Qué es este proyecto

Agente comercial de IA para ML Traductores (empresa colombiana de servicios lingüísticos). El agente conversa con clientes por WhatsApp, recopila necesidades, cotiza servicios, genera PDFs y hace seguimiento. María Luisa (la dueña) solo observa desde un dashboard.

## Stack tecnológico

- **Backend:** Python 3.12 + FastAPI
- **DB:** PostgreSQL (AWS RDS) con SQLAlchemy 2.0 async + Alembic
- **IA:** Anthropic Claude vía `langchain-anthropic` (NO LangChain completo)
- **Observabilidad:** LangSmith (tracing automático vía `langchain-anthropic`)
- **WhatsApp:** Meta Cloud API (webhook entrante + httpx para enviar)
- **Frontend (futuro):** Next.js 14 + Tailwind + shadcn/ui
- **Infraestructura (futuro):** AWS ECS Fargate + S3

## Estructura del proyecto

```
ml-traductores-agent/
├── CLAUDE.md                          ← Este archivo
├── PLAN_IMPLEMENTACION.md             ← Plan completo (referencia, no modificar)
├── FASE_0_TAREAS.md                   ← Tareas de la fase actual
├── .env.example
├── .gitignore
├── pyproject.toml
├── docker-compose.yml
├── Dockerfile
├── alembic/
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
├── src/
│   ├── __init__.py
│   ├── main.py                        # FastAPI app entry point
│   ├── config.py                      # Pydantic Settings (env vars)
│   ├── api/
│   │   ├── __init__.py
│   │   └── webhooks.py                # POST/GET /webhook/whatsapp
│   ├── agent/
│   │   ├── __init__.py
│   │   └── orchestrator.py            # Carga skills + tools → llama LLM → ejecuta tools
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── router.py                  # Abstracción: LLMRouter(provider="anthropic"|"openai")
│   │   ├── anthropic_provider.py      # ChatAnthropic con LangSmith tracing
│   │   └── schemas.py                 # ToolDefinition, ToolCall, LLMResponse
│   ├── skills/                        # Archivos .md que se inyectan como system prompt
│   │   ├── personalidad.md
│   │   └── recopilacion.md
│   ├── tools/                         # Funciones Python invocables por el LLM
│   │   ├── __init__.py
│   │   ├── registry.py                # @register_tool + execute_tool + get_tool_definitions
│   │   └── db_cliente.py              # buscar_cliente, crear_cliente
│   ├── db/
│   │   ├── __init__.py
│   │   ├── engine.py                  # create_async_engine + get_db dependency
│   │   └── models.py                  # 14 tablas SQLAlchemy (clientes, cotizaciones, etc.)
│   ├── whatsapp/
│   │   ├── __init__.py
│   │   └── client.py                  # WhatsAppClient: send_text, send_document
│   ├── storage/
│   │   └── __init__.py
│   └── templates/
│       └── cotizacion_v2.docx         # Plantilla Word de ML Traductores
└── tests/
```

## Arquitectura conceptual clave

### Skills vs Tools (CRÍTICO para costos)

**Skills = archivos .md** que se cargan como system prompt del LLM. Consumen tokens de entrada en cada llamada. Regla: cargar SOLO las skills de la fase actual, nunca todas juntas.

**Tools = funciones Python** registradas con `@register_tool`. El LLM solo recibe la definición (~80 tokens). La ejecución ocurre en Python, no consume tokens. Toda operación de DB, generación de docs, envío de WhatsApp son tools.

### Flujo por mensaje

```
WhatsApp → webhook → orquestador → [carga skills de la fase] → [carga tool defs] → LLM
                                                                                      ↓
WhatsApp ← wa_client ← orquestador ← [si hay tool_calls: ejecutar → re-llamar LLM] ← respuesta
```

### LangSmith

Se configura con env vars. El tracing es automático al usar `ChatAnthropic` de `langchain-anthropic`. No necesitas código adicional. Solo asegúrate de que `LANGSMITH_TRACING=true` en `.env`.

## Convenciones de código

- Async everywhere: todas las funciones de DB, HTTP, y LLM son async.
- Type hints en todo. Usar `Mapped[]` de SQLAlchemy 2.0 para models.
- Tools siempre con `@register_tool` decorator del registry.
- Skills siempre en archivos `.md` separados en `src/skills/`.
- Imports: usar `from src.xxx import yyy` (imports absolutos desde `src/`).
- No usar LangChain completo (chains, agents, memory). Solo `langchain-core`, `langchain-anthropic`, `langsmith`.
- Env vars: todo en `src/config.py` con Pydantic Settings.
- Logs: usar `logging.getLogger(__name__)`.

## Base de datos

14 tablas ya definidas. Los SQL originales están en el proyecto como referencia:
- `01_core.sql`: clientes, contactos, servicios, tarifas_alquiler_equipos, recargos, cotizaciones, versiones_cotizacion, lineas_cotizacion, ordenes_servicio, seguimientos
- `02_panel.sql`: conversaciones, mensajes, solicitudes_agente, mensajes_internos

Los models de SQLAlchemy en `src/db/models.py` deben mapear 1:1 con estos SQL.

## Qué NO hacer

- No instalar `langchain` completo. Solo `langchain-core` y `langchain-anthropic`.
- No cargar todas las skills en cada llamada al LLM. Solo las de la fase actual.
- No hacer llamadas directas a `anthropic` SDK. Siempre pasar por `src/llm/router.py`.
- No hardcodear API keys. Todo va en `.env` y se lee con `src/config.py`.
- No crear archivos frontend todavía. El frontend es Fase 3.
