# FASE 0 — Tareas para implementar

Objetivo: proyecto funcional de extremo a extremo. Un mensaje de WhatsApp entra, el agente responde con personalidad, puede buscar clientes en la DB, y todo queda trazado en LangSmith.

Ejecuta las tareas en orden. Cada tarea tiene los archivos a crear/modificar, la lógica exacta, y criterios de completitud.

---

## Tarea 0.1 — Inicializar proyecto

Crear archivos de configuración raíz si no existen.

**Archivos:**
- `pyproject.toml` — dependencias Python:
  ```
  fastapi>=0.115.0, uvicorn[standard]>=0.30.0, python-multipart>=0.0.9
  sqlalchemy[asyncio]>=2.0.30, asyncpg>=0.29.0, alembic>=1.13.0
  langchain-core>=0.3.0, langchain-anthropic>=0.3.21, langsmith>=0.1.0
  python-docx>=1.1.0, boto3>=1.34.0, httpx>=0.27.0, apscheduler>=3.10.0
  pydantic>=2.7.0, pydantic-settings>=2.3.0, python-dotenv>=1.0.0
  ```
- `.env.example` — template con estas variables:
  ```
  DATABASE_URL=postgresql+asyncpg://usuario:password@localhost:5432/ml_traductores
  ANTHROPIC_API_KEY=sk-ant-xxxxx
  LANGSMITH_API_KEY=lsv2_pt_xxxxx
  LANGSMITH_TRACING=true
  LANGSMITH_PROJECT=ml-traductores-agent
  LANGSMITH_ENDPOINT=https://api.smith.langchain.com
  WHATSAPP_TOKEN=EAAxxxxxxx
  WHATSAPP_PHONE_NUMBER_ID=123456789
  WHATSAPP_VERIFY_TOKEN=mi_token_secreto
  WHATSAPP_API_VERSION=v21.0
  AWS_ACCESS_KEY_ID=
  AWS_SECRET_ACCESS_KEY=
  AWS_S3_BUCKET=ml-traductores-cotizaciones
  AWS_REGION=us-east-1
  APP_ENV=development
  APP_HOST=0.0.0.0
  APP_PORT=8000
  LOG_LEVEL=INFO
  ```
- `.gitignore` — Python, .env, node_modules, __pycache__, .venv, .DS_Store
- `docker-compose.yml` — servicios: postgres (port 5432, db ml_traductores) + app (FastAPI, port 8000, depends_on postgres)
- `Dockerfile` — Python 3.12-slim, instalar LibreOffice headless (para futuro PDF), pip install del pyproject.toml

**Completitud:** `docker-compose up` levanta postgres y la app sin errores.

---

## Tarea 0.2 — Config y base de datos

**Archivos:**
- `src/__init__.py` (vacío)
- `src/config.py` — clase `Settings(BaseSettings)` con todas las env vars del `.env.example`. Función `get_settings()` con `@lru_cache`.
- `src/db/__init__.py` (vacío)
- `src/db/engine.py` — `create_async_engine` con `DATABASE_URL`, `async_sessionmaker`, función `get_db()` como dependency de FastAPI (yield session, commit, rollback, close).
- `src/db/models.py` — 14 modelos SQLAlchemy que mapean exactamente estas tablas:

**Esquema CORE (10 tablas):**

```sql
-- clientes: id, nombre_empresa(VARCHAR 200 UNIQUE), tipo_cliente(VARCHAR 50 default 'Empresa'), nivel_precio(VARCHAR 20 default 'nuevo'), descuento_min_porcentaje(DECIMAL 5,2 default 0), descuento_max_porcentaje(DECIMAL 5,2 default 0), markup_personalizado(DECIMAL 5,2 nullable), exento_iva(BOOL default FALSE), notas_pricing(TEXT nullable), es_recurrente(BOOL default FALSE), servicios_confirmados(INT default 0), ultima_cotizacion(DATE nullable), created_at(TIMESTAMPTZ default NOW), updated_at(TIMESTAMPTZ default NOW)

-- contactos: id, cliente_id(FK clientes ON DELETE CASCADE), nombre_completo(VARCHAR 200), email(VARCHAR 150 nullable), telefono(VARCHAR 50 nullable), cargo(VARCHAR 100 nullable), es_principal(BOOL default FALSE), created_at(TIMESTAMPTZ default NOW)

-- servicios: id, nombre(VARCHAR 200), idioma_origen(VARCHAR 50 nullable), idioma_destino(VARCHAR 50 nullable), precio_base(DECIMAL 12,2), precio_cliente(DECIMAL 12,2), unidad_cobro(VARCHAR 20), num_interpretes_default(INT default 1), notas(TEXT nullable), activo(BOOL default TRUE), created_at(TIMESTAMPTZ default NOW)

-- tarifas_alquiler_equipos: id, tipo_equipo(VARCHAR 50), descripcion(TEXT nullable), cantidad_min(INT default 1), cantidad_max(INT default 9999), num_dias(INT nullable), precio_base(DECIMAL 12,2 nullable), precio_cliente(DECIMAL 12,2), notas(TEXT nullable), activo(BOOL default TRUE), created_at(TIMESTAMPTZ default NOW)

-- recargos: id, nombre(VARCHAR 100), porcentaje(DECIMAL 5,2), descripcion(TEXT nullable), activo(BOOL default TRUE)

-- cotizaciones: id, cliente_id(FK clientes nullable), contacto_id(FK contactos nullable), numero_cotizacion(VARCHAR 20 UNIQUE), fecha(DATE default CURRENT_DATE), ubicacion_evento(VARCHAR 200 nullable), es_fuera_de_bogota(BOOL default FALSE), subtotal(DECIMAL 15,2), iva(DECIMAL 15,2), total(DECIMAL 15,2), exento_iva(BOOL default FALSE), validez_oferta(VARCHAR 200 nullable), forma_pago(VARCHAR 200 nullable), estado(VARCHAR 20 default 'borrador'), notas_internas(TEXT nullable), created_at(TIMESTAMPTZ default NOW), updated_at(TIMESTAMPTZ default NOW)

-- versiones_cotizacion: id, cotizacion_id(FK cotizaciones ON DELETE CASCADE), version_label(VARCHAR 10), total_anterior(DECIMAL 15,2 nullable), total_nuevo(DECIMAL 15,2), motivo_cambio(TEXT nullable), created_at(TIMESTAMPTZ default NOW)

-- lineas_cotizacion: id, cotizacion_id(FK cotizaciones ON DELETE CASCADE), servicio_id(FK servicios nullable), equipo_alquiler_id(FK tarifas_alquiler_equipos nullable), cantidad(DECIMAL 10,2 default 1), precio_unitario(DECIMAL 12,2), precio_total(DECIMAL 15,2), fecha_servicio_inicio(DATE nullable), fecha_servicio_fin(DATE nullable), horario(VARCHAR 100 nullable), num_interpretes(INT nullable), num_equipos(INT nullable), descripcion_generada(TEXT nullable), orden(INT default 0)

-- ordenes_servicio: id, cotizacion_id(FK cotizaciones), numero_os(VARCHAR 20 UNIQUE nullable), fecha_emision(DATE default CURRENT_DATE), estado(VARCHAR 20 default 'pendiente'), created_at(TIMESTAMPTZ default NOW)

-- seguimientos: id, cotizacion_id(FK cotizaciones), fecha_seguimiento(TIMESTAMPTZ default NOW), metodo(VARCHAR 50 nullable), resultado(TEXT nullable), proximo_seguimiento(DATE nullable)
```

**Esquema PANEL (4 tablas):**

```sql
-- conversaciones: id, cliente_id(FK clientes ON DELETE SET NULL nullable), canal(VARCHAR 20 default 'whatsapp'), estado(VARCHAR 20 default 'activa'), telefono_whatsapp(VARCHAR 20 nullable), nombre_temporal(VARCHAR 100 nullable), ultimo_mensaje_preview(TEXT nullable), ultimo_mensaje_at(TIMESTAMPTZ nullable), mensajes_no_leidos(INT default 0), metadata(JSONB default '{}'), created_at(TIMESTAMPTZ default NOW), updated_at(TIMESTAMPTZ default NOW). Índices: cliente_id, estado, ultimo_mensaje_at.

-- mensajes: id, conversacion_id(FK conversaciones ON DELETE CASCADE), origen(VARCHAR 20), contenido(TEXT), tipo_contenido(VARCHAR 20 default 'texto'), url_archivo(TEXT nullable), whatsapp_message_id(VARCHAR 100 nullable UNIQUE), metadata(JSONB default '{}'), created_at(TIMESTAMPTZ default NOW). Índices: conversacion_id, created_at.

-- solicitudes_agente: id, cliente_id(FK clientes ON DELETE SET NULL nullable), cotizacion_id(FK cotizaciones ON DELETE SET NULL nullable), conversacion_id(FK conversaciones ON DELETE SET NULL nullable), tipo(VARCHAR 30), estado(VARCHAR 20 default 'pendiente'), prioridad(VARCHAR 10 default 'normal'), titulo(VARCHAR 200), descripcion(TEXT nullable), datos_formulario(JSONB default '{}'), respuesta_encargada(TEXT nullable), archivo_adjunto(TEXT nullable), created_at(TIMESTAMPTZ default NOW), resuelta_at(TIMESTAMPTZ nullable). Índices: estado, tipo, cliente_id, cotizacion_id.

-- mensajes_internos: id, solicitud_id(FK solicitudes_agente ON DELETE CASCADE), origen(VARCHAR 20), contenido(TEXT), tipo_contenido(VARCHAR 20 default 'texto'), metadata(JSONB default '{}'), created_at(TIMESTAMPTZ default NOW). Índice: solicitud_id.
```

- `alembic/` — configurar Alembic con `alembic init alembic`. Modificar `alembic.ini` para usar `DATABASE_URL` de env. Modificar `env.py` para importar `Base` de `src.db.models` y usar async engine. Generar primera migración con `alembic revision --autogenerate -m "initial_schema"`.

**Completitud:** `alembic upgrade head` crea las 14 tablas en PostgreSQL sin errores.

---

## Tarea 0.3 — Capa LLM con LangSmith

**Archivos:**
- `src/llm/__init__.py` (vacío)
- `src/llm/schemas.py` — 3 dataclasses:
  - `ToolDefinition(name: str, description: str, parameters: dict)`
  - `ToolCall(id: str, name: str, arguments: dict)`
  - `LLMResponse(content: str, tool_calls: list[ToolCall], input_tokens: int, output_tokens: int, stop_reason: str)`
- `src/llm/anthropic_provider.py` — clase `AnthropicProvider`:
  - En `__init__`: configurar env vars de LangSmith (`os.environ`), crear instancia de `ChatAnthropic` de `langchain_anthropic`.
  - Método `async send_message(messages, system_prompt, tools) -> LLMResponse`:
    - Convierte messages a formato LangChain (SystemMessage, HumanMessage, AIMessage, ToolMessage).
    - Si hay tools, las convierte a formato OpenAI-function y las bindea con `llm.bind_tools()`.
    - Llama `await llm.ainvoke(lc_messages)`.
    - LangSmith traza esta llamada automáticamente.
    - Normaliza la respuesta a `LLMResponse`.
- `src/llm/router.py` — clase `LLMRouter`:
  - `__init__(provider="anthropic")`: instancia el provider correspondiente.
  - `async send_message(...)`: delega al provider.
  - Preparado para agregar `openai` en el futuro (comentado).

**Completitud:** Puedes instanciar `LLMRouter()` y llamar `send_message` con un mensaje simple. La traza aparece en smith.langchain.com.

---

## Tarea 0.4 — Registry de tools + primera tool

**Archivos:**
- `src/tools/__init__.py` — importar `db_cliente` para que los decoradores se ejecuten al importar.
- `src/tools/registry.py` — Registro global:
  - Diccionario `_REGISTRY: dict[str, tuple[Callable, ToolDefinition]]`
  - Decorador `@register_tool(name, description, parameters)` que registra la función.
  - `get_tool_definitions(names: list[str] | None) -> list[ToolDefinition]` — devuelve definiciones para enviar al LLM.
  - `async execute_tool(name, arguments, **extra) -> Any` — ejecuta la tool. Pasa `**extra` (ej. `db=session`) a la función.
  - `list_tools() -> list[str]` — lista nombres registrados.
- `src/tools/db_cliente.py` — 2 tools:
  - `buscar_cliente(empresa: str, db: AsyncSession)` — `SELECT` con `ILIKE '%{empresa}%'` en tabla clientes. Si encuentra, devuelve dict con datos + contacto principal. Si no, devuelve `{"encontrado": False}`.
  - `crear_cliente(nombre_empresa, contacto_nombre, db, tipo_cliente, contacto_email, contacto_telefono, contacto_cargo)` — `INSERT` en clientes + contactos. Devuelve `{"cliente_id": ..., "contacto_id": ...}`.

**Completitud:** `list_tools()` devuelve `["buscar_cliente", "crear_cliente"]`. `get_tool_definitions(["buscar_cliente"])` devuelve 1 ToolDefinition.

---

## Tarea 0.5 — Skills (prompts de sistema)

**Archivos:**
- `src/skills/personalidad.md`:
```markdown
Eres el agente comercial virtual de ML Traductores, empresa colombiana con casi 30 años en servicios de traducción, interpretación y transcripción profesional.

## Personalidad
- Cálido pero profesional. Saluda con amabilidad genuina. Usa "usted" salvo que el cliente tutee primero.
- Directo sin ser brusco. Máximo 3 oraciones por mensaje en WhatsApp.
- Asesor, no vendedor. Preguntas para entender, no para presionar.
- Orgulloso de la empresa. Menciona la trayectoria solo cuando aporta valor.

## Reglas de comunicación
- Nunca uses emojis en exceso. Máximo 1 por mensaje.
- Nunca digas "¿En qué puedo ayudarte?" como primera respuesta.
- Si el cliente llega con la solicitud clara, no hagas preguntas innecesarias.
- Siempre firma como "ML Traductores" al cerrar una conversación.

## Servicios disponibles
- Interpretación simultánea y consecutiva (presencial y virtual)
- Traducción de documentos (oficial y no oficial)
- Transcripción (audio/video a texto)
- Alquiler de equipos (cabinas, receptores, portátiles)
```

- `src/skills/recopilacion.md`:
```markdown
## Datos necesarios para cotizar

Recopila estos datos de forma natural en la conversación. No los pidas todos de golpe.

| Campo | Obligatorio | Cómo preguntar |
|-------|------------|----------------|
| Nombre completo | Sí | "¿A nombre de quién elaboro la cotización?" |
| Empresa | Sí | "¿De qué empresa nos contacta?" |
| Email | Sí | "¿Me comparte un correo para enviarle la cotización formal?" |
| Teléfono | Sí | Ya lo tienes si es WhatsApp |
| Servicio(s) | Sí | "¿Qué tipo de servicio necesita?" |
| Idioma(s) | Sí para interp/trad | "¿Entre qué idiomas?" |
| Fecha(s) | Sí | "¿Para qué fecha(s) sería?" |
| Horario | Sí para interpretación | "¿En qué horario?" |
| Ubicación | Sí para presencial | "¿Dónde se realizaría el evento?" |
| Cantidad | Sí | Según servicio: horas, palabras, minutos, equipos |

## Estrategia
- Si el cliente da 3 datos en un mensaje, pregunta los 2 más importantes que falten.
- Si pide interpretación presencial, ofrece equipos proactivamente.
- No ofrezcas servicios adicionales si el cliente tiene prisa.

## Cuando tengas todos los datos
Invoca la tool `buscar_cliente` para verificar si el cliente existe en la DB. Si existe, consulta su historial. Luego avanza a cotizar.
```

**Completitud:** Los archivos existen en `src/skills/` y el orquestador puede leerlos con `Path.read_text()`.

---

## Tarea 0.6 — Orquestador del agente

**Archivo:** `src/agent/orchestrator.py`

Clase `AgentOrchestrator`:

- `__init__`: crea instancia de `LLMRouter()`.
- Constante `SKILLS_DIR` apuntando a `src/skills/`.
- Constante `PHASE_CONFIG` que mapea fase → skills + tools:
  ```python
  "inicial": {"skills": ["personalidad.md", "recopilacion.md"], "tools": ["buscar_cliente", "crear_cliente"]}
  ```
- Método `async handle_message(conversation_history: list[dict], db: AsyncSession, phase: str = "inicial") -> str`:
  1. `_load_skills(phase)` → lee y concatena los .md de la fase.
  2. `get_tool_definitions(config["tools"])` → obtiene definiciones.
  3. `await self.llm.send_message(messages=conversation_history, system_prompt=..., tools=...)`.
  4. Si `response.tool_calls`: ejecutar con `_handle_tool_calls()` y re-llamar al LLM.
  5. Retorna `response.content`.
- Método `async _handle_tool_calls(response, history, system_prompt, tool_defs, db, max_iterations=5)`:
  - Loop: ejecutar cada tool_call con `execute_tool(name, args, db=db)`.
  - Agregar resultados al historial como mensajes `"role": "tool"`.
  - Re-llamar al LLM.
  - Repetir hasta que no haya más tool_calls o se alcance max_iterations.
- Método `_load_skills(phase) -> str`: lee archivos .md y los une con `\n\n---\n\n`.

**Completitud:** `orchestrator.handle_message([{"role": "user", "content": "Hola, necesito interpretación"}], db)` devuelve una respuesta coherente del agente.

---

## Tarea 0.7 — Cliente WhatsApp

**Archivo:** `src/whatsapp/client.py`

Clase `WhatsAppClient`:

- `__init__`: lee token, phone_id, api_version de Settings. Crea `httpx.AsyncClient`.
- `async send_text(to: str, text: str)`: POST a `https://graph.facebook.com/{api_version}/{phone_id}/messages` con body `{"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}}`. Header `Authorization: Bearer {token}`.
- `async send_document(to: str, document_url: str, filename: str, caption: str)`: POST con type `"document"` y link al archivo. (Preparado para Fase 2, no se usa aún).
- Logging de request/response para debug.
- Manejo de errores: si Meta devuelve error, loggear y no crashear.

**Completitud:** `await wa_client.send_text("573001234567", "Hola!")` envía un mensaje real por WhatsApp.

---

## Tarea 0.8 — Webhook + FastAPI app

**Archivos:**
- `src/api/__init__.py` (vacío)
- `src/api/webhooks.py`:
  - `GET /webhook/whatsapp` → verificación del webhook Meta (compara `hub.verify_token` con env var, devuelve `hub.challenge`).
  - `POST /webhook/whatsapp` → recibe payload de Meta:
    1. Extrae mensaje de texto del payload (función `_extract_message`).
    2. Busca o crea conversación en DB por `telefono_whatsapp`.
    3. Verifica que el `whatsapp_message_id` no sea duplicado.
    4. Guarda mensaje del cliente en tabla `mensajes`.
    5. Carga historial de la conversación (últimos 50 mensajes).
    6. Llama `orchestrator.handle_message(history, db, phase="inicial")`.
    7. Guarda respuesta del agente en tabla `mensajes`.
    8. Envía respuesta por WhatsApp con `wa_client.send_text()`.
- `src/main.py`:
  - Crea `FastAPI(title="ML Traductores Agent")`.
  - Incluye router de webhooks.
  - Event `on_startup`: importar tools (`src.tools.db_cliente`) para que se registren.
  - `uvicorn.run` con host/port de Settings.

**Completitud:** Puedes enviar un WhatsApp al número configurado, el agente responde con personalidad, y si mencionas una empresa, intenta buscarla en la DB.

---

## Tarea 0.9 — Docker compose funcional

**Archivos:**
- `docker-compose.yml`:
  ```yaml
  services:
    postgres:
      image: postgres:16
      environment:
        POSTGRES_DB: ml_traductores
        POSTGRES_USER: mluser
        POSTGRES_PASSWORD: mlpassword
      ports:
        - "5432:5432"
      volumes:
        - pgdata:/var/lib/postgresql/data
    app:
      build: .
      ports:
        - "8000:8000"
      env_file: .env
      depends_on:
        - postgres
  volumes:
    pgdata:
  ```
- `Dockerfile`:
  ```dockerfile
  FROM python:3.12-slim
  RUN apt-get update && apt-get install -y libreoffice-writer && rm -rf /var/lib/apt/lists/*
  WORKDIR /app
  COPY pyproject.toml .
  RUN pip install --no-cache-dir .
  COPY . .
  CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```

**Completitud:** `docker-compose up --build` levanta todo. `curl http://localhost:8000/docs` muestra la documentación de FastAPI.

---

## Orden de ejecución recomendado

1. Tarea 0.1 (proyecto base)
2. Tarea 0.2 (config + DB + models + Alembic)
3. Tarea 0.3 (LLM + LangSmith)
4. Tarea 0.4 (tools registry + buscar_cliente)
5. Tarea 0.5 (skills .md)
6. Tarea 0.6 (orquestador)
7. Tarea 0.7 (WhatsApp client)
8. Tarea 0.8 (webhook + main.py)
9. Tarea 0.9 (Docker)

Cada tarea debe funcionar de forma aislada antes de pasar a la siguiente.
