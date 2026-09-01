-- =============================================================================
-- SCFV v6 — Migración 009: Esquema de Orientaciones
-- Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
-- Fecha: 2026-08-26
-- =============================================================================

CREATE TABLE IF NOT EXISTS epistemic_orientacion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    orientacion_id TEXT UNIQUE NOT NULL,
    tipo TEXT NOT NULL,
    severidad TEXT NOT NULL,
    mensaje TEXT NOT NULL,
    datos_soporte TEXT NOT NULL,
    accion_sugerida TEXT NOT NULL,
    requiere_respuesta INTEGER DEFAULT 1,
    proposicion_id TEXT NOT NULL,
    evidencia_hash TEXT NOT NULL,
    creado_en INTEGER NOT NULL,
    FOREIGN KEY (proposicion_id) REFERENCES epistemic_proposicion(proposicion_id)
);

CREATE INDEX IF NOT EXISTS idx_epistemic_orientacion_proposicion ON epistemic_orientacion(proposicion_id);
