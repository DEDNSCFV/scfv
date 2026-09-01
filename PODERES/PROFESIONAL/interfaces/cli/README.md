<!--
SCFV v6 — Documento de Ingeniería
Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
Versión: 1.0.0
Fecha: 2026-08-26
Estado: APROBADO
ADR relacionados: ADR-001, ADR-002, ADR-003, ADR-005
-->

# CLI — Interfaz de Usuario

## Propósito
La CLI es el punto de interacción entre el contador y el SCFV v6. Su responsabilidad es recibir comandos del contador, delegar la ejecución a los componentes internos y mostrar los resultados.

**La CLI no contiene lógica de negocio. Solo es un puente entre el usuario y el sistema.**

## Autoridad (ADR-001)
- **Profesional**: facilita la decisión del contador.
- **Nunca** escribe en `negocio_*`, `epistemic_*` ni `auditoria_*`.
- **Nunca** genera un asiento directamente. Siempre delega al Motor Contable.

## Modos de Operación

| Modo | Descripción | Uso |
|------|-------------|-----|
| **Manual** | El contador ingresa fecha, cuentas, montos y descripción. No invoca al Núcleo. | Registro rápido, operaciones simples. |
| **Asistido** | El contador ingresa evidencia (PDF, imagen, texto). El Núcleo extrae, interpreta y orienta. El contador revisa y acepta/modifica. | Operaciones complejas, apoyo al juicio. |
| **Batch** | Importación masiva desde CSV/XML con validación de esquema. | Alto volumen de operaciones. |

## Comandos Principales

| Comando | Descripción | Modo |
|---------|-------------|------|
| `registrar` | Registra un asiento manualmente (modo manual). | Manual |
| `orientar` | Procesa una evidencia y devuelve una orientación (modo asistido). | Asistido |
| `aceptar` | Acepta una orientación y la convierte en decisión. | Asistido |
| `rechazar` | Rechaza una orientación (con justificación). | Asistido |
| `modificar` | Modifica una orientación antes de aceptarla. | Asistido |
| `importar` | Importa operaciones desde CSV/XML. | Batch |
| `reporte` | Genera informes en PDF, CSV o HTML. | Todos |
| `auditar` | Exporta paquete de auditoría. | Todos |
| `mandante` | Selecciona el mandante activo. | Todos |
| `periodo` | Gestiona períodos contables (abrir/cerrar). | Todos |

## Invariantes

| ID | Invariante | Verificación |
|----|------------|--------------|
| I-1 | La CLI nunca escribe en `negocio_diario` directamente. | Solo usa el Motor Contable. |
| I-2 | La CLI nunca genera un asiento sin pasar por el Motor Contable. | Validación en el flujo de comandos. |
| I-3 | La CLI permite operar sin el Núcleo en todo momento. | El modo manual no invoca al Núcleo. |
| I-4 | La CLI valida la entrada del contador (formato, campos obligatorios). | Antes de enviar al Motor Contable. |

## Dependencias

### Permitidas
- `core/motor_contable/`: para registrar asientos.
- `epistemic/perceptum/`: para extraer evidencia.
- `epistemic/intellectus/`: para interpretar.
- `epistemic/dictum/`: para orientar.
- `audit/`: para exportar auditoría.
- `db/repositories/`: para leer y listar datos.

### Prohibidas
- Escritura directa en cualquier tabla de la base de datos.
- Generar asientos sin pasar por el Motor Contable.

## Pseudo-código de Funciones Principales

### 1. `registrar(datos) -> str`

```python
# PRE: datos contiene fecha, periodo_id, descripcion, partidas
# POST: retorna el ID del asiento registrado
# INVARIANTE: el asiento se registra a través del Motor Contable
def registrar(datos):
    # 1. Validar entrada
    validar_datos(datos)
    
    # 2. Construir DecisionProfesional (H₂)
    decision = {
        'decision_id': generar_uuid(),
        'fecha': datos.fecha,
        'periodo_id': datos.periodo_id,
        'descripcion': datos.descripcion,
        'partidas': datos.partidas,
        'tipo': 'MANUAL',
        'contador': obtener_usuario_actual()
    }
    
    # 3. Delegar al Motor Contable
    asiento_id = motor_contable.generar_asiento(decision)
    
    # 4. Mostrar confirmación
    return f"Asiento {asiento_id} registrado exitosamente."

# PRE: archivo existe y es accesible
# POST: retorna una orientación generada por el Núcleo
# INVARIANTE: la orientación no es vinculante (E-3)
def orientar(archivo):
    # 1. Extraer evidencia (Perceptum)
    observacion = perceptum.extraer(archivo)
    
    # 2. Interpretar (Intellectus)
    proposicion = intellectus.interpretar(observacion.id)
    
    # 3. Orientar (Dictum)
    orientacion = dictum.orientar(proposicion.id)
    
    # 4. Mostrar orientación al contador
    mostrar_orientacion(orientacion)
    
    return orientacion

# PRE: orientacion_id existe en epistemic_orientacion
# POST: la orientación se convierte en decisión y se registra el asiento
# INVARIANTE: el contador confirma explícitamente
def aceptar(orientacion_id):
    # 1. Obtener orientación
    orientacion = obtener_orientacion(orientacion_id)
    
    # 2. Pedir justificación (opcional)
    justificacion = input("Justificación (opcional): ")
    
    # 3. Construir DecisionProfesional
    decision = {
        'decision_id': generar_uuid(),
        'orientacion_id': orientacion_id,
        'fecha': timestamp_actual(),
        'justificacion': justificacion,
        'contador': obtener_usuario_actual(),
        'tipo': 'ASISTIDA'
    }
    
    # 4. Delegar al Motor Contable
    asiento_id = motor_contable.generar_asiento(decision)
    
    # 5. Registrar decisión
    registrar_decision(decision, asiento_id)
    
    return f"Orientación aceptada. Asiento {asiento_id} registrado."

# PRE: orientacion_id existe en epistemic_orientacion
# POST: la orientación se rechaza y se registra la justificación
# INVARIANTE: el contador explica por qué rechaza
def rechazar(orientacion_id, justificacion):
    # 1. Registrar rechazo
    registrar_rechazo(orientacion_id, justificacion, obtener_usuario_actual())
    
    # 2. Alimentar aprendizaje del Núcleo (retroalimentación)
    dictum.retroalimentar(orientacion_id, 'RECHAZADA')
    
    return "Orientación rechazada. Justificación registrada."

# PRE: orientacion_id existe, modificaciones contiene cambios
# POST: se crea una nueva orientación modificada
# INVARIANTE: la modificación queda registrada para auditoría
def modificar(orientacion_id, modificaciones):
    # 1. Obtener orientación original
    orientacion = obtener_orientacion(orientacion_id)
    
    # 2. Aplicar modificaciones
    nueva_orientacion = aplicar_modificaciones(orientacion, modificaciones)
    
    # 3. Mostrar la nueva orientación al contador
    mostrar_orientacion(nueva_orientacion)
    
    # 4. Registrar modificación
    registrar_modificacion(orientacion_id, nueva_orientacion.id, obtener_usuario_actual())
    
    return "Modificaciones aplicadas. Revisar nueva orientación."

# PRE: tipo es 'diario', 'mayor', 'balance', 'resultados'
#     formato es 'pdf', 'csv', 'html'
# POST: retorna el contenido del reporte en el formato solicitado
def reporte(tipo, periodo, formato):
    # 1. Leer datos del Diario y Mayor
    datos = obtener_datos_para_reporte(tipo, periodo)
    
    # 2. Generar reporte
    if formato == 'pdf':
        contenido = generar_pdf(datos)
    elif formato == 'csv':
        contenido = generar_csv(datos)
    elif formato == 'html':
        contenido = generar_html(datos)
    
    # 3. Registrar hash del reporte en auditoría
    hash_id = audit.escribir_hash_chain('reportes', f'{tipo}_{periodo}', {'hash': hash_contenido})
    
    return contenido

# PRE: la carpeta del mandante existe en /data/mandante_{nombre}/
# POST: cambia el contexto al mandante seleccionado
# INVARIANTE: la conexión a la base de datos se reestablece
def mandante(nombre):
    # 1. Validar que la carpeta existe
    ruta = f"/data/mandante_{nombre}"
    if not os.path.exists(ruta):
        return f"Error: Mandante '{nombre}' no existe."
    
    # 2. Cerrar conexión actual (si existe)
    db.cerrar_conexion()
    
    # 3. Establecer nuevo contexto
    establecer_mandante_activo(nombre)
    
    # 4. Abrir conexión a la base del mandante
    db.abrir_conexion(f"{ruta}/scfv_v6.db")
    
    return f"Mandante '{nombre}' activo."

# PRE: archivo existe y es CSV o XML con formato válido
# POST: importa múltiples operaciones y registra asientos
# INVARIANTE: cada operación se registra como un asiento individual
def importar(archivo):
    # 1. Leer archivo
    datos = leer_archivo(archivo)
    
    # 2. Validar formato
    validar_esquema(datos)
    
    # 3. Procesar línea por línea
    exitosos = 0
    fallidos = 0
    errores = []
    
    for linea in datos:
        try:
            # Registrar cada operación (usa el modo manual)
            registrar(linea)
            exitosos += 1
        except Exception as e:
            fallidos += 1
            errores.append(f"Línea {linea.numero}: {str(e)}")
    
    # 4. Mostrar resumen
    mensaje = f"Importación completada: {exitosos} exitosas, {fallidos} fallidas."
    if errores:
        mensaje += f"\nErrores:\n" + "\n".join(errores)
    
    return mensaje

# PRE: periodo existe y está cerrado (opcional)
# POST: retorna el paquete de auditoría para descarga
def auditar(periodo):
    # 1. Obtener mandante activo
    mandante = obtener_mandante_activo()
    
    # 2. Exportar paquete
    paquete = audit.exportar_paquete(periodo, mandante)
    
    # 3. Registrar exportación en bitácora
    audit.registrar_bitacora('EXPORTACION_AUDITORIA', periodo, mandante)
    
    return paquete

$ scfv mandante ABC
Mandante 'ABC' activo.

$ scfv registrar
Fecha (YYYY-MM-DD): 2026-08-25
Período: 2026-08
Descripción: Venta de mercancía
Cuenta DEBE: 110101 (Clientes)
Monto: 100.00
Cuenta HABER: 410101 (Ventas)
Monto: 100.00
¿Confirmar? (s/n): s
Asiento aebc1234-5678-90ab-cdef-1234567890ab registrado exitosamente.

$ scfv orientar factura_1234.pdf
Extrayendo evidencia... (Perceptum)
Interpretando... (Intellectus)
Sugerencia generada... (Dictum)

Orientación #o-001:
  Tipo: SUGERENCIA
  Severidad: INFORMATIVA
  Mensaje: La evidencia del 25/08/2026 del emisor J-123456789 al receptor J-987654321 por 100.00 USD es consistente con una compra de inventario.
  Soporte: 0.86
  Acción sugerida: REVISAR_CUENTA
  ¿Aceptar? (s/n/m=modificar): s
  Justificación: Factura verificada.
Asiento aebc1234-5678-90ab-cdef-1234567890ab registrado.

$ scfv importar operaciones_2026_08.csv
Importación completada: 45 exitosas, 3 fallidas.
Errores:
  Línea 12: Cuenta no existe en PCU.
  Línea 23: Período cerrado.
  Línea 34: Monto inválido (negativo).


