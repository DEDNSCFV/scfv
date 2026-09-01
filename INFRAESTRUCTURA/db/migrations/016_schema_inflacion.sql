-- Tabla de factores de inflación (IPC mensual)
CREATE TABLE IF NOT EXISTS negocio_inflacion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha DATE NOT NULL UNIQUE,
    factor REAL NOT NULL,          -- Factor acumulado desde base (ej. 1.15 = 15% inflación)
    ipc REAL NOT NULL,             -- Índice de Precios al Consumidor (base = 100)
    fuente TEXT DEFAULT 'BCV',
    fecha_obtencion DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de saldos reexpresados (para trazabilidad)
CREATE TABLE IF NOT EXISTS negocio_saldos_reexpresados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cuenta TEXT NOT NULL,
    fecha_original DATE NOT NULL,
    saldo_original REAL NOT NULL,
    factor_reexpresion REAL NOT NULL,
    saldo_reexpresado REAL NOT NULL,
    fecha_reexpresion DATE NOT NULL,
    periodo TEXT NOT NULL,
    FOREIGN KEY (cuenta) REFERENCES negocio_pcu(codigo)
);

CREATE INDEX idx_inflacion_fecha ON negocio_inflacion(fecha);
CREATE INDEX idx_reexpresados_periodo ON negocio_saldos_reexpresados(periodo);
