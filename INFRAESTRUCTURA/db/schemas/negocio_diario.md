<!--
SCFV v6 — Documento de Ingeniería
Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
Versión: 1.0.0
Fecha: 2026-08-26
Estado: APROBADO
ADR relacionados: ADR-001, ADR-002
-->

# Esquema: negocio_diario

## Propósito
Almacena el libro Diario. Es la fuente de verdad de todos los asientos contables. Es **append-only**: los asientos no se modifican ni eliminan; solo se revierten con nuevos asientos.

## Tabla

```sql
CREATE TABLE negocio_diario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asiento_id TEXT UNIQUE NOT NULL,          -- Identificador único del asiento (UUID)
    fecha INTEGER NOT NULL,                    -- Timestamp UNIX de la fecha del asiento
    periodo_id TEXT NOT NULL,                  -- Referencia al período contable
    descripcion TEXT NOT NULL,                 -- Descripción del asiento
    total_debe INTEGER NOT NULL,               -- Suma total debe (en céntimos)
    total_haber INTEGER NOT NULL,              -- Suma total haber (en céntimos)
    decision_id TEXT NOT NULL,                 -- Referencia a epistemic_decisiones (H₂)
    hash_chain_id INTEGER NOT NULL,            -- Referencia a auditoria_hash_chain
    creado_en INTEGER NOT NULL,                -- Timestamp de creación
    FOREIGN KEY (periodo_id) REFERENCES negocio_periodos(id),
    FOREIGN KEY (decision_id) REFERENCES epistemic_decisiones(id),
    FOREIGN KEY (hash_chain_id) REFERENCES auditoria_hash_chain(id)
);

CREATE INDEX idx_diario_fecha ON negocio_diario(fecha);
CREATE INDEX idx_diario_periodo ON negocio_diario(periodo_id);
CREATE INDEX idx_diario_decision ON negocio_diario(decision_id);
