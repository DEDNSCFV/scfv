<!--
SCFV v6 — Documento de Ingeniería
Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
Versión: 1.0.0
Fecha: 2026-08-26
Estado: APROBADO
ADR relacionados: ADR-001, ADR-002
-->

# Esquema: negocio_pcu (Plan de Cuentas Único)

## Propósito
Almacena el catálogo de cuentas contable del mandante. Es versionado para permitir cambios normativos sin afectar asientos históricos.

## Tabla

```sql
CREATE TABLE negocio_pcu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT NOT NULL,                     -- Versión del PCU (ej. "2024-01", "2025-06")
    codigo TEXT NOT NULL,                      -- Código de la cuenta (ej. "110101")
    nombre TEXT NOT NULL,                      -- Nombre de la cuenta
    naturaleza TEXT NOT NULL,                  -- 'DEUDORA' o 'ACREEDORA'
    nivel INTEGER NOT NULL,                    -- Nivel jerárquico (1, 2, 3, ...)
    padre_codigo TEXT,                         -- Código de la cuenta padre (NULL si es raíz)
    activa BOOLEAN DEFAULT 1,                  -- 1 = activa, 0 = desactivada
    creado_en INTEGER NOT NULL,                -- Timestamp de creación
    UNIQUE(version, codigo)
);

CREATE INDEX idx_pcu_version ON negocio_pcu(version);
CREATE INDEX idx_pcu_codigo ON negocio_pcu(codigo);
CREATE INDEX idx_pcu_padre ON negocio_pcu(padre_codigo);

-- Ejemplo: Nueva versión con cambios normativos
INSERT INTO negocio_pcu (version, codigo, nombre, naturaleza, nivel, padre_codigo)
SELECT '2025-01', codigo, nombre, naturaleza, nivel, padre_codigo
FROM negocio_pcu
WHERE version = '2024-01';
