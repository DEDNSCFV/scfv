-- =============================================================================
-- SCFV v6 — Migración 003: Esquema del Fractal de Ventas
-- Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
-- Fecha: 2026-08-26
-- =============================================================================

-- Tabla principal de ventas
CREATE TABLE IF NOT EXISTS negocio_ventas (
    id TEXT PRIMARY KEY,
    cliente_id TEXT NOT NULL,
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

-- Detalle de ventas (líneas)
CREATE TABLE IF NOT EXISTS negocio_ventas_detalle (
    id TEXT PRIMARY KEY,
    venta_id TEXT NOT NULL,
    producto_codigo TEXT NOT NULL,
    cantidad INTEGER NOT NULL,
    precio_unitario INTEGER NOT NULL,
    descuento_linea INTEGER DEFAULT 0,
    total_linea INTEGER NOT NULL,
    FOREIGN KEY (venta_id) REFERENCES negocio_ventas(id) ON DELETE CASCADE
);

-- Índices para ventas
CREATE INDEX IF NOT EXISTS idx_ventas_estado ON negocio_ventas(estado);
CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON negocio_ventas(fecha);
CREATE INDEX IF NOT EXISTS idx_ventas_cliente ON negocio_ventas(cliente_id);
CREATE INDEX IF NOT EXISTS idx_ventas_detalle_venta ON negocio_ventas_detalle(venta_id);
