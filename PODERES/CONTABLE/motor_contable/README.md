<!--
SCFV v6 — Documento de Ingeniería
Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
Versión: 1.0.0
Fecha: 2026-08-26
Estado: APROBADO
ADR relacionados: ADR-001, ADR-002, ADR-003
-->

# Motor Contable

## Propósito
El Motor Contable es la **única autoridad de escritura** en el Diario y el Mayor. Recibe una `DecisionProfesional` (H₂) estructurada y genera un asiento de N partidas, validando las invariantes contables antes de persistir.

## Autoridad (ADR-001)
- **Contable**: escribe en `negocio_asientos`, `negocio_partidas`, `negocio_mayor`.
- **Nunca** escribe en `epistemic_*` ni `auditoria_*` (solo delega a Auditoría para la hash chain).

## Entradas
- `DecisionProfesional` (H₂): objeto que contiene:
  - `fecha`: fecha del hecho.
  - `periodo_id`: período contable.
  - `descripcion`: texto descriptivo.
  - `partidas`: lista de `{cuenta_codigo, cuenta_version, monto, ubicacion}`.
  - `decision_id`: referencia a la decisión en `epistemic_decisiones`.
  - `evidencia_hash`: hash de la evidencia que respalda la operación.

## Salidas
- `Asiento`: objeto con `asiento_id`, `total_debe`, `total_haber`, `hash_chain_id`.
- Registro persistido en `negocio_diario`, `negocio_partidas`, `negocio_mayor`.
- Evento `ASIENTO_REGISTRADO` publicado al Event Store.

## Invariantes

| ID | Invariante | Verificación |
|----|------------|--------------|
| I-1 | ΣDEBE = ΣHABER | Antes de persistir, suma y compara. Si no es igual, rechazar. |
| I-2 | Cada partida satisface `U = N ⊙ M` | Aplicar el axioma booleano a cada partida. |
| I-3 | El período debe estar ABIERTO | Consultar `negocio_periodos`; si no, rechazar. |
| I-4 | Las cuentas existen en el PCU (versión activa) | Verificar en `negocio_pcu`. |
| I-5 | Un asiento registrado no se modifica (append-only) | Solo se permite insertar; no update/delete. |

## Dependencias

### Permitidas
- `db/connection.py`: para conexión a SQLite.
- `db/repositories/negocio_diario.py`: para escritura en Diario.
- `db/repositories/negocio_partidas.py`: para escritura de partidas.
- `db/repositories/negocio_mayor.py`: para actualización del Mayor.
- `db/repositories/negocio_periodos.py`: para verificar estado del período.
- `db/repositories/negocio_pcu.py`: para validar cuentas.
- `audit/hash_chain.py`: para registrar hash de integridad.
- `orchestrator/event_publisher.py`: para publicar evento `ASIENTO_REGISTRADO`.

### Prohibidas
- Cualquier módulo de `epistemic/` (Perceptum, Intellectus, Dictum).
- Cualquier fractal de dominio (Ventas, Compras, Inventario, etc.).
- Escritura directa en tablas sin pasar por los repositorios.

## Pseudo-código de Funciones Principales

### 1. `validar_partida_doble(partidas) -> bool`

```python
# PRE: partidas es una lista de objetos con 'monto' y 'ubicacion' ('DEBE' o 'HABER')
# POST: retorna True si ΣDEBE == ΣHABER, False en caso contrario
# INVARIANTE: ningún monto es negativo
def validar_partida_doble(partidas):
    total_debe = sum(p.monto for p in partidas if p.ubicacion == 'DEBE')
    total_haber = sum(p.monto for p in partidas if p.ubicacion == 'HABER')
    return total_debe == total_haber

# PRE: cuenta tiene campo 'naturaleza' ('DEUDORA' o 'ACREEDORA')
#      movimiento es 'AUMENTA' o 'DISMINUYE'
# POST: retorna 'DEBE' o 'HABER' según U = N ⊙ M
# INVARIANTE: la cuenta existe en el PCU
def aplicar_axioma_booleano(cuenta, movimiento):
    # Naturaleza: DEUDORA = 1, ACREEDORA = 0
    N = 1 if cuenta.naturaleza == 'DEUDORA' else 0
    # Movimiento: AUMENTA = 1, DISMINUYE = 0
    M = 1 if movimiento == 'AUMENTA' else 0
    # XNOR: coincidencia lógica
    U = 1 if N == M else 0
    return 'DEBE' if U == 1 else 'HABER'

# PRE: decision es una DecisionProfesional (H₂) válida
# POST: retorna un objeto Asiento con todos los campos calculados
# INVARIANTE: el período está abierto y las cuentas existen
def generar_asiento(decision):
    # 1. Validar período
    periodo = obtener_periodo(decision.periodo_id)
    if periodo.estado != 'ABIERTO':
        raise PeriodoCerradoError(f"Periodo {periodo.id} no está abierto")
    
    # 2. Validar partida doble
    if not validar_partida_doble(decision.partidas):
        raise PartidaDobleError("ΣDEBE != ΣHABER")
    
    # 3. Validar cuentas y aplicar axioma
    for partida in decision.partidas:
        cuenta = obtener_cuenta(partida.cuenta_codigo, partida.cuenta_version)
        if not cuenta:
            raise CuentaNoExisteError(f"Cuenta {partida.cuenta_codigo} no existe en versión {partida.cuenta_version}")
        # Verificar que la ubicación de la partida coincide con el axioma
        ubicacion_calculada = aplicar_axioma_booleano(cuenta, partida.movimiento)
        if partida.ubicacion != ubicacion_calculada:
            raise AxiomaBooleanoError(f"Ubicación incorrecta para cuenta {partida.cuenta_codigo}")
    
    # 4. Calcular totales
    total_debe = sum(p.monto for p in decision.partidas if p.ubicacion == 'DEBE')
    total_haber = sum(p.monto for p in decision.partidas if p.ubicacion == 'HABER')
    
    # 5. Construir asiento
    asiento = {
        'asiento_id': generar_uuid(),
        'fecha': decision.fecha,
        'periodo_id': decision.periodo_id,
        'descripcion': decision.descripcion,
        'total_debe': total_debe,
        'total_haber': total_haber,
        'decision_id': decision.decision_id,
        'creado_en': timestamp_actual()
    }
    return asiento

# PRE: asiento es el objeto generado, partidas es la lista validada
# POST: persiste el asiento en negocio_diario y las partidas en negocio_partidas
# INVARIANTE: la operación es atómica (transacción SQLite)
def escribir_diario(asiento, partidas):
    with transaccion_atomica():
        # 1. Calcular hash de los datos
        datos_hash = sha256(json.dumps(asiento))
        # 2. Obtener hash previo
        hash_previo = obtener_ultimo_hash_chain()
        # 3. Calcular hash_actual
        hash_actual = sha256(datos_hash + hash_previo)
        # 4. Escribir en auditoria_hash_chain
        hash_chain_id = escribir_hash_chain(asiento, datos_hash, hash_previo, hash_actual)
        # 5. Escribir en negocio_diario
        asiento_id = insertar_asiento(asiento, hash_chain_id)
        # 6. Escribir partidas
        insertar_partidas(asiento_id, partidas)
        # 7. Actualizar Mayor
        actualizar_mayor(asiento_id, partidas)
        # 8. Publicar evento
        publicar_evento('ASIENTO_REGISTRADO', asiento_id)
        return asiento_id


# PRE: asiento_original existe y no ha sido revertido previamente
# POST: genera un asiento de reversión en el período actual
# INVARIANTE: el período actual está abierto
def revertir_asiento(asiento_original, justificacion):
    # 1. Crear partidas inversas (cambiar DEBE ↔ HABER)
    partidas_reversion = []
    for p in obtener_partidas(asiento_original.asiento_id):
        partidas_reversion.append({
            'cuenta_codigo': p.cuenta_codigo,
            'cuenta_version': p.cuenta_version,
            'monto': p.monto,
            'ubicacion': 'HABER' if p.ubicacion == 'DEBE' else 'DEBE',
            'movimiento': 'DISMINUYE' if p.movimiento == 'AUMENTA' else 'AUMENTA'  # inverso lógico
        })
    
    # 2. Crear decisión de reversión
    decision_reversion = {
        'fecha': timestamp_actual(),
        'periodo_id': periodo_actual.id,
        'descripcion': f"Reversión del asiento #{asiento_original.asiento_id}: {justificacion}",
        'partidas': partidas_reversion,
        'decision_id': generar_uuid(),
        'tipo': 'REVERSION'
    }
    
    # 3. Generar asiento de reversión (reutiliza generar_asiento)
    asiento_reversion = generar_asiento(decision_reversion)
    escribir_diario(asiento_reversion, partidas_reversion)
    
    # 4. Registrar la relación de reversión
    registrar_reversion(asiento_original.asiento_id, asiento_reversion.asiento_id)
    return asiento_reversion


