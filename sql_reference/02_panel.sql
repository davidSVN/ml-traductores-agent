-- ==========================================
-- ML TRADUCTORES - ESQUEMA PANEL (4 TABLAS)
-- ==========================================

-- 1. Tabla: conversaciones
CREATE TABLE IF NOT EXISTS conversaciones (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER REFERENCES clientes(id) ON DELETE SET NULL,
    canal VARCHAR(20) NOT NULL DEFAULT 'whatsapp', -- whatsapp, gmail, telegram, web
    estado VARCHAR(20) NOT NULL DEFAULT 'activa', -- activa, en_seguimiento, cerrada, archivada
    telefono_whatsapp VARCHAR(20), -- Identificador único para WhatsApp
    nombre_temporal VARCHAR(100),
    ultimo_mensaje_preview TEXT,
    ultimo_mensaje_at TIMESTAMP WITH TIME ZONE,
    mensajes_no_leidos INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_conversaciones_cliente_id ON conversaciones(cliente_id);
CREATE INDEX idx_conversaciones_estado ON conversaciones(estado);
CREATE INDEX idx_conversaciones_ultimo_mensaje ON conversaciones(ultimo_mensaje_at DESC);

-- 2. Tabla: mensajes
CREATE TABLE IF NOT EXISTS mensajes (
    id SERIAL PRIMARY KEY,
    conversacion_id INTEGER NOT NULL REFERENCES conversaciones(id) ON DELETE CASCADE,
    origen VARCHAR(20) NOT NULL, -- cliente, agente, sistema
    contenido TEXT NOT NULL,
    tipo_contenido VARCHAR(20) NOT NULL DEFAULT 'texto', -- texto, imagen, documento, audio, ubicacion, template
    url_archivo TEXT,
    whatsapp_message_id VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_mensajes_conversacion_id ON mensajes(conversacion_id);
CREATE UNIQUE INDEX idx_mensajes_whatsapp_id ON mensajes(whatsapp_message_id) WHERE whatsapp_message_id IS NOT NULL;
CREATE INDEX idx_mensajes_created_at ON mensajes(created_at);

-- 3. Tabla: solicitudes_agente
CREATE TABLE IF NOT EXISTS solicitudes_agente (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER REFERENCES clientes(id) ON DELETE SET NULL,
    cotizacion_id INTEGER REFERENCES cotizaciones(id) ON DELETE SET NULL,
    conversacion_id INTEGER REFERENCES conversaciones(id) ON DELETE SET NULL,
    tipo VARCHAR(30) NOT NULL, -- aprobar_cotizacion, completar_cliente, consulta_precio, escalar_negociacion, otro
    estado VARCHAR(20) NOT NULL DEFAULT 'pendiente', -- pendiente, aprobada, rechazada, modificada, cancelada
    prioridad VARCHAR(10) DEFAULT 'normal', -- urgente, normal, baja
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT,
    datos_formulario JSONB DEFAULT '{}',
    respuesta_encargada TEXT,
    archivo_adjunto TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resuelta_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_solicitudes_estado ON solicitudes_agente(estado);
CREATE INDEX idx_solicitudes_tipo ON solicitudes_agente(tipo);
CREATE INDEX idx_solicitudes_cliente_id ON solicitudes_agente(cliente_id);
CREATE INDEX idx_solicitudes_cotizacion_id ON solicitudes_agente(cotizacion_id);

-- 4. Tabla: mensajes_internos
CREATE TABLE IF NOT EXISTS mensajes_internos (
    id SERIAL PRIMARY KEY,
    solicitud_id INTEGER NOT NULL REFERENCES solicitudes_agente(id) ON DELETE CASCADE,
    origen VARCHAR(20) NOT NULL, -- agente, encargada
    contenido TEXT NOT NULL,
    tipo_contenido VARCHAR(20) DEFAULT 'texto', -- texto, archivo, accion
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_mensajes_internos_solicitud_id ON mensajes_internos(solicitud_id);

-- TRIGGERS
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_conversaciones_updated_at
BEFORE UPDATE ON conversaciones
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE OR REPLACE FUNCTION sync_conversacion_on_mensaje()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversaciones
    SET 
        ultimo_mensaje_at = NEW.created_at,
        ultimo_mensaje_preview = LEFT(NEW.contenido, 100),
        updated_at = NOW()
    WHERE id = NEW.conversacion_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sync_conversacion_after_mensaje
AFTER INSERT ON mensajes
FOR EACH ROW
EXECUTE FUNCTION sync_conversacion_on_mensaje();
