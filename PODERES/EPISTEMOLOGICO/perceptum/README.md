<!--
SCFV v6 — Documento de Ingeniería
Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
Versión: 1.0.0
Fecha: 2026-08-26
Estado: APROBADO
ADR relacionados: ADR-004, ADR-003
-->

# Perceptum — Fase de Extracción del Núcleo Epistemológico

## Propósito
El Perceptum es la primera fase del Núcleo Epistemológico. Su responsabilidad es **extraer entidades estructuradas** de la evidencia (PDF, imagen, XML, texto, manuscrito) y producir una `Observacion` con un nivel de confianza por campo.

**El Perceptum no interpreta ni decide. Solo observa y mide.**

## Autoridad (ADR-004)
- **Epistemológica**: extrae información, no la valida ni la decide.
- **Nunca** escribe en `negocio_*` ni en `auditoria_*`. Solo escribe en `epistemic_observacion`.
- **Nunca** genera un asiento ni modifica datos contables.

## Entradas
- **Evidencia**: archivo (PDF, imagen JPG/PNG, XML, TXT, CSV) o texto ingresado por el contador.
- **Metadatos** (opcional): tipo de evidencia, contexto, instrucciones de extracción.

## Salidas
- **Observacion**: objeto estructurado con:
  - `evidencia_hash`: SHA-256 del archivo (garantiza integridad).
  - `tipo_evidencia`: PDF, IMAGEN, XML, TEXTO, MANUSCRITO, CSV.
  - `entidades`: JSON con los datos extraídos (fecha, monto, moneda, RIF, productos, descripción, tasa, etc.).
  - `confianza`: JSON con la confianza por campo (0.0 a 1.0).
  - `metadatos`: información del proceso (OCR usado, resolución, tiempo, etc.).
  - `fecha_extraccion`: timestamp de cuando se realizó la extracción.

## Invariantes (Axiomas E-1, E-2, E-3)

| ID | Invariante | Verificación |
|----|------------|--------------|
| I-1 | `evidencia_hash` es SHA-256 del archivo original | Se calcula antes de extraer. |
| I-2 | `confianza` tiene la misma estructura que `entidades` | Mismos campos; si no se extrajo, confianza = 0.0. |
| I-3 | Ningún campo de `confianza` es NULL | Se inicializa con 0.0 y se actualiza según extracción. |
| I-4 | El Perceptum no decide sobre la veracidad del hecho | Solo extrae; la decisión es del contador. |

## Dependencias

### Permitidas
- `db/repositories/epistemic_observacion.py`: para persistir la observación.
- `audit/hash_chain.py`: para registrar el hash de integridad de la evidencia.
- Librerías de extracción: `pypdf`, `pytesseract` (OCR), `xml.etree`, `csv`, `re` (regex).

### Prohibidas
- Cualquier módulo de `core/motor_contable/` (no escribe en Diario).
- Cualquier fractal de dominio (Ventas, Compras, etc.).
- Cualquier decisión o interpretación (se delega a Intellectus).

## Componentes Internos

| Componente | Responsabilidad |
|------------|-----------------|
| **Detector de Tipo** | Identifica el tipo de archivo (PDF, imagen, XML, CSV, texto). |
| **Extractor de Texto** | Extrae texto bruto del archivo (OCR para imágenes, parseo para PDF). |
| **Analizador Semántico** | Usa regex o NLP ligero para identificar entidades (fechas, montos, RIF, etc.). |
| **Calculador de Confianza** | Asigna confianza a cada campo según la calidad de la extracción. |
| **Generador de Observación** | Construye el objeto `Observacion` y lo persiste en `epistemic_observacion`. |

## Pseudo-código de Funciones Principales

### 1. `extraer(archivo: str, metadatos: dict) -> Observacion`

```python
# PRE: archivo existe y es accesible
# POST: retorna una Observacion con entidades extraídas y confianza por campo
# INVARIANTE: la observación queda persistida en epistemic_observacion
def extraer(archivo, metadatos=None):
    # 1. Calcular hash de integridad
    evidencia_hash = calcular_sha256(archivo)
    
    # 2. Detectar tipo de archivo
    tipo = detectar_tipo(archivo)
    
    # 3. Extraer texto bruto según tipo
    texto_bruto = extraer_texto(archivo, tipo)
    
    # 4. Analizar semánticamente (extraer entidades)
    entidades = analizar(texto_bruto)
    
    # 5. Calcular confianza por campo
    confianza = calcular_confianza(entidades, texto_bruto, tipo)
    
    # 6. Registrar en hash chain (integridad)
    hash_chain_id = registrar_hash_chain('epistemic_observacion', evidencia_hash)
    
    # 7. Construir Observacion
    observacion = {
        'observacion_id': generar_uuid(),
        'evidencia_hash': evidencia_hash,
        'evidencia_ruta': archivo,
        'fecha_extraccion': timestamp_actual(),
        'tipo_evidencia': tipo,
        'entidades': entidades,
        'confianza': confianza,
        'metadatos': metadatos or {},
        'hash_chain_id': hash_chain_id
    }
    
    # 8. Persistir en epistemic_observacion
    guardar_observacion(observacion)
    
    return observacion

# PRE: archivo existe
# POST: retorna 'PDF', 'IMAGEN', 'XML', 'CSV', 'TEXTO', 'MANUSCRITO'
# INVARIANTE: siempre retorna un tipo válido
def detectar_tipo(archivo):
    extension = archivo.split('.')[-1].lower()
    if extension in ['pdf']:
        return 'PDF'
    elif extension in ['jpg', 'jpeg', 'png', 'bmp', 'tiff']:
        return 'IMAGEN'
    elif extension in ['xml']:
        return 'XML'
    elif extension in ['csv', 'tsv']:
        return 'CSV'
    elif extension in ['txt', 'md']:
        return 'TEXTO'
    else:
        # Si no se reconoce, tratar como texto (el contador puede ingresar manualmente)
        return 'TEXTO'

# PRE: archivo existe y tipo es válido
# POST: retorna el texto bruto extraído
# INVARIANTE: el texto es una representación aproximada del contenido
def extraer_texto(archivo, tipo):
    if tipo == 'PDF':
        return extraer_pdf(archivo)
    elif tipo == 'IMAGEN':
        return extraer_ocr(archivo)  # Usa Tesseract en Termux
    elif tipo == 'XML':
        return extraer_xml(archivo)
    elif tipo == 'CSV':
        return extraer_csv(archivo)
    else:  # TEXTO, MANUSCRITO
        with open(archivo, 'r', encoding='utf-8') as f:
            return f.read()

# PRE: texto es una cadena no vacía
# POST: retorna un diccionario con las entidades encontradas
# INVARIANTE: si no se encuentra una entidad, el campo se deja vacío
def analizar(texto):
    entidades = {
        'fecha': extraer_fecha(texto),
        'monto': extraer_monto(texto),
        'moneda': extraer_moneda(texto),
        'rif_emisor': extraer_rif(texto),
        'rif_receptor': extraer_rif(texto, receptor=True),
        'productos': extraer_productos(texto),
        'descripcion': extraer_descripcion(texto),
        'tasa_cambio': extraer_tasa_cambio(texto)
    }
    return entidades

def extraer_fecha(texto):
    # Busca patrones de fecha: DD/MM/YYYY, YYYY-MM-DD, etc.
    patrones = [
        r'(\d{2}/\d{2}/\d{4})',
        r'(\d{4}-\d{2}-\d{2})',
        r'(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})'
    ]
    for patron in patrones:
        match = re.search(patron, texto)
        if match:
            return match.group(1)
    return ''

def extraer_monto(texto):
    # Busca montos con símbolos de moneda
    patrones = [
        r'[\$\€\£]\s*(\d{1,3}(?:\.\d{3})*,\d{2})',  # $ 1.000,00
        r'(\d{1,3}(?:\.\d{3})*,\d{2})\s*[\$\€\£]',
        r'(\d+\.\d{2})\s*(?:USD|EUR|VES)'
    ]
    for patron in patrones:
        match = re.search(patron, texto)
        if match:
            return match.group(1)
    return ''

def extraer_rif(texto, receptor=False):
    # Busca RIF venezolano: J-123456789, V-12345678, etc.
    patron = r'([JjVvEeGg]\s*-\s*\d{6,10})'
    matches = re.findall(patron, texto)
    if matches:
        return matches[1] if receptor else matches[0]
    return ''

# PRE: entidades contiene los campos extraídos
# POST: retorna un diccionario con confianza por campo (0.0 - 1.0)
# INVARIANTE: la confianza nunca es > 1.0
def calcular_confianza(entidades, texto, tipo):
    confianza = {}
    
    # Factor base según tipo de evidencia
    factor_base = {
        'PDF': 0.90,
        'XML': 0.95,
        'CSV': 0.95,
        'IMAGEN': 0.70,  # OCR puede tener errores
        'TEXTO': 0.80,
        'MANUSCRITO': 0.60  # El más bajo
    }[tipo]
    
    for campo, valor in entidades.items():
        if valor:
            # Si el valor fue extraído, la confianza es factor_base
            # menos penalizaciones por: longitud del texto, caracteres extraños, etc.
            confianza[campo] = factor_base
        else:
            confianza[campo] = 0.0
    
    return confianza

# El contador sube una factura PDF
archivo = '/data/mandante_A/evidencias/factura_1234.pdf'
metadatos = {'cliente': 'Comercial XYZ', 'emisor': 'Proveedor ABC'}

observacion = perceptum.extraer(archivo, metadatos)

print(observacion.entidades)
# {
#   'fecha': '25/08/2026',
#   'monto': '10000.00',
#   'moneda': 'USD',
#   'rif_emisor': 'J-123456789',
#   'rif_receptor': 'J-987654321',
#   'productos': ['Harina x10'],
#   'descripcion': 'Compra de harina al crédito',
#   'tasa_cambio': ''
# }

print(observacion.confianza)
# {
#   'fecha': 0.90,
#   'monto': 0.90,
#   'moneda': 0.90,
#   'rif_emisor': 0.85,
#   'rif_receptor': 0.80,
#   'productos': 0.85,
#   'descripcion': 0.90,
#   'tasa_cambio': 0.0
# }


