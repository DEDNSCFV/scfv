<!--
SCFV v6 — Documento de Ingeniería
Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
Versión: 1.0.0
Fecha: 2026-08-26
Estado: APROBADO
ADR relacionados: ADR-001, ADR-002, ADR-003
-->

# Fractal: Compras

## Propósito
Gestiona el ciclo de vida de las compras del mandante. Registra adquisiciones de bienes o servicios, valida su integridad y publica eventos que otros fractales (Inventario, Fiscal, Motor Contable) consumen para actualizar sus propios dominios.

## Objeto de Dominio
**Compra**: registro de una transacción comercial donde el mandante adquiere bienes o servicios de un proveedor.

## Estados

| Estado | Significado |
|--------|-------------|
| **BORRADOR** | Creada pero incompleta (falta información). |
| **DOCUMENTADA** | Evidencia (factura de compra) cargada y validada. |
| **VALIDADA** | Reglas de negocio aprobadas (precios, cantidades, etc.). |
| **CONFIRMADA** | Lista para contabilizar. Publica `COMPRA_CONFIRMADA`. |
| **CONTABILIZADA** | Asiento generado por el Motor Contable. |
| **ANULADA** | Compra cancelada (solo desde CONFIRMADA o DOCUMENTADA). |

## Hechos que Reconoce (Eventos de Entrada)

| Evento | Origen | Propósito |
|--------|--------|-----------|
| `COMPRA_REGISTRADA` | CLI (contador) | Inicia el proceso de compra. |
| `COMPRA_DOCUMENTADA` | CLI (contador) | Evidencia cargada. |
| `COMPRA_VALIDADA` | Núcleo / Contador | Reglas de negocio verificadas. |
| `COMPRA_CONFIRMADA` | Fractal Compras | Publicado internamente; pasa a CONFIRMADA. |
| `ASIENTO_REGISTRADO` | Motor Contable | Confirma que el asiento fue registrado. |

## Eventos que Produce

| Evento | Destino | Propósito |
|--------|---------|-----------|
| `COMPRA_CONFIRMADA` | Orquestador → Inventario, Fiscal, Motor Contable | Notifica que la compra está lista para ser contabilizada y afectar inventario. |
| `COMPRA_ANULADA` | Orquestador → Motor Contable | Notifica anulación; puede requerir reversión. |

## Reglas de Negocio

1. **Toda compra requiere evidencia** (factura de compra o documento equivalente).
2. **Monto total = Σ líneas * precio_unitario** (validación de consistencia).
3. **IVA soportado** (crédito fiscal) se calcula según tasa vigente.
4. **Descuentos** se aplican como líneas separadas (cuenta de descuento en compras).
5. **No se puede confirmar una compra** si el proveedor no está registrado (opcional).
6. **No se puede anular una compra** ya contabilizada (debe hacerse mediante asiento de reversión).

## Invariantes

| ID | Invariante | Verificación |
|----|------------|--------------|
| I-1 | `total_compra = Σ (cantidad * precio_unitario) - descuentos` | Antes de confirmar. |
| I-2 | `iva_calculado = total_compra * tasa_iva` | Antes de confirmar. |
| I-3 | `proveedor_existe` | Verificar en catálogo de proveedores (si existe). |
| I-4 | `fecha_compra >= fecha_ultimo_cierre` | No se puede registrar compras en períodos cerrados. |
| I-5 | `estado_compra ∈ {BORRADOR, DOCUMENTADA, VALIDADA, CONFIRMADA, CONTABILIZADA, ANULADA}` | Estado válido. |

## Eventos que Recibe (Comandos del Orquestador)

| Evento | Acción |
|--------|--------|
| `COMPRA_REGISTRADA` | Crear compra en estado BORRADOR. |
| `COMPRA_DOCUMENTADA` | Asociar evidencia (hash) y pasar a DOCUMENTADA. |
| `COMPRA_VALIDADA` | Validar reglas de negocio y pasar a VALIDADA. |
| `COMPRA_CONFIRMAR` | Confirmar compra y publicar `COMPRA_CONFIRMADA`. |
| `ASIENTO_REGISTRADO` | Marcar compra como CONTABILIZADA. |

## Consecuencias (Cambios Internos)

1. **BORRADOR → DOCUMENTADA**: Se almacena hash de la factura en `negocio_compras_evidencia`.
2. **DOCUMENTADA → VALIDADA**: Se calculan totales, IVA, descuentos; se verifica proveedor.
3. **VALIDADA → CONFIRMADA**: Se publica `COMPRA_CONFIRMADA` con payload completo.
4. **CONFIRMADA → CONTABILIZADA**: Se actualiza estado a CONTABILIZADA (sin más cambios).
5. **CONFIRMADA → ANULADA**: Se publica `COMPRA_ANULADA` con justificación.

## Evidencias
- **Factura de compra**: archivo PDF o imagen. Su hash se almacena en `negocio_compras_evidencia`.
- **Nota de débito**: en caso de devolución.

## Relación con Otros Fractales
- **Ninguna invocación directa**. Se comunica mediante eventos:
  - `COMPRA_CONFIRMADA` → lo consumen `Inventario` (incrementa stock), `Fiscal` (registra IVA soportado), `Motor Contable` (genera asiento).

## Autoridad
- **Puede modificar**: `negocio_compras`, `negocio_compras_detalle`, `negocio_compras_evidencia`.
- **Nunca modifica**: tablas de otros fractales (`negocio_inventario`, `negocio_fiscal`, `negocio_diario`).

## Límite
- **No escribe** en `negocio_diario` ni `negocio_mayor`. Solo el Motor Contable tiene esa autoridad.
- **No modifica** inventario directamente; publica eventos y deja que el fractal `Inventario` reaccione.

## Tablas Propias del Fractal Compras

### `negocio_compras`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | TEXT | UUID de la compra |
| proveedor_id | TEXT | Identificador del proveedor |
| fecha | INTEGER | Timestamp de la compra |
| total_bruto | INTEGER | Monto bruto (sin IVA) |
| total_iva | INTEGER | IVA calculado |
| total_descuento | INTEGER | Descuentos aplicados |
| total_neto | INTEGER | Total neto a pagar |
| estado | TEXT | BORRADOR, DOCUMENTADA, VALIDADA, CONFIRMADA, CONTABILIZADA, ANULADA |
| evidencia_hash | TEXT | Hash de la factura (referencia a auditoria_hash_chain) |
| creado_en | INTEGER | Timestamp de creación |
| actualizado_en | INTEGER | Timestamp de última modificación |

### `negocio_compras_detalle`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | TEXT | UUID del detalle |
| compra_id | TEXT | Referencia a negocio_compras |
| producto_codigo | TEXT | Código del producto |
| cantidad | INTEGER | Cantidad comprada |
| precio_unitario | INTEGER | Precio unitario en céntimos |
| descuento_linea | INTEGER | Descuento aplicado a esta línea |
| total_linea | INTEGER | Subtotal de la línea |

## Pseudo-código de Funciones Principales

### 1. `registrar_compra(datos) -> Compra`

```python
# PRE: datos contiene proveedor_id, fecha, líneas, evidencia_hash
# POST: crea una compra en estado BORRADOR
# INVARIANTE: el proveedor existe y el período está abierto
def registrar_compra(datos):
    # 1. Validar período
    periodo = obtener_periodo_actual()
    if periodo.estado != 'ABIERTO':
        raise PeriodoCerradoError()
    
    # 2. Validar proveedor (si existe catálogo)
    if not proveedor_existe(datos.proveedor_id):
        raise ProveedorNoExisteError()
    
    # 3. Crear compra
    compra = {
        'id': generar_uuid(),
        'proveedor_id': datos.proveedor_id,
        'fecha': datos.fecha,
        'estado': 'BORRADOR',
        'evidencia_hash': datos.evidencia_hash,
        'creado_en': timestamp_actual()
    }
    
    # 4. Guardar en negocio_compras
    guardar_compra(compra)
    
    # 5. Guardar detalles
    for linea in datos.lineas:
        guardar_detalle(compra.id, linea)
    
    return compra

# PRE: la compra existe y está en estado VALIDADA o DOCUMENTADA
# POST: la compra pasa a CONFIRMADA y se publica COMPRA_CONFIRMADA
# INVARIANTE: las reglas de negocio están validadas
def confirmar_compra(compra_id):
    compra = obtener_compra(compra_id)
    
    # 1. Validar estado
    if compra.estado not in ['DOCUMENTADA', 'VALIDADA']:
        raise EstadoInvalidoError(f"Compra en estado {compra.estado} no puede confirmarse")
    
    # 2. Validar reglas de negocio (recalcular)
    validar_reglas(compra)
    
    # 3. Calcular totales
    calcular_totales(compra)
    
    # 4. Cambiar estado
    compra.estado = 'CONFIRMADA'
    compra.actualizado_en = timestamp_actual()
    actualizar_compra(compra)
    
    # 5. Publicar evento COMPRA_CONFIRMADA
    evento = {
        'event_id': generar_uuid(),
        'tipo': 'COMPRA_CONFIRMADA',
        'origen': 'compras',
        'payload': {
            'compra_id': compra.id,
            'proveedor_id': compra.proveedor_id,
            'fecha': compra.fecha,
            'total_neto': compra.total_neto,
            'total_iva': compra.total_iva,
            'lineas': obtener_detalles(compra.id),
            'evidencia_hash': compra.evidencia_hash,
            'periodo_id': obtener_periodo_actual().id
        },
        'timestamp': timestamp_actual()
    }
    publicar_evento(evento)
    
    return evento

# PRE: evento es válido y tiene un tipo reconocido por el fractal
# POST: se procesa el evento y se actualiza el estado de la compra
# INVARIANTE: la operación es idempotente
def procesar_evento(evento):
    # Verificar idempotencia
    if not idempotency_guard.verificar(evento.event_id, 'compras'):
        return
    
    if evento.tipo == 'COMPRA_REGISTRADA':
        registrar_compra(evento.payload)
    elif evento.tipo == 'COMPRA_VALIDADA':
        validar_compra(evento.payload.compra_id)
    elif evento.tipo == 'COMPRA_CONFIRMAR':
        confirmar_compra(evento.payload.compra_id)
    elif evento.tipo == 'ASIENTO_REGISTRADO':
        # Marcar compra como CONTABILIZADA
        compra = obtener_compra(evento.payload.compra_id)
        compra.estado = 'CONTABILIZADA'
        actualizar_compra(compra)
    else:
        raise EventoNoReconocidoError(f"Evento {evento.tipo} no reconocido")


