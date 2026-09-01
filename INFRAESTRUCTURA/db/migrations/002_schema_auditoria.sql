-- =============================================================================
-- SCFV v6 — Migración 002: Esquema de Auditoría, Eventos y Hash Chain
-- Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
-- Fecha: 2026-08-26
-- Propósito: Crear las tablas del dominio de auditoría, trazabilidad y eventos
--            (prefijo auditoria_)
-- =============================================================================

-- Habilitar claves foráneas y WAL mode
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- =============================================================================
-- 1. Hash Chain (Cadena de Hashes para Inmutabilidad)
-- =============================================================================
CREATE TABLE IF NOT EXISTS auditoria_hash_chain (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tabla_origen TEXT NOT NULL,                -- Tabla que se está registrando
    registro_id TEXT NOT NULL,                 -- ID único del registro en esa tabla
    datos_hash TEXT NOT NULL,                  -- SHA-256 de los datos (JSON)
    hash_previo TEXT NOT NULL,                 -- SHA-256 del registro anterior
    hash_actual TEXT NOT NULL,                 -- SHA-256(datos_hash || hash_previo)
    creado_en INTEGER NOT NULL,                -- Timestamp UNIX
    UNIQUE(tabla_origen, registro_id)
);

CREATE INDEX IF NOT EXISTS idx_hash_chain_tabla ON auditoria_hash_chain(tabla_origen);
CREATE INDEX IF NOT EXISTS idx_hash_chain_registro ON auditoria_hash_chain(registro_id);
CREATE INDEX IF NOT EXISTS idx_hash_chain_previo ON auditoria_hash_chain(hash_previo);

-- =============================================================================
-- 2. Event Store (Almacenamiento de Eventos para Reconstrucción)
-- =============================================================================
CREATE TABLE IF NOT EXISTS auditoria_event_store (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE NOT NULL,             -- UUID generado por el cliente
    saga_id TEXT,                              -- UUID de la saga (si aplica)
    tipo TEXT NOT NULL,                        -- Ej. 'VENTA_CONFIRMADA', 'ASIENTO_REGISTRADO'
    origen TEXT NOT NULL,                      -- Componente que emite el evento
    payload JSON NOT NULL,                     -- Datos del evento en JSON
    timestamp INTEGER NOT NULL,                -- Momento de emisión
    version INTEGER DEFAULT 1,                 -- Versión del formato del evento
    procesado BOOLEAN DEFAULT 0                -- Marcador para idempotencia
);

CREATE INDEX IF NOT EXISTS idx_event_store_tipo ON auditoria_event_store(tipo);
CREATE INDEX IF NOT EXISTS idx_event_store_saga ON auditoria_event_store(saga_id);
CREATE INDEX IF NOT EXISTS idx_event_store_procesado ON auditoria_event_store(procesado);
CREATE INDEX IF NOT EXISTS idx_event_store_timestamp ON auditoria_event_store(timestamp);

-- =============================================================================
-- 3. Event Processing (Idempotencia por Consumidor)
-- =============================================================================
CREATE TABLE IF NOT EXISTS auditoria_event_processing (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL,                    -- Referencia a auditoria_event_store
    consumidor TEXT NOT NULL,                  -- Ej. 'motor_contable', 'fractal_ventas'
    procesado_en INTEGER NOT NULL,             -- Timestamp de procesamiento
    estado TEXT NOT NULL CHECK (estado IN ('EXITOSO', 'FALLIDO', 'EN_PROCESO')),
    error TEXT,                                -- Mensaje de error si falló
    UNIQUE(event_id, consumidor),
    FOREIGN KEY (event_id) REFERENCES auditoria_event_store(event_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_event_processing_event ON auditoria_event_processing(event_id);
CREATE INDEX IF NOT EXISTS idx_event_processing_consumidor ON auditoria_event_processing(consumidor);

-- =============================================================================
-- 4. Sagas (Transacciones Distribuidas Persistentes)
-- =============================================================================
CREATE TABLE IF NOT EXISTS auditoria_sagas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    saga_id TEXT UNIQUE NOT NULL,              -- UUID de la saga
    nombre TEXT NOT NULL,                      -- Nombre descriptivo (ej. 'VentaCompleta')
    estado TEXT NOT NULL CHECK (estado IN ('INICIADA', 'EN_PROCESO', 'COMPLETADA', 'COMPENSADA', 'ERROR_DE_COMPENSACION')),
    paso_actual INTEGER DEFAULT 0,             -- Último paso completado (secuencia)
    payload JSON NOT NULL,                     -- Datos de entrada originales
    contexto JSON,                             -- Estado acumulado de los pasos
    error TEXT,                                -- Mensaje de error si aplica
    creado_en INTEGER NOT NULL,
    actualizado_en INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sagas_estado ON auditoria_sagas(estado);
CREATE INDEX IF NOT EXISTS idx_sagas_nombre ON auditoria_sagas(nombre);
CREATE INDEX IF NOT EXISTS idx_sagas_actualizado ON auditoria_sagas(actualizado_en);

-- =============================================================================
-- 5. Bitácora de Auditoría (Log de Acciones Críticas del Sistema)
-- =============================================================================
CREATE TABLE IF NOT EXISTS auditoria_bitacora (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT NOT NULL,                     -- Usuario que realizó la acción
    accion TEXT NOT NULL,                      -- Tipo de acción (ej. 'LOGIN', 'REGISTRO', 'CIERRE_PERIODO')
    detalle JSON,                              -- Detalles adicionales
    ip TEXT,                                   -- Dirección IP (si aplica)
    timestamp INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_bitacora_usuario ON auditoria_bitacora(usuario);
CREATE INDEX IF NOT EXISTS idx_bitacora_accion ON auditoria_bitacora(accion);
CREATE INDEX IF NOT EXISTS idx_bitacora_timestamp ON auditoria_bitacora(timestamp);

-- =============================================================================
-- Fin de migración 002
-- =============================================================================
