#!/usr/bin/env python3
"""
SCFV v8.0 - CLI (Command Line Interface)
Comandos: venta, compra, reporte, evidencia, salud
"""
import sys
import argparse
import sqlite3
from datetime import date
from pathlib import Path
import re

from PODERES.PROFESIONAL.interfaces.cli.integrador import Integrador
from PODERES.PROFESIONAL.interfaces.cli.reportes import GeneradorReportes

print("🔍 Cargando fractales...")
try:
    from DOMINIOS.ventas.ventas import FractalVentas
    from DOMINIOS.compras.compras import FractalCompras
    from DOMINIOS.inventario.inventario import FractalInventario
    from DOMINIOS.fiscal.fiscal import FractalFiscal
    FRACTALES = [FractalVentas, FractalCompras, FractalInventario, FractalFiscal]
    print(f"✅ Fractales cargados: {len(FRACTALES)}")
except Exception as e:
    print(f"❌ Error cargando fractales: {e}")
    FRACTALES = []

def validar_rif(rif: str) -> bool:
    # Formato: J-12345678 o V-98765432 (7 a 10 dígitos)
    return bool(re.match(r'^[JV]\s*-\s*\d{7,10}$', rif.strip()))

# ------------------------------------------------------------
# COMANDO: VENTA
# ------------------------------------------------------------
def cmd_venta(args):
    if args.monto <= 0:
        print("❌ El monto debe ser mayor que cero.")
        return
    if not validar_rif(args.rif):
        print("❌ RIF inválido. Formato esperado: J-12345678 o V-98765432")
        return
    integrador = Integrador(fractales=FRACTALES)
    evidencia = {
        "factura": args.factura,
        "rif": args.rif,
        "monto": args.monto,
        "fecha": args.fecha or date.today().isoformat(),
        "tipo": "venta",
        "producto": args.producto,
        "cantidad": args.cantidad,
        "costo_unitario": args.costo_unitario
    }
    try:
        resultado = integrador.procesar_evidencia(evidencia)
        if resultado["estado"] == "completado":
            print(f"✅ Venta registrada. Asiento: {resultado['asiento_id']}")
        else:
            print(f"⚠️ No se pudo completar el registro: {resultado}")
    except Exception as e:
        print(f"❌ Error al registrar la venta: {e}")
        print("   Verifica los datos y vuelve a intentarlo.")

# ------------------------------------------------------------
# COMANDO: COMPRA
# ------------------------------------------------------------
def cmd_compra(args):
    if args.monto <= 0:
        print("❌ El monto debe ser mayor que cero.")
        return
    if not validar_rif(args.rif):
        print("❌ RIF inválido. Formato esperado: J-12345678 o V-98765432")
        return
    integrador = Integrador(fractales=FRACTALES)
    evidencia = {
        "factura": args.factura,
        "rif": args.rif,
        "monto": args.monto,
        "fecha": args.fecha or date.today().isoformat(),
        "tipo": "compra",
        "producto": args.producto,
        "cantidad": args.cantidad,
        "costo_unitario": args.costo_unitario
    }
    try:
        resultado = integrador.procesar_evidencia(evidencia)
        if resultado["estado"] == "completado":
            print(f"✅ Compra registrada. Asiento: {resultado['asiento_id']}")
        else:
            print(f"⚠️ No se pudo completar el registro: {resultado}")
    except Exception as e:
        print(f"❌ Error al registrar la compra: {e}")
        print("   Verifica los datos y vuelve a intentarlo.")

# ------------------------------------------------------------
# COMANDO: REPORTE
# ------------------------------------------------------------
def cmd_reporte(args):
    conn = sqlite3.connect("scfv.db")
    generador = GeneradorReportes(conn)

    if args.tipo == "diario":
        if args.formato == "csv":
            generador.generar_csv_diario(args.periodo)
        elif args.formato == "html":
            generador.generar_html_diario(args.periodo)
        elif args.formato == "pdf":
            generador.generar_pdf_diario(args.periodo)
        print(f"✅ Reporte diario ({args.formato}) generado.")
    elif args.tipo == "mayor":
        generador.generar_csv_mayor(args.periodo)
        print("✅ Reporte mayor generado.")
    elif args.tipo == "inventario":
        generador.generar_csv_inventario(args.periodo)
        print("✅ Reporte inventario generado.")
    elif args.tipo == "balance":
        generador.generar_csv_balance(args.periodo)
        print("✅ Reporte balance generado.")
    else:
        print(f"❌ Tipo de reporte no soportado: {args.tipo}")
    conn.close()

# ------------------------------------------------------------
# COMANDO: EVIDENCIA (con fallback interactivo)
# ------------------------------------------------------------
def cmd_evidencia(args):
    ruta = Path(args.archivo)
    if not ruta.exists():
        print(f"❌ Archivo no encontrado: {ruta}")
        return

    ext = ruta.suffix.lower()
    tipo = 'desconocido'
    if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
        tipo = 'imagen'
    elif ext == '.pdf':
        tipo = 'pdf'
    elif ext == '.csv':
        tipo = 'csv'
    elif ext == '.json':
        tipo = 'json'
    elif ext == '.txt':
        tipo = 'texto'
    elif ext == '.xml':
        tipo = 'xml'

    print(f"📄 Procesando archivo {ruta.name} (tipo: {tipo})")

    if tipo == 'csv':
        try:
            from PODERES.PROFESIONAL.interfaces.loader.batch_processor import BatchProcessor
            bp = BatchProcessor()
            bp.procesar_csv(str(ruta))
        except ImportError as e:
            print(f"❌ Error cargando BatchProcessor: {e}")
        return

    if tipo == 'json':
        try:
            import json
            with open(ruta, 'r', encoding='utf-8') as f:
                data = json.load(f)
            integrador = Integrador(fractales=FRACTALES)
            res = integrador.procesar_evidencia(data)
            if res["estado"] == "completado":
                print(f"✅ JSON procesado. Asiento: {res['asiento_id']}")
            else:
                print(f"⚠️ {res}")
        except Exception as e:
            print(f"❌ Error procesando JSON: {e}")
        return

    if tipo == 'texto':
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                contenido = f.read()

            monto_match = re.search(r'(?i)monto\s*[:=]?\s*([\d,.]+)', contenido)
            rif_match = re.search(r'(?i)rif\s*[:=]?\s*([JV]\s*-\s*[\d]+)', contenido)
            factura_match = re.search(r'(?i)factura\s*[:=]?\s*([\w-]+)', contenido)
            fecha_match = re.search(r'(\d{4}-\d{2}-\d{2})', contenido)

            # ----- FALLBACK INTERACTIVO -----
            monto = float(monto_match.group(1).replace(',', '')) if monto_match else None
            if not monto or monto <= 0:
                try:
                    monto_input = input("💰 No se pudo extraer el monto. Ingresa el monto (ej. 1000): ")
                    monto = float(monto_input.replace(',', '').replace(' ', ''))
                except:
                    print("❌ Monto inválido. Operación cancelada.")
                    return

            rif = rif_match.group(1).replace(" ", "") if rif_match else None
            if not rif or not validar_rif(rif):
                try:
                    rif_input = input("📋 No se pudo extraer el RIF. Ingresa el RIF (ej. J-12345678): ")
                    rif = rif_input.strip()
                    if not validar_rif(rif):
                        print("❌ RIF inválido. Operación cancelada.")
                        return
                except:
                    print("❌ RIF inválido. Operación cancelada.")
                    return

            factura = factura_match.group(1) if factura_match else None
            if not factura:
                try:
                    factura_input = input("📄 No se pudo extraer la factura. Ingresa un identificador: ")
                    factura = factura_input.strip()
                except:
                    factura = "TXT-001"

            fecha = fecha_match.group(1) if fecha_match else date.today().isoformat()

            evidencia = {
                "factura": factura,
                "rif": rif,
                "monto": monto,
                "fecha": fecha,
                "tipo": "venta",
                "producto": "DESCONOCIDO",
                "cantidad": 1,
                "costo_unitario": 0
            }

            print(f"📋 Evidencia construida: {evidencia}")
            integrador = Integrador(fractales=FRACTALES)
            res = integrador.procesar_evidencia(evidencia)
            if res["estado"] == "completado":
                print(f"✅ Texto procesado. Asiento: {res['asiento_id']}")
            else:
                print(f"⚠️ {res}")
        except Exception as e:
            print(f"❌ Error procesando texto: {e}")
        return

    if tipo in ['imagen', 'pdf']:
        try:
            from PODERES.EPISTEMOLOGICO.perceptum.perceptum import Perceptum
            print("🧠 Extrayendo entidades con Perceptum...")
            evidencia = {"tipo": tipo, "archivo": str(ruta)}
            observacion = Perceptum.extraer(evidencia)
            integrador = Integrador(fractales=FRACTALES)
            res = integrador.procesar_evidencia(observacion)
            if res["estado"] == "completado":
                print(f"✅ {tipo.capitalize()} procesado. Asiento: {res['asiento_id']}")
            else:
                print(f"⚠️ {res}")
        except ImportError as e:
            print(f"⚠️ Perceptum no disponible: {e}")
            print("   Para habilitar OCR/PDF: pip install pypdf pytesseract")
            print("   Para imágenes: pkg install tesseract")
        except Exception as e:
            print(f"❌ Error en Perceptum: {e}")
        return

    print(f"⚠️ Formato no soportado: {ext}")

# ------------------------------------------------------------
# COMANDO: SALUD
# ------------------------------------------------------------
def cmd_salud(args):
    """Verifica la integridad del sistema."""
    print("🔍 Verificando salud del sistema...")

    # 1. Verificar hash chain
    try:
        integrador = Integrador(fractales=FRACTALES)
        estado, mensaje = integrador.event_store.verificar_cadena()
        if estado:
            print("✅ Hash chain: Íntegra")
        else:
            print(f"❌ Hash chain: {mensaje}")
    except Exception as e:
        print(f"❌ Error verificando hash chain: {e}")

    # 2. Verificar tablas necesarias
    conn = sqlite3.connect("scfv.db")
    cursor = conn.cursor()
    tablas = ["event_store", "negocio_diario", "negocio_monedas", "negocio_tasas_cambio", "negocio_inflacion"]
    for tabla in tablas:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tabla,))
        if cursor.fetchone():
            print(f"✅ Tabla {tabla}: existe")
        else:
            print(f"⚠️ Tabla {tabla}: no existe (puede crearse automáticamente)")
    conn.close()

    # 3. Últimas tasas
    try:
        conn = sqlite3.connect("scfv.db")
        cursor = conn.cursor()
        cursor.execute("SELECT moneda_origen, tasa, fecha_valor FROM negocio_tasas_cambio ORDER BY fecha_valor DESC LIMIT 3")
        tasas = cursor.fetchall()
        if tasas:
            print("📊 Últimas tasas guardadas:")
            for moneda, tasa, fecha in tasas:
                print(f"   {moneda}: {tasa} ({fecha})")
        else:
            print("⚠️ No hay tasas registradas.")
        conn.close()
    except Exception as e:
        print(f"⚠️ Error consultando tasas: {e}")

    # 4. Último factor de inflación
    try:
        conn = sqlite3.connect("scfv.db")
        cursor = conn.cursor()
        cursor.execute("SELECT fecha, factor, ipc FROM negocio_inflacion ORDER BY fecha DESC LIMIT 1")
        factor = cursor.fetchone()
        if factor:
            print(f"📈 Último factor de inflación: {factor[0]} → factor {factor[1]} (IPC: {factor[2]})")
        else:
            print("⚠️ No hay factores de inflación registrados.")
        conn.close()
    except Exception as e:
        print(f"⚠️ Error consultando inflación: {e}")

    print("✅ Verificación completada.")

# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="SCFV v8.0")
    subparsers = parser.add_subparsers(dest="comando")

    p_venta = subparsers.add_parser("venta")
    sub_venta = p_venta.add_subparsers(dest="subcomando")
    venta_reg = sub_venta.add_parser("registrar")
    venta_reg.add_argument("--factura", required=True)
    venta_reg.add_argument("--rif", required=True)
    venta_reg.add_argument("--monto", type=float, required=True)
    venta_reg.add_argument("--fecha", default=None)
    venta_reg.add_argument("--producto", required=True)
    venta_reg.add_argument("--cantidad", type=int, default=1)
    venta_reg.add_argument("--costo_unitario", type=float, default=0.0)
    venta_reg.set_defaults(func=cmd_venta)

    p_compra = subparsers.add_parser("compra")
    sub_compra = p_compra.add_subparsers(dest="subcomando")
    compra_reg = sub_compra.add_parser("registrar")
    compra_reg.add_argument("--factura", required=True)
    compra_reg.add_argument("--rif", required=True)
    compra_reg.add_argument("--monto", type=float, required=True)
    compra_reg.add_argument("--fecha", default=None)
    compra_reg.add_argument("--producto", required=True)
    compra_reg.add_argument("--cantidad", type=int, default=1)
    compra_reg.add_argument("--costo_unitario", type=float, required=True)
    compra_reg.set_defaults(func=cmd_compra)

    p_reporte = subparsers.add_parser("reporte")
    p_reporte.add_argument("periodo")
    p_reporte.add_argument("tipo", choices=["diario", "mayor", "inventario", "balance"])
    p_reporte.add_argument("formato", nargs="?", default="csv", choices=["csv", "html", "pdf"])
    p_reporte.set_defaults(func=cmd_reporte)

    p_evidencia = subparsers.add_parser("evidencia")
    p_evidencia.add_argument("archivo")
    p_evidencia.set_defaults(func=cmd_evidencia)

    p_salud = subparsers.add_parser("salud", help="Verificar integridad del sistema")
    p_salud.set_defaults(func=cmd_salud)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
