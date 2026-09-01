<!--
SCFV v6 — Documento de Ingeniería
Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
Versión: 1.0.0
Fecha: 2026-08-26
Estado: APROBADO
ADR relacionados: ADR-001, ADR-002, ADR-003
-->

# Auditoría — Autoridad Demostrativa

## Propósito
La Auditoría es la **Autoridad Demostrativa** del SCFV v6. Su responsabilidad es reconstruir y demostrar la **cadena causal** y la **cadena de justificación** de cualquier operación, desde el saldo final hasta la evidencia original, y desde la evidencia hasta la decisión del contador y el asiento resultante.

**La Auditoría nunca modifica datos históricos. Solo lee, reconstruye y demuestra.**

## Autoridad (ADR-001)
- **Demostrativa**: reconstruye y demuestra, no modifica.
- **Nunca** escribe en `negocio_*` ni en `epistemic_*`. Solo escribe en `auditoria_hash_chain`, `auditoria_event_store`, `auditoria_event_processing`, `auditoria_sagas`, `auditoria_bitacora`.
- **Nunca** modifica datos históricos (append-only).

## Responsabilidades

| Responsabilidad | Descripción |
|-----------------|-------------|
| **Mantener la Hash Chain** | Registro append-only con SHA-256 encadenado para garantizar inmutabilidad. |
| **Reconstruir la Cadena Causal** | Saldo → Partida → Asiento → Evento → Hecho → Evidencia. |
| **Reconstruir la Cadena de Justificación** | Evidencia → Observación → Interpretación → Sugerencia → Decisión → Asiento. |
| **Exportar Paquete de Auditoría** | Generar un paquete exportable para auditoría externa (Diario, Mayor, Hash Chain, Decisiones, Evidencias). |
| **Verificar Integridad** | Validar que la hash chain no esté rota y que los datos sean consistentes. |

## Invariantes

| ID | Invariante | Verificación |
|----|------------|--------------|
| I-1 | `hash_actual = SHA-256(datos_hash + hash_previo)` | Siempre se cumple. |
| I-2 | La hash chain es append-only | Ningún registro se actualiza ni elimina. |
| I-3 | La Auditoría nunca escribe en `negocio_*` | Restricción de acceso por diseño. |
| I-4 | La Auditoría nunca escribe en `epistemic_*` | Restricción de acceso por diseño. |

## Entradas
- **Evento**: cualquier evento publicado al Bus (`auditoria_event_store`).
- **Asiento**: cuando el Motor Contable registra un asiento.
- **Decisión Profesional**: cuando el contador toma una decisión.
- **Observación**: cuando el Perceptum extrae una observación.
- **Evidencia**: cuando se carga un archivo de evidencia.

## Salidas
- **Hash Chain**: registro en `auditoria_hash_chain` con hash encadenado.
- **Paquete de Auditoría**: archivo exportable (JSON, CSV) para auditoría externa.
- **Reconstrucción**: cadenas causales y de justificación completas.

## Dependencias

### Permitidas
- `db/repositories/auditoria_hash_chain.py`: para escribir y leer la hash chain.
- `db/repositories/auditoria_event_store.py`: para leer eventos.
- `db/repositories/auditoria_sagas.py`: para leer Sagas.
- `db/repositories/negocio_diario.py`: para leer el Diario.
- `db/repositories/negocio_partidas.py`: para leer partidas.
- `db/repositories/negocio_mayor.py`: para leer el Mayor.
- `db/repositories/epistemic_decisiones.py`: para leer decisiones.
- `db/repositories/epistemic_observacion.py`: para leer observaciones.
- `db/repositories/epistemic_proposicion.py`: para leer proposiciones.
- `db/repositories/epistemic_orientacion.py`: para leer orientaciones.

### Prohibidas
- Cualquier módulo de `core/motor_contable/` (no escribe en Diario).
- Cualquier fractal de dominio (Ventas, Compras, etc.).
- Cualquier módulo de `epistemic/` (no modifica datos del Núcleo).

## Componentes Internos

| Componente | Responsabilidad |
|------------|-----------------|
| **Hash Chain Writer** | Escribe registros en `auditoria_hash_chain` (append-only). |
| **Hash Verifier** | Verifica que la cadena no esté rota. |
| **Reconstructor Causal** | Reconstruye: Saldo → Partida → Asiento → Evento → Hecho → Evidencia. |
| **Reconstructor de Justificación** | Reconstruye: Evidencia → Observación → Interpretación → Sugerencia → Decisión → Asiento. |
| **Exportador de Auditoría** | Genera paquete exportable para auditoría externa. |
| **Validador de Integridad** | Verifica que la hash chain y los datos sean consistentes. |

## Pseudo-código de Funciones Principales

### 1. `escribir_hash_chain(tabla_origen: str, registro_id: str, datos: dict) -> int`

```python
# PRE: tabla_origen y registro_id identifican unívocamente el registro
# POST: retorna el ID del nuevo registro en auditoria_hash_chain
# INVARIANTE: hash_actual = SHA-256(datos_hash + hash_previo)
def escribir_hash_chain(tabla_origen, registro_id, datos):
    # 1. Serializar datos a JSON
    datos_str = json.dumps(datos, sort_keys=True)
    datos_hash = hashlib.sha256(datos_str.encode('utf-8')).hexdigest()
    
    # 2. Obtener el último hash de la cadena para esta tabla
    hash_previo = obtener_ultimo_hash(tabla_origen)
    
    # 3. Calcular hash_actual
    hash_actual = hashlib.sha256(
        (datos_hash + hash_previo).encode('utf-8')
    ).hexdigest()
    
    # 4. Insertar en auditoria_hash_chain
    registro = {
        'tabla_origen': tabla_origen,
        'registro_id': registro_id,
        'datos_hash': datos_hash,
        'hash_previo': hash_previo,
        'hash_actual': hash_actual,
        'creado_en': timestamp_actual()
    }
    id = insertar_hash_chain(registro)
    
    return id

# PRE: desde_id es opcional (si no se da, verifica toda la cadena)
# POST: retorna True si la cadena es válida, False si está rota
# INVARIANTE: cada hash_actual debe coincidir con el cálculo
def verificar_integridad(desde_id=None):
    registros = obtener_hash_chain(desde_id)
    
    for i, registro in enumerate(registros):
        # Recalcular hash_actual
        hash_recalculado = hashlib.sha256(
            (registro.datos_hash + registro.hash_previo).encode('utf-8')
        ).hexdigest()
        
        if registro.hash_actual != hash_recalculado:
            return False
        
        # Si no es el primero, verificar que hash_previo coincide con el anterior
        if i > 0:
            if registro.hash_previo != registros[i-1].hash_actual:
                return False
    
    return True

# PRE: asiento_id existe en negocio_diario
# POST: retorna un diccionario con la cadena causal completa
# INVARIANTE: todos los enlaces existen y son válidos
def reconstruir_causal(asiento_id):
    # 1. Obtener asiento
    asiento = obtener_asiento(asiento_id)
    
    # 2. Obtener partidas
    partidas = obtener_partidas(asiento_id)
    
    # 3. Obtener eventos relacionados con este asiento
    eventos = obtener_eventos_por_asiento(asiento_id)
    
    # 4. Obtener el hecho (decisión) que originó el asiento
    decision = obtener_decision(asiento.decision_id)
    
    # 5. Obtener la evidencia original
    evidencia = obtener_evidencia_por_hash(decision.evidencia_hash)
    
    # 6. Construir la cadena
    cadena = {
        'asiento': asiento,
        'partidas': partidas,
        'eventos': eventos,
        'decision': decision,
        'evidencia': evidencia,
        'saldo_final': calcular_saldo_final(asiento.periodo_id, asiento_id)
    }
    
    return cadena

# PRE: asiento_id existe en negocio_diario
# POST: retorna un diccionario con la cadena de justificación completa
# INVARIANTE: todos los enlaces existen y son válidos
def reconstruir_justificacion(asiento_id):
    # 1. Obtener asiento
    asiento = obtener_asiento(asiento_id)
    
    # 2. Obtener decisión profesional
    decision = obtener_decision(asiento.decision_id)
    
    # 3. Obtener orientación (si existió)
    orientacion = obtener_orientacion_por_decision(decision.id) if decision.orientacion_id else None
    
    # 4. Obtener proposición (si existió)
    proposicion = obtener_proposicion(orientacion.proposicion_id) if orientacion else None
    
    # 5. Obtener observación
    observacion = obtener_observacion(proposicion.observacion_id) if proposicion else None
    
    # 6. Obtener evidencia
    evidencia = obtener_evidencia_por_hash(decision.evidencia_hash)
    
    # 7. Construir la cadena
    cadena = {
        'evidencia': evidencia,
        'observacion': observacion,
        'proposicion': proposicion,
        'orientacion': orientacion,
        'decision': decision,
        'asiento': asiento
    }
    
    return cadena

# PRE: periodo_id existe en negocio_periodos
# POST: retorna un archivo ZIP con el paquete de auditoría
def exportar_paquete(periodo_id, mandante):
    # 1. Obtener Diario del período
    diario = obtener_diario_por_periodo(periodo_id)
    
    # 2. Obtener Mayor del período
    mayor = obtener_mayor_por_periodo(periodo_id)
    
    # 3. Obtener hash chain completa
    hash_chain = obtener_hash_chain_completa()
    
    # 4. Obtener decisiones profesionales del período
    decisiones = obtener_decisiones_por_periodo(periodo_id)
    
    # 5. Obtener evidencias (rutas)
    evidencias = obtener_evidencias_por_periodo(periodo_id)
    
    # 6. Construir archivo ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f'{mandante}_diario_{periodo_id}.csv', diario.to_csv())
        zf.writestr(f'{mandante}_mayor_{periodo_id}.csv', mayor.to_csv())
        zf.writestr(f'{mandante}_hash_chain_{periodo_id}.json', json.dumps(hash_chain, indent=2))
        zf.writestr(f'{mandante}_decisiones_{periodo_id}.json', json.dumps(decisiones, indent=2))
        zf.writestr(f'{mandante}_evidencias_{periodo_id}.json', json.dumps(evidencias, indent=2))
        
        # Incluir archivos de evidencia (opcional)
        for evidencia in evidencias:
            zf.write(evidencia.ruta, f'evidencias/{evidencia.nombre}')
    
    return zip_buffer.getvalue()

Saldo Final
    ↑
Partida
    ↑
Asiento
    ↑
Evento
    ↑
Hecho Económico
    ↑
Evidencia (hash)

Evidencia (hash)
    ↓
Observación (extraída por Perceptum)
    ↓
Interpretación (proposición con r, s, o, t, v)
    ↓
Orientación (sugerencia del Dictum)
    ↓
Decisión Profesional (del contador)
    ↓
Asiento (generado por el Motor Contable)


