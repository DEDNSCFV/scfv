-- Tabla de monedas soportadas
CREATE TABLE IF NOT EXISTS negocio_monedas (
    codigo TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    simbolo TEXT
);

-- Tabla de tasas de cambio históricas
CREATE TABLE IF NOT EXISTS negocio_tasas_cambio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    moneda_origen TEXT NOT NULL,
    moneda_destino TEXT NOT NULL DEFAULT 'VES',
    tasa REAL NOT NULL,
    fecha_valor DATE NOT NULL,
    fecha_obtencion DATETIME DEFAULT CURRENT_TIMESTAMP,
    fuente TEXT DEFAULT 'BCV',
    UNIQUE(moneda_origen, moneda_destino, fecha_valor)
);

-- Índices para consultas rápidas
CREATE INDEX idx_tasas_fecha ON negocio_tasas_cambio(fecha_valor);
CREATE INDEX idx_tasas_moneda ON negocio_tasas_cambio(moneda_origen);

-- Insertar monedas base
INSERT OR IGNORE INTO negocio_monedas (codigo, nombre, simbolo) VALUES
    ('VES', 'Bolívar Venezolano', 'Bs.'),
    ('USD', 'Dólar Estadounidense', '$'),
    ('EUR', 'Euro', '€'),
    ('CNY', 'Yuan Chino', '¥'),
    ('TRY', 'Lira Turca', '₺'),
    ('RUB', 'Rublo Ruso', '₽');
