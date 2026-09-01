<!--
SCFV v6 — Documento de Ingeniería
Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
Versión: 1.0.0
Fecha: 2026-08-26
Estado: APROBADO
ADR relacionados: ADR-001, ADR-002, ADR-003
-->

# Orquestador

## Propósito
El Orquestador es el coordinador central del sistema. Procesa eventos del Event Store en orden FIFO, gestiona Sagas (transacciones distribuidas) y garantiza la idempotencia y recuperación ante crash.

## Autoridad (ADR-001)
- **Técnica**: coordina la ejecución de eventos entre fractales y el Motor Contable.
- **Nunca** escribe en `negocio_*` ni en `epistemic_*` (solo en `auditoria_*`).
- **Nunca** modifica datos históricos.

## Entradas
- `Evento` desde el Event Store (`auditoria_event_store`).
- `SagaRequest` desde la CLI o desde un fractal (para iniciar una Saga).

## Salidas
- `Evento` encaminado al Motor Contable o a un fractal.
- Estado de Saga actualizado en `auditoria_sagas`.
- Registro de idempotencia en `auditoria_event_processing`.

## Componentes

| Componente | Responsabilidad |
|------------|-----------------|
| **Event Reader** | Lee eventos pendientes del Event Store en orden FIFO (por timestamp). |
| **Event Dispatcher** | Distribuye el evento al consumidor correspondiente (Motor Contable o fractal). |
| **Saga Manager** | Crea, actualiza y monitorea Sagas. Controla el flujo de pasos y la compensación. |
| **Idempotency Guard** | Verifica si un evento ya fue procesado por un consumidor específico. |
| **Recovery Handler** | Al reiniciar, reanuda Sagas en estado `EN_PROCESO` desde el último paso completado. |

## Invariantes

| ID | Invariante | Verificación |
|----|------------|--------------|
| I-1 | Un evento no se procesa dos veces por el mismo consumidor | `Idempotency Guard` verifica en `auditoria_event_processing`. |
| I-2 | Las Sagas solo pueden estar en un estado a la vez | Transiciones de estado definidas. |
| I-3 | Si una Saga termina en `ERROR_DE_COMPENSACION`, requiere intervención | No se reanuda automáticamente. |
| I-4 | El orden de procesamiento es FIFO (por timestamp) | Se lee el Event Store ordenado por timestamp. |

## Dependencias

### Permitidas
- `db/repositories/auditoria_event_store.py`: para leer eventos y marcar procesados.
- `db/repositories/auditoria_sagas.py`: para crear, leer y actualizar Sagas.
- `db/repositories/auditoria_event_processing.py`: para registrar idempotencia.
- `core/motor_contable/`: para enviar eventos al Motor Contable.
- `fractals/`: para enviar eventos a los fractales.

### Prohibidas
- Cualquier módulo de `epistemic/` (el Orquestador no participa en la orientación).
- Escritura directa en `negocio_*` o `epistemic_*`.

## Pseudo-código de Funciones Principales

### 1. `procesar_evento(event_id: str) -> None`

```python
# PRE: event_id existe en auditoria_event_store
# POST: el evento se procesa una vez por cada consumidor
# INVARIANTE: el procesamiento es atómico y persistente
def procesar_evento(event_id):
    evento = obtener_evento(event_id)
    consumidor = determinar_consumidor(evento.tipo)
    
    # 1. Verificar idempotencia
    if not idempotency_guard.verificar(event_id, consumidor):
        # Ya fue procesado, saltar
        return
    
    # 2. Marcar como EN_PROCESO
    idempotency_guard.registrar(event_id, consumidor, 'EN_PROCESO')
    
    try:
        # 3. Ejecutar la acción correspondiente
        if consumidor == 'MOTOR_CONTABLE':
            motor_contable.procesar_evento(evento)
        elif consumidor == 'FRACTAL':
            fractal = obtener_fractal(evento.origen)
            fractal.procesar_evento(evento)
        
        # 4. Marcar como EXITOSO
        idempotency_guard.registrar(event_id, consumidor, 'EXITOSO')
    except Exception as e:
        # 5. Marcar como FALLIDO y registrar error
        idempotency_guard.registrar(event_id, consumidor, 'FALLIDO', error=str(e))
        # 6. Activar compensación si es parte de una Saga
        if evento.saga_id:
            saga_manager.compensar(evento.saga_id)

# PRE: saga_request contiene nombre, pasos, payload
# POST: la Saga se ejecuta paso a paso; si falla, se compensa
# INVARIANTE: los pasos se ejecutan en orden secuencial
def ejecutar_saga(saga_request):
    saga_id = generar_uuid()
    saga = crear_saga(saga_id, saga_request)
    saga_manager.crear(saga)
    
    for paso in saga.pasos:
        try:
            # Ejecutar paso
            resultado = ejecutar_paso(paso)
            # Actualizar paso_actual
            saga_manager.actualizar_paso(saga_id, paso.secuencia, resultado)
        except Exception as e:
            # Si falla, ejecutar compensación en orden inverso
            saga_manager.compensar(saga_id)
            return saga
    
    # Todos los pasos exitosos
    saga_manager.completar(saga_id)
    return saga

# PRE: el sistema acaba de reiniciar
# POST: todas las Sagas en EN_PROCESO se reanudan desde el último paso completado
# INVARIANTE: la idempotencia garantiza que los pasos ya ejecutados no se repitan
def recuperar_sagas_pendientes():
    sagas_en_proceso = obtener_sagas_por_estado('EN_PROCESO')
    for saga in sagas_en_proceso:
        # Determinar el último paso completado
        ultimo_paso = saga.paso_actual
        # Reanudar desde el siguiente paso
        for paso in saga.pasos[ultimo_paso:]:
            try:
                ejecutar_paso(paso)
                saga_manager.actualizar_paso(saga.saga_id, paso.secuencia, resultado)
            except Exception as e:
                saga_manager.compensar(saga.saga_id)
                break


