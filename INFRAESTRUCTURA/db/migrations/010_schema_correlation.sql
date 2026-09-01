-- =============================================================================
-- SCFV v6.1 — Migración 010: Añadir correlation_id a auditoria_event_store
-- Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
-- Fecha: 2026-08-30
-- Propósito: Añadir campo correlation_id para trazabilidad genealógica.
-- =============================================================================

-- 1. Añadir columna correlation_id (puede ser NULL para eventos antiguos)
ALTER TABLE auditoria_event_store ADD COLUMN correlation_id TEXT;

-- 2. Crear índice para búsquedas genealógicas
CREATE INDEX idx_auditoria_correlation ON auditoria_event_store(correlation_id);

-- 3. (Opcional) Para eventos futuros, se recomienda NOT NULL,
--    pero se deja como TEXT sin restricción para compatibilidad.
