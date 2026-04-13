-- ==========================================
-- ML TRADUCTORES - ESQUEMA CORE (10 TABLAS)
-- ==========================================

-- 1. Tabla: clientes
CREATE TABLE IF NOT EXISTS clientes (
    id SERIAL PRIMARY KEY,
    nombre_empresa VARCHAR(200) NOT NULL UNIQUE,
    tipo_cliente VARCHAR(50) DEFAULT 'Empresa', -- Empresa, Persona Natural
    nivel_precio VARCHAR(20) DEFAULT 'nuevo', -- premium, estandar, nuevo
    descuento_min_porcentaje DECIMAL(5,2) DEFAULT 0,
    descuento_max_porcentaje DECIMAL(5,2) DEFAULT 0,
    markup_personalizado DECIMAL(5,2), -- Si es NULL, se usa el 30% estándar
    exento_iva BOOLEAN DEFAULT FALSE,
    notas_pricing TEXT,
    es_recurrente BOOLEAN DEFAULT FALSE,
    servicios_confirmados INTEGER DEFAULT 0,
    ultima_cotizacion DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Tabla: contactos
CREATE TABLE IF NOT EXISTS contactos (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    nombre_completo VARCHAR(200) NOT NULL,
    email VARCHAR(150),
    telefono VARCHAR(50),
    cargo VARCHAR(100),
    es_principal BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Tabla: servicios
CREATE TABLE IF NOT EXISTS servicios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    idioma_origen VARCHAR(50),
    idioma_destino VARCHAR(50),
    precio_base DECIMAL(12,2) NOT NULL, -- Costo interno
    precio_cliente DECIMAL(12,2) NOT NULL, -- Precio ya con markup
    unidad_cobro VARCHAR(20) NOT NULL, -- por_hora, por_palabra, por_minuto
    num_interpretes_default INTEGER DEFAULT 1,
    notas TEXT,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Tabla: tarifas_alquiler_equipos
CREATE TABLE IF NOT EXISTS tarifas_alquiler_equipos (
    id SERIAL PRIMARY KEY,
    tipo_equipo VARCHAR(50) NOT NULL, -- receptores_simultanea, portatiles, etc.
    descripcion TEXT,
    cantidad_min INTEGER DEFAULT 1,
    cantidad_max INTEGER DEFAULT 9999,
    num_dias INTEGER, -- NULL para equipos que no dependen de días en tarifa base
    precio_base DECIMAL(12,2),
    precio_cliente DECIMAL(12,2) NOT NULL,
    notas TEXT,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Tabla: recargos
CREATE TABLE IF NOT EXISTS recargos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    porcentaje DECIMAL(5,2) NOT NULL,
    descripcion TEXT,
    activo BOOLEAN DEFAULT TRUE
);

-- 6. Tabla: cotizaciones
CREATE TABLE IF NOT EXISTS cotizaciones (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER REFERENCES clientes(id),
    contacto_id INTEGER REFERENCES contactos(id),
    numero_cotizacion VARCHAR(20) NOT NULL UNIQUE,
    fecha DATE NOT NULL DEFAULT CURRENT_DATE,
    ubicacion_evento VARCHAR(200),
    es_fuera_de_bogota BOOLEAN DEFAULT FALSE,
    subtotal DECIMAL(15,2) NOT NULL,
    iva DECIMAL(15,2) NOT NULL,
    total DECIMAL(15,2) NOT NULL,
    exento_iva BOOLEAN DEFAULT FALSE,
    validez_oferta VARCHAR(200),
    forma_pago VARCHAR(200),
    estado VARCHAR(20) DEFAULT 'borrador', -- borrador, enviada, aprobada, perdida, etc.
    notas_internas TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. Tabla: versiones_cotizacion
CREATE TABLE IF NOT EXISTS versiones_cotizacion (
    id SERIAL PRIMARY KEY,
    cotizacion_id INTEGER NOT NULL REFERENCES cotizaciones(id) ON DELETE CASCADE,
    version_label VARCHAR(10) NOT NULL, -- A, B, C...
    total_anterior DECIMAL(15,2),
    total_nuevo DECIMAL(15,2) NOT NULL,
    motivo_cambio TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 8. Tabla: lineas_cotizacion
CREATE TABLE IF NOT EXISTS lineas_cotizacion (
    id SERIAL PRIMARY KEY,
    cotizacion_id INTEGER NOT NULL REFERENCES cotizaciones(id) ON DELETE CASCADE,
    servicio_id INTEGER REFERENCES servicios(id),
    equipo_alquiler_id INTEGER REFERENCES tarifas_alquiler_equipos(id),
    cantidad DECIMAL(10,2) DEFAULT 1,
    precio_unitario DECIMAL(12,2) NOT NULL,
    precio_total DECIMAL(15,2) NOT NULL,
    fecha_servicio_inicio DATE,
    fecha_servicio_fin DATE,
    horario VARCHAR(100),
    num_interpretes INTEGER,
    num_equipos INTEGER,
    descripcion_generada TEXT,
    orden INTEGER DEFAULT 0
);

-- 9. Tabla: ordenes_servicio
CREATE TABLE IF NOT EXISTS ordenes_servicio (
    id SERIAL PRIMARY KEY,
    cotizacion_id INTEGER NOT NULL REFERENCES cotizaciones(id),
    numero_os VARCHAR(20) UNIQUE,
    fecha_emision DATE DEFAULT CURRENT_DATE,
    estado VARCHAR(20) DEFAULT 'pendiente',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 10. Tabla: seguimientos
CREATE TABLE IF NOT EXISTS seguimientos (
    id SERIAL PRIMARY KEY,
    cotizacion_id INTEGER NOT NULL REFERENCES cotizaciones(id),
    fecha_seguimiento TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metodo VARCHAR(50), -- whatsapp, email, llamada
    resultado TEXT,
    proximo_seguimiento DATE
);
