<!--
SCFV v6 — Documento de Ingeniería
Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
Versión: 1.0.0
Fecha: 2026-08-26
Estado: APROBADO
ADR relacionados: ADR-001, ADR-002
-->

# Esquema: auditoria_hash_chain

## Propósito
Almacena la cadena de hash que garantiza la inmutabilidad de todos los registros del sistema. Es **append-only**: cada nuevo registro apunta al hash del registro anterior. Cualquier alteración posterior rompe la cadena.

## Tabla

```sql
CREATE TABLE auditoria_hash_chain (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tabla_origen TEXT NOT NULL,                -- Tabla que se está registrando (ej. 'negocio_diario')
    registro_id TEXT NOT NULL,                 -- ID único del registro en esa tabla
    datos_hash TEXT NOT NULL,                  -- SHA-256 de los datos del registro (JSON)
    hash_previo TEXT NOT NULL,                 -- SHA-256 del registro anterior en la cadena
    hash_actual TEXT NOT NULL,                 -- SHA-256(datos_hash + hash_previo)
    creado_en INTEGER NOT NULL,                -- Timestamp de creación
    UNIQUE(tabla_origen, registro_id)
);

CREATE INDEX idx_hash_chain_tabla ON auditoria_hash_chain(tabla_origen);
CREATE INDEX idx_hash_chain_registro ON auditoria_hash_chain(registro_id);

t-- Verificar que cada hash_actual coincide con el cálculo
SELECT 
    id,
    tabla_origen,
    registro_id,
    hash_actual,
    SHA256(datos_hash || hash_previo) AS hash_recalculado
FROM auditoria_hash_chain
WHERE hash_actual != SHA256(datos_hash || hash_previo);
