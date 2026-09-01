-- =============================================================================
-- SCFV v6.2 — Migración 012: Contexto Versionado
-- Autor: Domingo E. Díaz N.
-- Fecha: 2026-08-30
-- =============================================================================

CREATE TABLE IF NOT EXISTS contexto_version (
    version_id TEXT PRIMARY KEY,
    fecha_activacion INTEGER NOT NULL,
    fecha_fin INTEGER,
    pcu_hash TEXT NOT NULL,
    reglas_hash TEXT NOT NULL,
    parametros_sector TEXT,  -- JSON
    creado_en INTEGER NOT NULL,
    activo INTEGER DEFAULT 1
);

CREATE INDEX idx_contexto_activo ON contexto_version(activo);
