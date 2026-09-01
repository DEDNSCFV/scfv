<!--
SCFV v6 — Documento de Ingeniería
Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
Versión: 1.0.0
Fecha: 2026-08-26
Estado: APROBADO
ADR relacionados: ADR-001, ADR-002
-->

# Esquema: negocio_mayor

## Propósito
Almacena el libro Mayor. Es una **proyección derivada** del Diario, no una fuente de verdad primaria. Se actualiza cada vez que se inserta un asiento en `negocio_diario`.

## Tabla

```sql
CREATE TABLE negocio_mayor (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cuenta_id TEXT NOT NULL,                   -- Referencia a negocio_cuentas (código de cuenta)
    periodo_id TEXT NOT NULL,                  -- Período contable
    saldo_debe INTEGER DEFAULT 0,              -- Saldo acumulado DEBE (en céntimos)
    saldo_haber INTEGER DEFAULT 0,             -- Saldo acumulado HABER (en céntimos)
    saldo_neto INTEGER DEFAULT 0,              -- Saldo neto (DEBE - HABER) para cuentas deudoras, o (HABER - DEBE) para acreedoras
    ultimo_asiento_id TEXT,                    -- ID del último asiento que afectó esta cuenta
    actualizado_en INTEGER NOT NULL,           -- Timestamp de última actualización
    FOREIGN KEY (cuenta_id) REFERENCES negocio_cuentas(codigo),
    FOREIGN KEY (periodo_id) REFERENCES negocio_periodos(id)
);

CREATE INDEX idx_mayor_cuenta_periodo ON negocio_mayor(cuenta_id, periodo_id);
CREATE INDEX idx_mayor_periodo ON negocio_mayor(periodo_id);

-- Reconstrucción del Mayor desde el Diario
SELECT 
    p.cuenta_id,
    d.periodo_id,
    SUM(CASE WHEN p.ubicacion = 'DEBE' THEN p.monto ELSE 0 END) AS saldo_debe,
    SUM(CASE WHEN p.ubicacion = 'HABER' THEN p.monto ELSE 0 END) AS saldo_haber
FROM negocio_partidas p
JOIN negocio_diario d ON p.asiento_id = d.asiento_id
GROUP BY p.cuenta_id, d.periodo_id;
