-- =============================================================================
-- SCFV v6.1 — Migración 011: Versionado de Contexto
-- Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
-- Fecha: 2026-08-30
-- Propósito: Añadir tabla de versiones de contexto y columna version_contexto
--            a event_store para reproducibilidad histórica (I10).
-- =============================================================================

-- 1. Crear tabla de versiones de contexto
CREATE TABLE IF NOT EXISTS negocio_contextos (
    version_id TEXT PRIMARY KEY,
    fecha_inicio TEXT NOT NULL,
    fecha_fin TEXT,
    PCU_version TEXT NOT NULL,
    reglas_version TEXT NOT NULL,
    politica_inventario_version TEXT NOT NULL,
    marco_contable_version TEXT NOT NULL,
    politica_monetaria_version TEXT NOT NULL,
    creado_en INTEGER NOT NULL
);

-- 2. Insertar versión inicial (v1)
INSERT OR IGNORE INTO negocio_contextos (
    version_id, fecha_inicio, fecha_fin,
    PCU_version, reglas_version,
    politica_inventario_version, marco_contable_version,
    politica_monetaria_version, creado_en
) VALUES (
    'V1', '2026-01-01', NULL,
    'PCU-2024', 'REG-2024',
    'INV-2024', 'NIC1-2024',
    'MON-2024', strftime('%s', 'now')
);

-- 3. Añadir columna version_contexto a event_store (si no existe)
--    Nota: En la práctica, la nueva tabla ya la tiene, pero por compatibilidad:
ALTER TABLE event_store ADD COLUMN version_contexto TEXT DEFAULT 'V1';

-- 4. Índice para version_contexto (opcional)
CREATE INDEX IF NOT EXISTS idx_version_contexto ON event_store(version_contexto);
