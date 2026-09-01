<!--
SCFV v6 — Documento de Ingeniería
Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
Versión: 1.0.0
Fecha: 2026-08-26
Estado: APROBADO
ADR relacionados: ADR-004, ADR-003
-->

# Intellectus — Fase de Interpretación del Núcleo Epistemológico

## Propósito
El Intellectus es la segunda fase del Núcleo Epistemológico. Su responsabilidad es **interpretar una Observación** (generada por Perceptum), compararla con reglas, casos históricos y ontología, y producir una **Proposición** con las métricas de soporte computacional: **r (cobertura normativa), s (similitud histórica), o (consistencia ontológica), t (peso temporal) y v (volatilidad contextual)**.

**El Intellectus no decide ni orienta. Solo interpreta y mide.**

## Autoridad (ADR-004)
- **Epistemológica**: interpreta y calcula métricas, no decide.
- **Nunca** escribe en `negocio_*` ni en `auditoria_*`. Solo escribe en `epistemic_proposicion`.
- **Nunca** genera una orientación (eso es responsabilidad de Dictum).

## Entradas
- **Observacion**: objeto generado por Perceptum (con entidades y confianza por campo).
- **PCU**: Plan de Cuentas Único del mandante (versión vigente).
- **Casos CBR**: Base de casos históricos (decisiones previas del contador).
- **Catálogos**: productos, clientes, proveedores (si existen).
- **Parámetros**: tasa de cambio, inflación, ajustes por período.

## Salidas
- **Proposicion**: objeto que contiene:
  - `proposicion_id`: UUID.
  - `observacion_id`: referencia a la Observación original.
  - `interpretacion`: texto en lenguaje natural con la interpretación del hecho.
  - `r`: cobertura normativa (0.0 - 1.0).
  - `s`: similitud histórica (0.0 - 1.0).
  - `o`: consistencia ontológica (0.0 - 1.0).
  - `t`: peso temporal (0.0 - 1.0).
  - `v`: volatilidad contextual (0.0 - 1.0).
  - `evidencia_hash`: hash de la evidencia original.
  - `creado_en`: timestamp de creación.

## Métricas de Soporte Computacional

### r — Cobertura Normativa
Mide qué proporción de la observación coincide con reglas deterministas del diccionario de cuentas y normativa contable.

**Cálculo**:

r = (número de campos que coinciden con reglas normativas) / (número total de campos extraídos)


**Ejemplo**: Si la observación contiene "venta de mercancía" y el PCU tiene una cuenta "Ingresos por Ventas", y las reglas indican que se debita Clientes y se acredita Ingresos, entonces r es alto.

### s — Similitud Histórica
Mide la similitud de la observación con casos anteriores (CBR - Case-Based Reasoning) utilizando TF-IDF o similar.

**Cálculo**:

s = similitud_coseno(vector_observacion, vector_caso_historico)

```

**Ejemplo**: Si el contador ha registrado 50 ventas similares en el pasado, s será alto.

### o — Consistencia Ontológica
Mide si las entidades extraídas existen en los catálogos del mandante (PCU, productos, clientes, proveedores, RIF, etc.).

**Cálculo**:
```

o = (entidades_existentes) / (entidades_total)

```

**Ejemplo**: Si la observación menciona un RIF que no existe en el catálogo de proveedores, o será bajo.

### t — Peso Temporal
Asigna menor peso a casos históricos antiguos (decaimiento exponencial).

**Cálculo**:
```

t = e^(-λ * Δt)

```
donde Δt es la diferencia en días entre el caso histórico y la observación actual, y λ es una constante de decaimiento (ej. 0.001).

**Ejemplo**: Un caso de hace 30 días tiene t ≈ 0.97; uno de hace 365 días tiene t ≈ 0.69.

### v — Volatilidad Contextual
Ajusta la confianza según la volatilidad del entorno (inflación, tasa de cambio, cambios normativos).

**Cálculo**:
```

v = 1 - (volatilidad_observada / volatilidad_maxima_historica)

```

**Ejemplo**: En un entorno hiperinflacionario, v puede ser bajo para montos que no están indexados.

## Invariantes (Axiomas E-1, E-2, E-3)

| ID | Invariante | Verificación |
|----|------------|--------------|
| I-1 | `r, s, o, t, v ∈ [0.0, 1.0]` | Las métricas siempre están en el rango 0-1. |
| I-2 | Si `r == 0.0`, la interpretación no tiene base normativa | Se registra como "sin cobertura". |
| I-3 | Si `s == 0.0`, no hay casos históricos similares | Se registra como "caso nuevo". |
| I-4 | La similitud histórica no es evidencia (E-1) | El Intellectus no usa `s` para afirmar verdad, solo para medir similitud. |
| I-5 | El hash de la evidencia garantiza integridad (E-2) | Se referencia `evidencia_hash` de la Observación. |

## Dependencias

### Permitidas
- `db/repositories/epistemic_observacion.py`: para leer la Observación.
- `db/repositories/epistemic_proposicion.py`: para persistir la Proposición.
- `db/repositories/epistemic_casos_cbr.py`: para acceder a casos históricos.
- `db/repositories/negocio_pcu.py`: para validar cuentas y normativas.
- `db/repositories/negocio_catalogos.py`: para validar productos, clientes, proveedores.
- `utils/tfidf.py` o `utils/similitud.py`: para calcular similitud de casos.

### Prohibidas
- Cualquier módulo de `core/motor_contable/` (no escribe en Diario).
- Cualquier fractal de dominio (Ventas, Compras, etc.).
- Cualquier decisión final (se delega a Dictum y luego al contador).

## Componentes Internos

| Componente | Responsabilidad |
|------------|-----------------|
| **Validador Normativo** | Compara la observación con reglas del PCU y normativa (r). |
| **Buscador de Casos** | Busca casos similares en la base CBR (s). |
| **Validador Ontológico** | Verifica existencia de entidades en catálogos (o). |
| **Calculador Temporal** | Aplica decaimiento exponencial a casos antiguos (t). |
| **Calculador de Volatilidad** | Mide volatilidad contextual (v) según parámetros del período. |
| **Generador de Proposición** | Construye la proposición y la persiste en `epistemic_proposicion`. |

## Pseudo-código de Funciones Principales

### 1. `interpretar(observacion_id: str) -> Proposicion`

```python
# PRE: observacion_id existe en epistemic_observacion
# POST: retorna una Proposicion con r, s, o, t, v calculados
# INVARIANTE: todas las métricas están en [0.0, 1.0]
def interpretar(observacion_id):
    # 1. Obtener Observación
    observacion = obtener_observacion(observacion_id)
    
    # 2. Calcular r (cobertura normativa)
    r = calcular_r(observacion)
    
    # 3. Calcular s (similitud histórica)
    casos_similares, s = calcular_s(observacion)
    
    # 4. Calcular o (consistencia ontológica)
    o = calcular_o(observacion)
    
    # 5. Calcular t (peso temporal)
    t = calcular_t(casos_similares)
    
    # 6. Calcular v (volatilidad contextual)
    v = calcular_v(observacion)
    
    # 7. Generar interpretación en lenguaje natural
    interpretacion_texto = generar_interpretacion(observacion, r, s, o, t, v)
    
    # 8. Construir Proposición
    proposicion = {
        'proposicion_id': generar_uuid(),
        'observacion_id': observacion.observacion_id,
        'interpretacion': interpretacion_texto,
        'r': r,
        's': s,
        'o': o,
        't': t,
        'v': v,
        'evidencia_hash': observacion.evidencia_hash,
        'creado_en': timestamp_actual()
    }
    
    # 9. Persistir en epistemic_proposicion
    guardar_proposicion(proposicion)
    
    return proposicion
```

2. calcular_r(observacion) -> float

```python
# PRE: observacion tiene entidades y confianza
# POST: retorna r entre 0.0 y 1.0
# INVARIANTE: r es la proporción de campos que coinciden con reglas normativas
def calcular_r(observacion):
    entidades = observacion.entidades
    campos = list(entidades.keys())
    
    # Definir qué campos son relevantes para la normativa
    campos_normativos = ['fecha', 'monto', 'moneda', 'rif_emisor', 'rif_receptor']
    
    coincidencias = 0
    total = len(campos_normativos)
    
    for campo in campos_normativos:
        if campo in entidades and entidades[campo]:
            # Verificar que el campo coincida con alguna regla del PCU o normativa
            if validar_normativa(campo, entidades[campo]):
                coincidencias += 1
    
    r = coincidencias / total if total > 0 else 0.0
    return r
```

3. calcular_s(observacion) -> tuple[list, float]

```python
# PRE: observacion tiene entidades
# POST: retorna una tupla (casos_similares, s) donde s es la similitud máxima
# INVARIANTE: s está entre 0.0 y 1.0
def calcular_s(observacion):
    # 1. Obtener casos históricos (decisiones previas del contador)
    casos = obtener_casos_cbr()
    
    if not casos:
        return [], 0.0
    
    # 2. Vectorizar la observación actual
    vector_actual = vectorizar(observacion.entidades)
    
    # 3. Calcular similitud con cada caso
    similitudes = []
    for caso in casos:
        vector_caso = vectorizar(caso.entidades)
        sim = similitud_coseno(vector_actual, vector_caso)
        similitudes.append((caso, sim))
    
    # 4. Ordenar por similitud descendente
    similitudes.sort(key=lambda x: x[1], reverse=True)
    
    # 5. Tomar la similitud máxima como s
    s = similitudes[0][1] if similitudes else 0.0
    
    return similitudes, s
```

4. calcular_o(observacion) -> float

```python
# PRE: observacion tiene entidades
# POST: retorna o entre 0.0 y 1.0
# INVARIANTE: o es la proporción de entidades que existen en los catálogos
def calcular_o(observacion):
    entidades = observacion.entidades
    
    # Lista de campos a verificar en catálogos
    campos_ontologicos = ['rif_emisor', 'rif_receptor', 'productos', 'moneda']
    
    existentes = 0
    total = len(campos_ontologicos)
    
    for campo in campos_ontologicos:
        if campo in entidades and entidades[campo]:
            if existe_en_ontologia(campo, entidades[campo]):
                existentes += 1
    
    o = existentes / total if total > 0 else 0.0
    return o
```

5. calcular_t(casos_similares) -> float

```python
# PRE: casos_similares es una lista de tuplas (caso, similitud)
# POST: retorna t entre 0.0 y 1.0 (promedio ponderado por antigüedad)
# INVARIANTE: t es mayor para casos recientes
def calcular_t(casos_similares):
    if not casos_similares:
        return 0.0
    
    # Parámetro de decaimiento (λ = 0.001 por día)
    LAMBDA = 0.001
    fecha_actual = timestamp_actual()
    
    pesos = []
    for caso, sim in casos_similares[:10]:  # Solo los 10 más similares
        antiguedad = (fecha_actual - caso.fecha) / (24 * 3600)  # días
        peso = math.exp(-LAMBDA * antiguedad)
        pesos.append(peso)
    
    t = sum(pesos) / len(pesos) if pesos else 0.0
    return t
```

6. calcular_v(observacion) -> float

```python
# PRE: observacion tiene fecha y entidades
# POST: retorna v entre 0.0 y 1.0
# INVARIANTE: v es inversamente proporcional a la volatilidad del período
def calcular_v(observacion):
    # 1. Obtener período de la fecha
    periodo = obtener_periodo_por_fecha(observacion.fecha)
    
    if not periodo:
        return 0.5  # Valor neutral
    
    # 2. Obtener parámetros de volatilidad (inflación, tasa de cambio)
    volatilidad = obtener_volatilidad(periodo.id)
    
    # 3. Normalizar volatilidad en un rango 0-1
    volatilidad_maxima = 100.0  # Máximo histórico
    v = 1.0 - min(volatilidad / volatilidad_maxima, 1.0)
    
    return v
```

7. generar_interpretacion(observacion, r, s, o, t, v) -> str

```python
# PRE: todas las métricas están calculadas
# POST: retorna un texto en lenguaje natural explicando la interpretación
def generar_interpretacion(observacion, r, s, o, t, v):
    entidades = observacion.entidades
    
    texto = f"Interpretación del hecho del {entidades.get('fecha', 'fecha desconocida')}: "
    
    if entidades.get('monto'):
        texto += f"por {entidades['monto']} {entidades.get('moneda', 'moneda desconocida')} "
    
    if entidades.get('rif_emisor'):
        texto += f"del emisor {entidades['rif_emisor']} "
    
    if entidades.get('rif_receptor'):
        texto += f"al receptor {entidades['rif_receptor']} "
    
    texto += f"\n\nMétricas de soporte computacional:\n"
    texto += f"  • Cobertura normativa (r): {r:.2f}\n"
    texto += f"  • Similitud histórica (s): {s:.2f}\n"
    texto += f"  • Consistencia ontológica (o): {o:.2f}\n"
    texto += f"  • Peso temporal (t): {t:.2f}\n"
    texto += f"  • Volatilidad contextual (v): {v:.2f}\n"
    
    # Interpretación cualitativa
    if r > 0.7 and s > 0.7 and o > 0.7:
        texto += "\nAlta coherencia con reglas, casos y ontología."
    elif r < 0.3 and s < 0.3:
        texto += "\nBaja coherencia; posible hecho nuevo o atípico."
    elif o < 0.5:
        texto += "\nEntidades no reconocidas en los catálogos; verificar datos."
    
    return texto
```

Ejemplo de Uso

```python
# Después de extraer una observación
observacion_id = 'obs_20260825_001'
proposicion = intellectus.interpretar(observacion_id)

print(proposicion.interpretacion)
# "Interpretación del hecho del 25/08/2026: por 10000.00 USD del emisor J-123456789 al receptor J-987654321
# 
# Métricas de soporte computacional:
#   • Cobertura normativa (r): 0.85
#   • Similitud histórica (s): 0.92
#   • Consistencia ontológica (o): 0.80
#   • Peso temporal (t): 0.97
#   • Volatilidad contextual (v): 0.75
# 
# Alta coherencia con reglas, casos y ontología."
