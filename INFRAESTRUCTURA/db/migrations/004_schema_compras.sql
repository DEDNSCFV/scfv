-- =============================================================================
-- SCFV v6 — Migración 004: Esquema del Fractal de Compras
-- Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
-- Fecha: 2026-08-26
-- =============================================================================

-- Tabla principal de compras
CREATE TABLE IF NOT EXISTS negocio_compras (
    id TEXT PRIMARY KEY,
    proveedor_id TEXT NOT NULL,
    fecha INTEGER NOT NULL,
    total_bruto INTEGER DEFAULT 0,
    total_iva INTEGER DEFAULT 0,
    total_descuento INTEGER DEFAULT 0,
    total_neto INTEGER DEFAULT 0,
    estado TEXT NOT NULL CHECK (estado IN ('BORRADOR', 'DOCUMENTADA', 'VALIDADA', 'CONFIRMADA', 'CONTABILIZADA', 'ANULADA')),
    evidencia_hash TEXT NOT NULL,
    creado_en INTEGER NOT NULL,
    actualizado_en INTEGER NOT NULL
);

-- Detalle de compras (líneas)
CREATE TABLE IF NOT EXISTS negocio_compras_detalle (
    id TEXT PRIMARY KEY,
    compra_id TEXT NOT NULL,
    producto_codigo TEXT NOT NULL,
    cantidad INTEGER NOT NULL,
    precio_unitario INTEGER NOT NULL,
    descuento_linea INTEGER DEFAULT 0,
    total_linea INTEGER NOT NULL,
    FOREIGN KEY (compra_id) REFERENCES negocio_compras(id) ON DELETE CASCADE
);

-- Índices para compras
CREATE INDEX IF NOT EXISTS idx_compras_estado ON negocio_compras(estado);
CREATE INDEX IF NOT EXISTS idx_compras_fecha ON negocio_compras(fecha);
CREATE INDEX IF NOT EXISTS idx_compras_proveedor ON negocio_compras(proveedor_id);
CREATE INDEX IF NOT EXISTS idx_compras_detalle_compra ON negocio_compras_detalle(compra_id);
