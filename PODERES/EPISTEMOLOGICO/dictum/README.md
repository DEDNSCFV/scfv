<!--
SCFV v6 — Documento de Ingeniería
Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
Versión: 1.0.0
Fecha: 2026-08-26
Estado: APROBADO
ADR relacionados: ADR-004, ADR-003
-->

# Dictum — Fase de Orientación del Núcleo Epistemológico

## Propósito
El Dictum es la tercera y última fase del Núcleo Epistemológico. Su responsabilidad es **medir el soporte computacional** a partir de las métricas generadas por el Intellectus (r, s, o, t, v) y producir una **Orientación** que el contador pueda consultar, aceptar, rechazar o modificar.

**El Dictum orienta, no decide. Su salida es una sugerencia, no una orden.**

## Autoridad (ADR-004)
- **Epistemológica**: genera orientaciones informativas.
- **Nunca** escribe en `negocio_*`. Solo escribe en `epistemic_orientacion`.
- **Nunca** genera un asiento ni modifica decisiones del contador.

## Entradas
- **Proposicion**: objeto generado por Intellectus (con r, s, o, t, v).
- **Contexto**: información adicional del mandante (políticas, restricciones, preferencias).
- **Historial**: decisiones previas del contador (para aprendizaje).

## Salidas
- **Orientacion**: objeto que contiene:
  - `id`: UUID.
  - `tipo`: "SUGERENCIA", "ALERTA", "PROYECCION", "PATRON".
  - `severidad`: "INFORMATIVA", "ATENCION", "CRITICA".
  - `mensaje`: texto legible en lenguaje natural.
  - `datos_soporte`: métricas y justificación.
  - `accion_sugerida`: "REVISAR_CUENTA", "VERIFICAR_TASA", "CONSULTAR_CATALOGO", etc.
  - `requiere_respuesta`: booleano (siempre TRUE para sugerencias).
  - `soporte_computacional`: C = f(r, s, o, t, v).
  - `creado_en`: timestamp.

## La Medida de Soporte Computacional

C = f(r, s, o, t, v)


| Dimensión | Significado | Rango |
|-----------|-------------|-------|
| **r** | Cobertura normativa | 0.0 - 1.0 |
| **s** | Similitud histórica | 0.0 - 1.0 |
| **o** | Consistencia ontológica | 0.0 - 1.0 |
| **t** | Peso temporal | 0.0 - 1.0 |
| **v** | Volatilidad contextual | 0.0 - 1.0 |

**Cálculo**:
```python
# C = promedio ponderado de las cinco dimensiones
C = (r * 0.30) + (s * 0.25) + (o * 0.20) + (t * 0.15) + (v * 0.10)

# PRE: proposicion_id existe en epistemic_proposicion
# POST: retorna una Orientacion con C calculado y sugerencia
# INVARIANTE: la orientación no es vinculante (E-3)
def orientar(proposicion_id):
    # 1. Obtener Proposición
    proposicion = obtener_proposicion(proposicion_id)
    
    # 2. Calcular C = f(r, s, o, t, v)
    C = calcular_C(proposicion)
    
    # 3. Determinar tipo y severidad
    tipo, severidad = clasificar(C, proposicion)
    
    # 4. Generar mensaje en lenguaje natural
    mensaje = generar_mensaje(proposicion, C, tipo, severidad)
    
    # 5. Sugerir acción
    accion = sugerir_accion(proposicion, C)
    
    # 6. Construir Orientación
    orientacion = {
        'id': generar_uuid(),
        'tipo': tipo,
        'severidad': severidad,
        'mensaje': mensaje,
        'datos_soporte': {
            'r': proposicion.r,
            's': proposicion.s,
            'o': proposicion.o,
            't': proposicion.t,
            'v': proposicion.v,
            'C': C
        },
        'accion_sugerida': accion,
        'requiere_respuesta': True,
        'proposicion_id': proposicion.proposicion_id,
        'evidencia_hash': proposicion.evidencia_hash,
        'creado_en': timestamp_actual()
    }
    
    # 7. Persistir en epistemic_orientacion
    guardar_orientacion(orientacion)
    
    return orientacion

# PRE: proposicion tiene r, s, o, t, v
# POST: retorna C entre 0.0 y 1.0
# INVARIANTE: C es un promedio ponderado
def calcular_C(proposicion):
    # Pesos definidos según importancia
    pesos = {
        'r': 0.30,  # Cobertura normativa (más importante)
        's': 0.25,  # Similitud histórica
        'o': 0.20,  # Consistencia ontológica
        't': 0.15,  # Peso temporal
        'v': 0.10   # Volatilidad contextual
    }
    
    C = (
        proposicion.r * pesos['r'] +
        proposicion.s * pesos['s'] +
        proposicion.o * pesos['o'] +
        proposicion.t * pesos['t'] +
        proposicion.v * pesos['v']
    )
    
    return min(C, 1.0)  # Asegurar que no supere 1.0

# PRE: proposicion tiene métricas, C está calculado
# POST: retorna (tipo, severidad)
def clasificar(proposicion, C):
    # Determinar tipo
    tipo = 'SUGERENCIA'  # Por defecto
    
    # Si la cobertura normativa es muy baja y no hay similitud
    if proposicion.r < 0.3 and proposicion.s < 0.3:
        tipo = 'ALERTA'
        severidad = 'CRITICA'
    # Si la consistencia ontológica es baja
    elif proposicion.o < 0.4:
        tipo = 'ALERTA'
        severidad = 'ATENCION'
    # Si el peso temporal es bajo (caso muy antiguo)
    elif proposicion.t < 0.3:
        tipo = 'ALERTA'
        severidad = 'INFORMATIVA'
    # Si hay similitud histórica alta y cobertura normativa alta
    elif proposicion.s > 0.7 and proposicion.r > 0.7:
        tipo = 'SUGERENCIA'
        severidad = 'INFORMATIVA'
    else:
        tipo = 'SUGERENCIA'
        severidad = 'ATENCION'
    
    # Ajustar severidad según C
    if C < 0.3:
        severidad = 'CRITICA'
    elif C < 0.5:
        severidad = 'ATENCION'
    
    return tipo, severidad

# PRE: todos los parámetros están definidos
# POST: retorna un mensaje legible en lenguaje natural
def generar_mensaje(proposicion, C, tipo, severidad):
    entidades = proposicion.observacion.entidades
    
    if tipo == 'SUGERENCIA':
        mensaje = f"Sugerencia: la evidencia del {entidades.get('fecha', 'fecha desconocida')} "
        if entidades.get('rif_emisor'):
            mensaje += f"del emisor {entidades['rif_emisor']} "
        if entidades.get('rif_receptor'):
            mensaje += f"al receptor {entidades['rif_receptor']} "
        mensaje += f"por {entidades.get('monto', 'monto desconocido')} {entidades.get('moneda', '')} "
        mensaje += f"es consistente con {proposicion.interpretacion}. "
        mensaje += f"Soporte computacional: {C:.2f}. "
        mensaje += "Revisar y confirmar antes de contabilizar."
    
    elif tipo == 'ALERTA':
        mensaje = f"Alerta ({severidad}): "
        if proposicion.r < 0.3:
            mensaje += "La cobertura normativa es baja. "
        if proposicion.s < 0.3:
            mensaje += "No hay casos históricos similares. "
        if proposicion.o < 0.4:
            mensaje += "Las entidades no coinciden con los catálogos. "
        mensaje += f"Soporte computacional: {C:.2f}. "
        mensaje += "Revisar la evidencia manualmente antes de decidir."
    
    elif tipo == 'PROYECCION':
        mensaje = f"Proyección: basado en patrones históricos, se estima un movimiento de {entidades.get('monto', 'monto desconocido')} "
        mensaje += f"para el período. Soporte computacional: {C:.2f}."
    
    else:  # PATRON
        mensaje = f"Patrón detectado: se han registrado {entidades.get('frecuencia', 'varios')} eventos similares en el período. "
        mensaje += f"Considere consolidar o revisar políticas. Soporte computacional: {C:.2f}."
    
    return mensaje

# PRE: proposicion tiene métricas, C está calculado
# POST: retorna una acción sugerida
def sugerir_accion(proposicion, C):
    if proposicion.r < 0.3:
        return 'REVISAR_CUENTA'
    elif proposicion.o < 0.4:
        return 'CONSULTAR_CATALOGO'
    elif proposicion.v < 0.3:
        return 'VERIFICAR_TASA'
    elif proposicion.t < 0.3:
        return 'VALIDAR_PERIODO'
    elif C < 0.5:
        return 'CONSULTAR_EVIDENCIA'
    else:
        return 'REVISAR_CUENTA'  # Acción por defecto

# Después de interpretar una observación
proposicion_id = 'prop_20260825_001'
orientacion = dictum.orientar(proposicion_id)

print(orientacion.tipo)          # "SUGERENCIA"
print(orientacion.severidad)     # "INFORMATIVA"
print(orientacion.mensaje)
# "Sugerencia: la evidencia del 25/08/2026 del emisor J-123456789 al receptor J-987654321 por 10000.00 USD es consistente con Interpretación del hecho del 25/08/2026: por 10000.00 USD del emisor J-123456789 al receptor J-987654321. Soporte computacional: 0.86. Revisar y confirmar antes de contabilizar."

print(orientacion.soporte_computacional)  # 0.86
print(orientacion.accion_sugerida)        # "REVISAR_CUENTA"
print(orientacion.requiere_respuesta)     # True

def retroalimentar(orientacion_id, decision_contador):
    # 1. Obtener orientación original
    orientacion = obtener_orientacion(orientacion_id)
    
    # 2. Si el contador rechazó o modificó, ajustar pesos
    if decision_contador == 'RECHAZADA':
        # Reducir peso de s (similitud histórica) para este tipo de caso
        ajustar_peso('s', -0.05)
    elif decision_contador == 'MODIFICADA':
        # Registrar el caso modificado como nuevo caso CBR
        registrar_caso_cbr(orientacion, decision_contador)
    
    # 3. Registrar la decisión para futuras consultas
    registrar_decision(orientacion_id, decision_contador)


