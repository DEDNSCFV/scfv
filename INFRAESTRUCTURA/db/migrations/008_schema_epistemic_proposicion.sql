-- =============================================================================
-- SCFV v6 — Migración 008: Esquema de Proposiciones
-- Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
-- Fecha: 2026-08-26
-- =============================================================================

CREATE TABLE IF NOT EXISTS epistemic_proposicion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposicion_id TEXT UNIQUE NOT NULL,
    observacion_id TEXT NOT NULL,
    interpretacion TEXT NOT NULL,
    r REAL NOT NULL,
    s REAL NOT NULL,
    o REAL NOT NULL,
    t REAL NOT NULL,
    v REAL NOT NULL,
    evidencia_hash TEXT NOT NULL,
    creado_en INTEGER NOT NULL,
    FOREIGN KEY (observacion_id) REFERENCES epistemic_observacion(observacion_id)
);

CREATE INDEX IF NOT EXISTS idx_epistemic_proposicion_observacion ON epistemic_proposicion(observacion_id);
