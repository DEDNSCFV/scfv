-- =============================================================================
-- SCFV v6 — Migración 005: Esquema del Fractal de Inventario
-- Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
-- Fecha: 2026-08-26
-- =============================================================================

-- Tabla de productos
CREATE TABLE IF NOT EXISTS negocio_productos (
    codigo TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    unidad_medida TEXT NOT NULL,
    precio_compra INTEGER DEFAULT 0,
    precio_venta INTEGER DEFAULT 0,
    stock_actual INTEGER DEFAULT 0,
    costo_promedio INTEGER DEFAULT 0,
    activo INTEGER DEFAULT 1,
    creado_en INTEGER NOT NULL,
    actualizado_en INTEGER NOT NULL
);

-- Tabla de movimientos de inventario
CREATE TABLE IF NOT EXISTS negocio_inventario_movimientos (
    id TEXT PRIMARY KEY,
    producto_codigo TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('ENTRADA', 'SALIDA', 'AJUSTE')),
    cantidad INTEGER NOT NULL,
    costo_unitario INTEGER NOT NULL,
    costo_total INTEGER NOT NULL,
    referencia_id TEXT NOT NULL,      -- ID de la compra o venta que lo originó
    referencia_tipo TEXT NOT NULL,    -- 'COMPRA', 'VENTA', 'AJUSTE'
    fecha INTEGER NOT NULL,
    creado_en INTEGER NOT NULL,
    FOREIGN KEY (producto_codigo) REFERENCES negocio_productos(codigo) ON DELETE RESTRICT
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_inventario_producto ON negocio_inventario_movimientos(producto_codigo);
CREATE INDEX IF NOT EXISTS idx_inventario_fecha ON negocio_inventario_movimientos(fecha);
CREATE INDEX IF NOT EXISTS idx_inventario_referencia ON negocio_inventario_movimientos(referencia_id);
