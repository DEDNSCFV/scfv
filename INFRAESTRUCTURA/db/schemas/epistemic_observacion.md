<!--
SCFV v6 — Documento de Ingeniería
Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
Versión: 1.0.0
Fecha: 2026-08-26
Estado: APROBADO
ADR relacionados: ADR-001, ADR-002, ADR-004
-->

# Esquema: epistemic_observacion

## Propósito
Almacena las observaciones generadas por el Perceptum a partir de una evidencia. Cada observación es la representación estructurada de lo que el sistema "ve" en la evidencia, con un nivel de confianza por campo. Es la base para la interpretación del Intellectus.

## Tabla

```sql
CREATE TABLE epistemic_observacion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    observacion_id TEXT UNIQUE NOT NULL,       -- Identificador único (UUID)
    evidencia_hash TEXT NOT NULL,              -- Hash SHA-256 de la evidencia procesada
    evidencia_ruta TEXT NOT NULL,              -- Ruta al archivo de evidencia
    fecha_extraccion INTEGER NOT NULL,         -- Timestamp de extracción
    tipo_evidencia TEXT NOT NULL,              -- 'PDF', 'XML', 'IMAGEN', 'TEXTO', 'MANUSCRITO', 'CSV'
    entidades JSON NOT NULL,                   -- JSON con los datos extraídos: montos, fechas, RIF, productos, etc.
    confianza JSON NOT NULL,                   -- JSON con confianza por campo (0.0 - 1.0)
    metadatos JSON,                            -- Metadatos adicionales (OCR usado, resolución, etc.)
    creado_en INTEGER NOT NULL,                -- Timestamp de creación
    FOREIGN KEY (evidencia_hash) REFERENCES auditoria_hash_chain(datos_hash) ON DELETE RESTRICT
);

CREATE INDEX idx_observacion_evidencia ON epistemic_observacion(evidencia_hash);
CREATE INDEX idx_observacion_fecha ON epistemic_observacion(fecha_extraccion);

{
    "fecha": "2026-08-25",
    "monto": 10000,
    "moneda": "USD",
    "rif_emisor": "J-123456789",
    "rif_receptor": "J-987654321",
    "productos": ["Harina x10"],
    "descripcion": "Compra de harina al crédito",
    "tasa_cambio": 40.50
}

{
    "fecha": 0.95,
    "monto": 0.99,
    "moneda": 0.85,
    "rif_emisor": 0.70,
    "rif_receptor": 0.60,
    "productos": 0.80,
    "descripcion": 0.75,
    "tasa_cambio": 0.90
}


