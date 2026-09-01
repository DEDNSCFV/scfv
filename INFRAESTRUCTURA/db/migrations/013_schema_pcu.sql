-- =============================================================================
-- SCFV v6.2 — Migración 013: Plan de Cuentas Único (PCU)
-- Autor: Domingo E. Díaz N.
-- Fecha: 2026-08-30
-- =============================================================================

CREATE TABLE IF NOT EXISTS negocio_pcu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT NOT NULL,
    codigo TEXT NOT NULL,
    nombre TEXT NOT NULL,
    naturaleza TEXT NOT NULL,  -- 'DEUDORA' o 'ACREEDORA'
    nivel INTEGER NOT NULL,
    padre_codigo TEXT,
    activa INTEGER DEFAULT 1,
    creado_en INTEGER NOT NULL,
    UNIQUE(version, codigo)
);

CREATE INDEX idx_pcu_version ON negocio_pcu(version);
CREATE INDEX idx_pcu_codigo ON negocio_pcu(codigo);
