# SCFV v7.0 - Manual de Usuario

## ¿Qué es el SCFV?

El **Sistema Contable Fractal Verificable (SCFV)** es una herramienta profesional para contadores que permite procesar lotes de facturas (archivos CSV) y generar automáticamente los libros legales (Diario, Mayor, Inventario), Estados Financieros (Balance, Resultados) y un informe de integridad con cadena de hash.

Está diseñado para ser:
- **Soberano**: todos los datos residen en tu dispositivo. No depende de internet ni de servidores externos.
- **Trazable**: cada asiento queda registrado con un hash que demuestra su integridad.
- **Configurable**: las reglas contables se escriben en archivos `.scfv` (lenguaje natural formalizado), sin necesidad de programar.

---

## Requisitos

- Python 3.8 o superior (recomendado: 3.13)
- Termux (Android) o cualquier sistema Linux / macOS / Windows (con WSL)

---

## Instalación

1. **Descomprimir el entregable**:
   ```bash
   tar -xzvf SCFV_v7.0_FINAL_DOCUMENTADO.tar.gz
   cd scfv_v6

1. **Descomprimir el entregable**:
   ```bash
   tar -xzvf SCFV_v7.0_FINAL_DOCUMENTADO.tar.gz
   cd scfv_v6
```

2. Instalar dependencias (opcional, pero recomendado para la TUI):
   ```bash
   pip install -r requirements.txt
   ```
3. Verificar que todo funciona:
   ```bash
   python run_lote.py examples/ejemplo_completo.csv
   ```

---

Estructura del archivo CSV

El sistema procesa archivos CSV con las siguientes columnas:

Columna Obligatoria Descripción
factura Sí Identificador único de la transacción.
rif Sí RIF del cliente (venta) o proveedor (compra).
monto Sí Monto total de la factura (en moneda local).
fecha Sí Fecha en formato YYYY-MM-DD.
tipo Sí compra o venta.
producto No Código del producto (para inventario).
cantidad No Cantidad (para inventario).
costo_unitario No Costo unitario (solo compras).

Ejemplo:

```csv
factura,rif,monto,fecha,tipo,producto,cantidad,costo_unitario
FAC-001,J-12345678,11200.0,2026-08-01,compra,PROD-A,10,500.0
FAC-002,V-98765432,5600.0,2026-08-02,venta,PROD-B,0,0
```

---

Uso básico

1. Procesar un lote de facturas

```bash
python run_lote.py ruta/a/tu_archivo.csv
```

El sistema procesará todas las líneas y generará un reporte de convergencias/divergencias.

2. Exportar los libros legales

```bash
python exportar_libros.py
```

Esto genera en la carpeta libros/:

· diario.csv (Libro Diario)
· mayor.csv (Libro Mayor)
· inventario.csv (Libro de Inventario)
· balance_general.csv
· estado_resultados.csv

3. Generar PDFs (opcional)

```bash
python generar_pdf.py
```

Convierte todos los CSV a PDFs listos para imprimir o entregar.

4. Abrir la interfaz TUI (recomendado)

```bash
python -m src.tui.main
```

La TUI te permite:

· Procesar lotes desde una interfaz gráfica en terminal.
· Visualizar los libros y EEFF en tablas.
· Editar reglas .scfv directamente.
· Ver el reporte de divergencias y los logs del sistema.

---

Personalización

Cambiar tasas, exenciones o cuentas

Edita el archivo reglas/SCFV.scfv. Allí se definen:

```scfv
CONTEXTO:
  NORMATIVO:
    IVA_TASA = 0.12
    ISLR_RETENCION_VENTAS = 0.01
    UMBRAL_RETENCION = 5000.0
    EXENCIONES = ["V-12345678"]

  CONTABLE:
    CUENTA_CAJA = "110101"
    CUENTA_VENTAS = "410101"
    CUENTA_IVA_PAGAR = "210201"
    ...
```

Crear o modificar un fractal

Los fractales están en reglas/*.scfv. Puedes editarlos para cambiar la lógica de negocio.

Ejemplo (ventas.scfv):

```scfv
FRACTAL VENTAS DOMINIO CONTABLE:

  REGLA VENTA_NACIONAL:
    SI monto > 0 Y tipo == "venta" ENTONCES
      base = monto / (1 + IVA_TASA)
      iva = monto - base
      GENERAR CONSECUENCIA (cuenta=CUENTA_CAJA, naturaleza=DEUDORA, movimiento=AUMENTA, monto=monto)
      GENERAR CONSECUENCIA (cuenta=CUENTA_VENTAS, naturaleza=ACREEDORA, movimiento=AUMENTA, monto=base)
      GENERAR CONSECUENCIA (cuenta=CUENTA_IVA_PAGAR, naturaleza=ACREEDORA, movimiento=AUMENTA, monto=iva)
```

---

Solución de problemas

Error: "No such file or directory: 'ejemplo_completo.csv'"

Asegúrate de que el archivo esté en la carpeta examples/ o usa la ruta completa.

Error: "ModuleNotFoundError: No module named 'src'"

Ejecuta el script desde el directorio raíz del proyecto (cd ~/scfv_v6).

Divergencias en el reporte

Revisa el archivo reporte_mensual.json. Te indicará qué líneas del CSV tienen errores y una sugerencia para corregirlos.

---

Soporte y contacto

Si tienes dudas o necesitas configuración personalizada, contacta al autor:

Domingo E. Díaz N. (C.P.C.)
C.P.C. Nº 183594
Registro: Distrito Capital, Venezuela

---

Licencia

Este software es de código abierto y gratuito. Puedes usarlo, copiarlo y modificarlo libremente.

---

¡Gracias por usar el SCFV! 🚀📊
