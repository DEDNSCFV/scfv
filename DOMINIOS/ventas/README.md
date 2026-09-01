<!--
SCFV v6 — Documento de Ingeniería
Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
Versión: 1.0.0
Fecha: 2026-08-26
Estado: APROBADO
ADR relacionados: ADR-001, ADR-002, ADR-003
-->

# Fractal: Ventas

## Propósito
Gestiona el ciclo de vida de las ventas del mandante. Registra operaciones comerciales, valida su integridad y publica eventos que otros fractales (Inventario, Fiscal, Motor Contable) consumen para actualizar sus propios dominios.

## Objeto de Dominio
**Venta**: registro de una transacción comercial donde el mandante vende bienes o servicios a un cliente.

## Estados

| Estado | Significado |
|--------|-------------|
| **BORRADOR** | Creada pero incompleta (falta información). |
| **DOCUMENTADA** | Evidencia (factura) cargada y validada. |
| **VALIDADA** | Reglas de negocio aprobadas (crédito, inventario, etc.). |
| **CONFIRMADA** | Lista para contabilizar. Publica `VENTA_CONFIRMADA`. |
| **CONTABILIZADA** | Asiento generado por el Motor Contable. |
| **ANULADA** | Venta cancelada (solo desde CONFIRMADA o DOCUMENTADA). |

## Hechos que Reconoce (Eventos de Entrada)

| Evento | Origen | Propósito |
|--------|--------|-----------|
| `VENTA_REGISTRADA` | CLI (contador) | Inicia el proceso de venta. |
| `VENTA_DOCUMENTADA` | CLI (contador) | Evidencia cargada. |
| `VENTA_VALIDADA` | Núcleo / Contador | Reglas de negocio verificadas. |
| `VENTA_CONFIRMADA` | Fractal Ventas | Publicado internamente; pasa a CONFIRMADA. |
| `ASIENTO_REGISTRADO` | Motor Contable | Confirma que el asiento fue registrado. |

## Eventos que Produce

| Evento | Destino | Propósito |
|--------|---------|-----------|
| `VENTA_CONFIRMADA` | Orquestador → Inventario, Fiscal, Motor Contable | Notifica que la venta está lista para ser contabilizada y afectar inventario. |
| `VENTA_ANULADA` | Orquestador → Motor Contable | Notifica anulación; puede requerir reversión. |

## Reglas de Negocio

1. **Toda venta requiere evidencia** (factura o documento equivalente).
2. **Monto total = Σ líneas * precio_unitario** (validación de consistencia).
3. **IVA calculado automáticamente** según tasa vigente y tipo de producto.
4. **Descuentos** se aplican como líneas separadas (cuenta de descuento).
5. **No se puede confirmar una venta** si el cliente tiene saldo vencido (opcional, según política).
6. **No se puede anular una venta** ya contabilizada (debe hacerse mediante asiento de reversión).

## Invariantes

| ID | Invariante | Verificación |
|----|------------|--------------|
| I-1 | `total_venta = Σ (cantidad * precio_unitario) - descuentos` | Antes de confirmar. |
| I-2 | `iva_calculado = total_venta * tasa_iva` | Antes de confirmar. |
| I-3 | `cliente_existe` | Verificar en catálogo de clientes (si existe). |
| I-4 | `fecha_venta >= fecha_ultimo_cierre` | No se puede registrar ventas en períodos cerrados. |
| I-5 | `estado_venta ∈ {BORRADOR, DOCUMENTADA, VALIDADA, CONFIRMADA, CONTABILIZADA, ANULADA}` | Estado válido. |

## Eventos que Recibe (Comandos del Orquestador)

| Evento | Acción |
|--------|--------|
| `VENTA_REGISTRADA` | Crear venta en estado BORRADOR. |
| `VENTA_DOCUMENTADA` | Asociar evidencia (hash) y pasar a DOCUMENTADA. |
| `VENTA_VALIDADA` | Validar reglas de negocio y pasar a VALIDADA. |
| `VENTA_CONFIRMAR` | Confirmar venta y publicar `VENTA_CONFIRMADA`. |
| `ASIENTO_REGISTRADO` | Marcar venta como CONTABILIZADA. |

## Consecuencias (Cambios Internos)

1. **BORRADOR → DOCUMENTADA**: Se almacena hash de la factura en `negocio_ventas_evidencia`.
2. **DOCUMENTADA → VALIDADA**: Se calculan totales, IVA, descuentos; se verifica cliente.
3. **VALIDADA → CONFIRMADA**: Se publica `VENTA_CONFIRMADA` con payload completo.
4. **CONFIRMADA → CONTABILIZADA**: Se actualiza estado a CONTABILIZADA (sin más cambios).
5. **CONFIRMADA → ANULADA**: Se publica `VENTA_ANULADA` con justificación.

## Evidencias
- **Factura**: archivo PDF o imagen. Su hash se almacena en `negocio_ventas_evidencia`.
- **Nota de crédito**: en caso de devolución.

## Relación con Otros Fractales
- **Ninguna invocación directa**. Se comunica mediante eventos:
  - `VENTA_CONFIRMADA` → lo consumen `Inventario` (descuenta stock), `Fiscal` (calcula IVA), `Motor Contable` (genera asiento).

## Autoridad
- **Puede modificar**: `negocio_ventas`, `negocio_ventas_detalle`, `negocio_ventas_evidencia`.
- **Nunca modifica**: tablas de otros fractales (`negocio_inventario`, `negocio_fiscal`, `negocio_diario`).

## Límite
- **No escribe** en `negocio_diario` ni `negocio_mayor`. Solo el Motor Contable tiene esa autoridad.
- **No modifica** inventario directamente; publica eventos y deja que el fractal `Inventario` reaccione.

## Tablas Propias del Fractal Ventas

### `negocio_ventas`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | TEXT | UUID de la venta |
| cliente_id | TEXT | Identificador del cliente |
| fecha | INTEGER | Timestamp de la venta |
| total_bruto | INTEGER | Monto bruto (sin IVA) |
| total_iva | INTEGER | IVA calculado |
| total_descuento | INTEGER | Descuentos aplicados |
| total_neto | INTEGER | Total neto a pagar |
| estado | TEXT | BORRADOR, DOCUMENTADA, VALIDADA, CONFIRMADA, CONTABILIZADA, ANULADA |
| evidencia_hash | TEXT | Hash de la factura (referencia a auditoria_hash_chain) |
| creado_en | INTEGER | Timestamp de creación |
| actualizado_en | INTEGER | Timestamp de última modificación |

### `negocio_ventas_detalle`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | TEXT | UUID del detalle |
| venta_id | TEXT | Referencia a negocio_ventas |
| producto_codigo | TEXT | Código del producto |
| cantidad | INTEGER | Cantidad vendida |
| precio_unitario | INTEGER | Precio unitario en céntimos |
| descuento_linea | INTEGER | Descuento aplicado a esta línea |
| total_linea | INTEGER | Subtotal de la línea |

## Pseudo-código de Funciones Principales

### 1. `registrar_venta(datos) -> Venta`

```python
# PRE: datos contiene cliente_id, fecha, líneas, evidencia_hash
# POST: crea una venta en estado BORRADOR
# INVARIANTE: el cliente existe y el período está abierto
def registrar_venta(datos):
    # 1. Validar período
    periodo = obtener_periodo_actual()
    if periodo.estado != 'ABIERTO':
        raise PeriodoCerradoError()
    
    # 2. Validar cliente (si existe catálogo)
    if not cliente_existe(datos.cliente_id):
        raise ClienteNoExisteError()
    
    # 3. Crear venta
    venta = {
        'id': generar_uuid(),
        'cliente_id': datos.cliente_id,
        'fecha': datos.fecha,
        'estado': 'BORRADOR',
        'evidencia_hash': datos.evidencia_hash,
        'creado_en': timestamp_actual()
    }
    
    # 4. Guardar en negocio_ventas
    guardar_venta(venta)
    
    # 5. Guardar detalles
    for linea in datos.lineas:
        guardar_detalle(venta.id, linea)
    
    return venta

# PRE: la venta existe y está en estado VALIDADA o DOCUMENTADA
# POST: la venta pasa a CONFIRMADA y se publica VENTA_CONFIRMADA
# INVARIANTE: las reglas de negocio están validadas
def confirmar_venta(venta_id):
    venta = obtener_venta(venta_id)
    
    # 1. Validar estado
    if venta.estado not in ['DOCUMENTADA', 'VALIDADA']:
        raise EstadoInvalidoError(f"Venta en estado {venta.estado} no puede confirmarse")
    
    # 2. Validar reglas de negocio (recalcular)
    validar_reglas(venta)
    
    # 3. Calcular totales
    calcular_totales(venta)
    
    # 4. Cambiar estado
    venta.estado = 'CONFIRMADA'
    venta.actualizado_en = timestamp_actual()
    actualizar_venta(venta)
    
    # 5. Publicar evento VENTA_CONFIRMADA
    evento = {
        'event_id': generar_uuid(),
        'tipo': 'VENTA_CONFIRMADA',
        'origen': 'ventas',
        'payload': {
            'venta_id': venta.id,
            'cliente_id': venta.cliente_id,
            'fecha': venta.fecha,
            'total_neto': venta.total_neto,
            'total_iva': venta.total_iva,
            'lineas': obtener_detalles(venta.id),
            'evidencia_hash': venta.evidencia_hash,
            'periodo_id': obtener_periodo_actual().id
        },
        'timestamp': timestamp_actual()
    }
    publicar_evento(evento)
    
    return evento

# PRE: la venta existe y NO está CONTABILIZADA
# POST: la venta pasa a ANULADA y se publica VENTA_ANULADA
# INVARIANTE: solo se permite anular antes de contabilizar
def anular_venta(venta_id, justificacion):
    venta = obtener_venta(venta_id)
    
    if venta.estado == 'CONTABILIZADA':
        raise VentaContabilizadaError("No se puede anular una venta contabilizada")
    
    venta.estado = 'ANULADA'
    venta.justificacion_anulacion = justificacion
    venta.actualizado_en = timestamp_actual()
    actualizar_venta(venta)
    
    evento = {
        'event_id': generar_uuid(),
        'tipo': 'VENTA_ANULADA',
        'origen': 'ventas',
        'payload': {
            'venta_id': venta.id,
            'justificacion': justificacion
        },
        'timestamp': timestamp_actual()
    }
    publicar_evento(evento)
    return evento

# PRE: evento es válido y tiene un tipo reconocido por el fractal
# POST: se procesa el evento y se actualiza el estado de la venta
# INVARIANTE: la operación es idempotente
def procesar_evento(evento):
    # Verificar idempotencia
    if not idempotency_guard.verificar(evento.event_id, 'ventas'):
        return
    
    if evento.tipo == 'VENTA_REGISTRADA':
        registrar_venta(evento.payload)
    elif evento.tipo == 'VENTA_VALIDADA':
        validar_venta(evento.payload.venta_id)
    elif evento.tipo == 'VENTA_CONFIRMAR':
        confirmar_venta(evento.payload.venta_id)
    elif evento.tipo == 'ASIENTO_REGISTRADO':
        # Marcar venta como CONTABILIZADA
        venta = obtener_venta(evento.payload.venta_id)
        venta.estado = 'CONTABILIZADA'
        actualizar_venta(venta)
    else:
        raise EventoNoReconocidoError(f"Evento {evento.tipo} no reconocido")


