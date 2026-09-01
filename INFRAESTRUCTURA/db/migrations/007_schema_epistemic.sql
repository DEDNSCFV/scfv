-- =============================================================================
-- SCFV v6 — Migración 007: Esquema del Núcleo Epistemológico
-- Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
-- Fecha: 2026-08-26
-- =============================================================================

CREATE TABLE IF NOT EXISTS epistemic_observacion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    observacion_id TEXT UNIQUE NOT NULL,
    evidencia_hash TEXT NOT NULL,
    evidencia_ruta TEXT NOT NULL,
    fecha_extraccion INTEGER NOT NULL,
    tipo_evidencia TEXT NOT NULL,
    entidades TEXT NOT NULL,
    confianza TEXT NOT NULL,
    metadatos TEXT,
    creado_en INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_epistemic_observacion_hash ON epistemic_observacion(evidencia_hash);
CREATE INDEX IF NOT EXISTS idx_epistemic_observacion_fecha ON epistemic_observacion(fecha_extraccion);
