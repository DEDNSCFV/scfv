# SCFV v6.3 - Sistema Contable Fractal Verificable

## ¿Qué hace?
Procesa lotes de facturas (CSV) y genera:
- **Libro Diario** (cronológico)
- **Libro Mayor** (saldos por cuenta)
- **Inventario** (costo promedio ponderado)
- **Balance General** y **Estado de Resultados** (opcional)

## ¿Cómo usarlo?
1. Coloca tu archivo CSV en la carpeta `examples/`.
2. Ejecuta: `python run_lote.py examples/tu_archivo.csv`
3. Exporta los libros: `python exportar_libros.py`
4. Revisa el reporte de divergencias en `reporte_mensual.json`.

## Estructura del CSV
| Columna | Obligatoria | Descripción |
|---------|-------------|-------------|
| factura | Sí | Identificador único |
| rif | Sí | RIF del cliente/proveedor |
| monto | Sí | Monto total |
| fecha | Sí | Fecha (YYYY-MM-DD) |
| tipo | Sí | `compra` o `venta` |
| producto | No | Código de producto (para inventario) |
| cantidad | No | Cantidad (para inventario) |
| costo_unitario | No | Costo unitario (solo compras) |

## Personalización
- Edita `reglas/SCFV.scfv` para cambiar tasas, exenciones y cuentas.
- Los fractales están en `reglas/*.scfv` (lenguaje natural formalizado).

## Requisitos
- Python 3.8+ (Termux / Linux / macOS / Windows WSL)

## Contacto
Domingo E. Díaz N. (C.P.C.)
