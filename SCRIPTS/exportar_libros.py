#!/usr/bin/env python3
"""
SCFV v6.3 - Exportador de Libros con redondeo a 8 decimales
"""
import sqlite3
import csv
import json
import os

DB_PATH = "scfv.db"
CARPETA_SALIDA = "libros"
ESCALA = 10 ** 8

def formatear(valor):
    """Redondea a 8 decimales para eliminar errores de truncamiento."""
    return f"{round(valor / ESCALA, 8):.8f}"

def crear_carpeta():
    os.makedirs(CARPETA_SALIDA, exist_ok=True)

def exportar_diario():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT asiento_id, correlation_id, total_debe, total_haber, hash_chain, timestamp
        FROM negocio_diario
        ORDER BY timestamp
    """)
    rows = cursor.fetchall()
    conn.close()
    archivo = os.path.join(CARPETA_SALIDA, "diario.csv")
    with open(archivo, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Asiento ID", "Correlation ID", "Total Debe", "Total Haber", "Hash Chain", "Timestamp"])
        for r in rows:
            writer.writerow([r[0], r[1], formatear(r[2]), formatear(r[3]), r[4], r[5]])
    print(f"✅ Diario exportado: {archivo} ({len(rows)} asientos)")

def exportar_mayor():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT payload FROM event_store WHERE tipo_evento = 'ASIENTO_REGISTRADO'")
    rows = cursor.fetchall()
    conn.close()
    saldos = {}
    for (payload_json,) in rows:
        asiento = json.loads(payload_json)
        for p in asiento.get('partidas', []):
            cuenta = p.get('cuenta', '')
            monto = p.get('monto', 0)
            ubicacion = p.get('ubicacion', '')
            if not cuenta:
                continue
            if cuenta not in saldos:
                saldos[cuenta] = {'debe': 0, 'haber': 0, 'saldo': 0}
            if ubicacion == 'DEBE':
                saldos[cuenta]['debe'] += monto
                saldos[cuenta]['saldo'] += monto
            elif ubicacion == 'HABER':
                saldos[cuenta]['haber'] += monto
                saldos[cuenta]['saldo'] -= monto
    archivo = os.path.join(CARPETA_SALIDA, "mayor.csv")
    with open(archivo, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Cuenta", "Total Debe", "Total Haber", "Saldo"])
        for cuenta, datos in sorted(saldos.items()):
            writer.writerow([cuenta, formatear(datos['debe']), formatear(datos['haber']), formatear(datos['saldo'])])
    print(f"✅ Mayor exportado: {archivo} ({len(saldos)} cuentas)")

def exportar_inventario():
    archivo_csv = os.path.join(CARPETA_SALIDA, "inventario.csv")
    with open(archivo_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Producto", "Cantidad", "Costo Promedio", "Última Fecha"])
        writer.writerow(["Producto A", 0, 0.0, ""])
    print(f"✅ Inventario exportado: {archivo_csv} (plantilla)")

if __name__ == "__main__":
    print("=== EXPORTACIÓN DE LIBROS LEGALES SCFV ===")
    crear_carpeta()
    exportar_diario()
    exportar_mayor()
    exportar_inventario()
    print(f"\n📁 Libros exportados en la carpeta: {CARPETA_SALIDA}/")
