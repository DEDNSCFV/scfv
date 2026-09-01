-- =============================================================================
-- SCFV v6.2 — Migración 014: Checkpoints para Hash Chain
-- Autor: Domingo E. Díaz N.
-- Fecha: 2026-08-30
-- =============================================================================

CREATE TABLE IF NOT EXISTS checkpoints (
    checkpoint_id TEXT PRIMARY KEY,
    evento_inicial_id TEXT NOT NULL,
    evento_final_id TEXT NOT NULL,
    hash_acumulado TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    firmado_por TEXT,  -- H2 (opcional)
    version_contexto_id TEXT,
    FOREIGN KEY (version_contexto_id) REFERENCES contexto_version(version_id)
);
