-- =============================================================================
-- SCFV v6 — Migración 001: Esquema de Negocio
-- Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
-- Fecha: 2026-08-26
-- Propósito: Crear las tablas del dominio contable y operativo (prefijo negocio_)
-- =============================================================================

-- Habilitar claves foráneas y WAL mode para atomicidad y recuperación
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- =============================================================================
-- 1. PCU (Plan de Cuentas Único) - Versionado
-- =============================================================================
CREATE TABLE IF NOT EXISTS negocio_pcu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT NOT NULL,                     -- Ej. '2024-01', '2025-06'
    codigo TEXT NOT NULL,                      -- Código de cuenta (ej. '110101')
    nombre TEXT NOT NULL,                      -- Nombre de la cuenta
    naturaleza TEXT NOT NULL CHECK (naturaleza IN ('DEUDORA', 'ACREEDORA')),
    nivel INTEGER NOT NULL,                    -- Nivel jerárquico (1,2,3,...)
    padre_codigo TEXT,                         -- Código de la cuenta padre
    activa BOOLEAN DEFAULT 1,
    creado_en INTEGER NOT NULL,                -- Timestamp UNIX
    UNIQUE(version, codigo),
    FOREIGN KEY (version, padre_codigo) REFERENCES negocio_pcu(version, codigo)
);

CREATE INDEX IF NOT EXISTS idx_pcu_version ON negocio_pcu(version);
CREATE INDEX IF NOT EXISTS idx_pcu_codigo ON negocio_pcu(codigo);
CREATE INDEX IF NOT EXISTS idx_pcu_padre ON negocio_pcu(padre_codigo);

-- =============================================================================
-- 2. Períodos Contables
-- =============================================================================
CREATE TABLE IF NOT EXISTS negocio_periodos (
    id TEXT PRIMARY KEY,                       -- Identificador único del período (ej. '2024-01')
    nombre TEXT NOT NULL,                      -- Nombre descriptivo
    fecha_inicio INTEGER NOT NULL,             -- Timestamp UNIX
    fecha_fin INTEGER NOT NULL,                -- Timestamp UNIX
    estado TEXT NOT NULL CHECK (estado IN ('ABIERTO', 'CERRADO', 'BLOQUEADO')),
    creado_en INTEGER NOT NULL,
    cerrado_en INTEGER                         -- Timestamp de cierre (NULL si está abierto)
);

CREATE INDEX IF NOT EXISTS idx_periodos_estado ON negocio_periodos(estado);
CREATE INDEX IF NOT EXISTS idx_periodos_fechas ON negocio_periodos(fecha_inicio, fecha_fin);

-- =============================================================================
-- 3. Diario (Asientos)
-- =============================================================================
CREATE TABLE IF NOT EXISTS negocio_diario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asiento_id TEXT UNIQUE NOT NULL,           -- UUID del asiento
    fecha INTEGER NOT NULL,                    -- Timestamp de la fecha del asiento
    periodo_id TEXT NOT NULL,                  -- Período al que pertenece
    descripcion TEXT NOT NULL,
    total_debe INTEGER NOT NULL,               -- En céntimos
    total_haber INTEGER NOT NULL,              -- En céntimos
    decision_id TEXT NOT NULL,                 -- Referencia a la decisión (epistemic_decisiones)
    hash_chain_id INTEGER NOT NULL,            -- Referencia a auditoria_hash_chain
    creado_en INTEGER NOT NULL,
    FOREIGN KEY (periodo_id) REFERENCES negocio_periodos(id) ON DELETE RESTRICT,
    FOREIGN KEY (decision_id) REFERENCES epistemic_decisiones(id) ON DELETE RESTRICT,
    FOREIGN KEY (hash_chain_id) REFERENCES auditoria_hash_chain(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_diario_fecha ON negocio_diario(fecha);
CREATE INDEX IF NOT EXISTS idx_diario_periodo ON negocio_diario(periodo_id);
CREATE INDEX IF NOT EXISTS idx_diario_decision ON negocio_diario(decision_id);
CREATE INDEX IF NOT EXISTS idx_diario_asiento ON negocio_diario(asiento_id);

-- =============================================================================
-- 4. Partidas (Líneas del Asiento)
-- =============================================================================
CREATE TABLE IF NOT EXISTS negocio_partidas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    partida_id TEXT UNIQUE NOT NULL,           -- UUID de la partida
    asiento_id TEXT NOT NULL,                  -- Referencia al asiento (UUID)
    cuenta_codigo TEXT NOT NULL,               -- Código de cuenta (debe existir en PCU)
    cuenta_version TEXT NOT NULL,              -- Versión del PCU en que se usó
    monto INTEGER NOT NULL,                    -- En céntimos
    ubicacion TEXT NOT NULL CHECK (ubicacion IN ('DEBE', 'HABER')),
    creado_en INTEGER NOT NULL,
    FOREIGN KEY (asiento_id) REFERENCES negocio_diario(asiento_id) ON DELETE CASCADE,
    FOREIGN KEY (cuenta_version, cuenta_codigo) REFERENCES negocio_pcu(version, codigo) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_partidas_asiento ON negocio_partidas(asiento_id);
CREATE INDEX IF NOT EXISTS idx_partidas_cuenta ON negocio_partidas(cuenta_codigo);
CREATE INDEX IF NOT EXISTS idx_partidas_ubicacion ON negocio_partidas(ubicacion);

-- =============================================================================
-- 5. Mayor (Saldos Acumulados por Cuenta y Período)
-- =============================================================================
CREATE TABLE IF NOT EXISTS negocio_mayor (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cuenta_codigo TEXT NOT NULL,
    cuenta_version TEXT NOT NULL,
    periodo_id TEXT NOT NULL,
    saldo_debe INTEGER DEFAULT 0,              -- En céntimos
    saldo_haber INTEGER DEFAULT 0,             -- En céntimos
    saldo_neto INTEGER DEFAULT 0,              -- DEBE - HABER (para deudoras) o HABER - DEBE (para acreedoras)
    ultimo_asiento_id TEXT,                    -- UUID del último asiento que afectó esta cuenta
    actualizado_en INTEGER NOT NULL,
    FOREIGN KEY (cuenta_version, cuenta_codigo) REFERENCES negocio_pcu(version, codigo) ON DELETE RESTRICT,
    FOREIGN KEY (periodo_id) REFERENCES negocio_periodos(id) ON DELETE RESTRICT,
    UNIQUE(cuenta_codigo, cuenta_version, periodo_id)
);

CREATE INDEX IF NOT EXISTS idx_mayor_cuenta_periodo ON negocio_mayor(cuenta_codigo, periodo_id);
CREATE INDEX IF NOT EXISTS idx_mayor_periodo ON negocio_mayor(periodo_id);

-- =============================================================================
-- 6. Trigger de validación de partida doble (opcional, pero deja constancia)
-- =============================================================================
-- Nota: La validación ΣDEBE = ΣHABER se hará a nivel de aplicación
-- (Motor Contable) para tener control explícito y mejor manejo de errores.
-- Este trigger es documental y puede activarse si se desea una capa extra.

-- =============================================================================
-- Fin de migración 001
-- =============================================================================
