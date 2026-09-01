-- =============================================================================
-- SCFV v6 — Migración 006: Esquema del Fractal de Fiscal
-- Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
-- Fecha: 2026-08-26
-- =============================================================================

-- Tabla de configuración de impuestos (tasas vigentes por período)
CREATE TABLE IF NOT EXISTS negocio_fiscal_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    periodo_id TEXT NOT NULL,
    impuesto TEXT NOT NULL CHECK (impuesto IN ('IVA', 'ISLR', 'RETENCION_IVA', 'RETENCION_ISLR', 'OTRO')),
    tasa INTEGER NOT NULL,                -- En base 10000 (ej. 16% = 1600)
    aplica_compra INTEGER DEFAULT 1,      -- 1: aplica a compras, 0: no
    aplica_venta INTEGER DEFAULT 1,       -- 1: aplica a ventas, 0: no
    activo INTEGER DEFAULT 1,
    creado_en INTEGER NOT NULL,
    UNIQUE(periodo_id, impuesto)
);

-- Tabla de declaraciones fiscales (periódicas)
CREATE TABLE IF NOT EXISTS negocio_fiscal_declaraciones (
    id TEXT PRIMARY KEY,
    periodo_id TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('IVA', 'ISLR', 'RETENCIONES')),
    fecha_inicio INTEGER NOT NULL,
    fecha_fin INTEGER NOT NULL,
    total_debito INTEGER DEFAULT 0,       -- IVA débito fiscal (ventas)
    total_credito INTEGER DEFAULT 0,      -- IVA crédito fiscal (compras)
    total_retenciones INTEGER DEFAULT 0,  -- Retenciones practicadas
    saldo_a_pagar INTEGER DEFAULT 0,     -- Total a pagar (débito - crédito + retenciones)
    estado TEXT NOT NULL CHECK (estado IN ('BORRADOR', 'CALCULADA', 'PRESENTADA', 'PAGADA')),
    creado_en INTEGER NOT NULL,
    actualizado_en INTEGER NOT NULL
);

-- Tabla de retenciones practicadas
CREATE TABLE IF NOT EXISTS negocio_fiscal_retenciones (
    id TEXT PRIMARY KEY,
    declaracion_id TEXT NOT NULL,
    tercero_id TEXT NOT NULL,            -- RIF del sujeto retenido
    tipo TEXT NOT NULL CHECK (tipo IN ('IVA', 'ISLR')),
    base_imponible INTEGER NOT NULL,
    tasa INTEGER NOT NULL,               -- En base 10000
    monto_retenido INTEGER NOT NULL,
    fecha INTEGER NOT NULL,
    referencia_id TEXT NOT NULL,         -- ID de la compra o venta
    referencia_tipo TEXT NOT NULL,       -- 'COMPRA', 'VENTA'
    creado_en INTEGER NOT NULL,
    FOREIGN KEY (declaracion_id) REFERENCES negocio_fiscal_declaraciones(id)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_fiscal_config_periodo ON negocio_fiscal_config(periodo_id);
CREATE INDEX IF NOT EXISTS idx_fiscal_declaraciones_periodo ON negocio_fiscal_declaraciones(periodo_id);
CREATE INDEX IF NOT EXISTS idx_fiscal_retenciones_declaracion ON negocio_fiscal_retenciones(declaracion_id);
CREATE INDEX IF NOT EXISTS idx_fiscal_retenciones_tercero ON negocio_fiscal_retenciones(tercero_id);
