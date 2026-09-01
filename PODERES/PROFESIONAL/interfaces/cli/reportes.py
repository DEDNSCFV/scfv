"""
SCFV v8.0 — Generador de Reportes (CSV, HTML, PDF)
"""
import csv
import calendar
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict

class GeneradorReportes:
    def __init__(self, db_connection):
        self.db = db_connection

    def _timestamp_rango(self, periodo_id: str):
        año, mes = map(int, periodo_id.split('-'))
        inicio = int(datetime(año, mes, 1).timestamp())
        ultimo_dia = calendar.monthrange(año, mes)[1]
        fin = int(datetime(año, mes, ultimo_dia, 23, 59, 59).timestamp())
        return inicio, fin

    def _obtener_saldos_mayor(self, periodo_id: str) -> dict:
        """Reconstruye el Mayor desde el Event Store para el período."""
        inicio, fin = self._timestamp_rango(periodo_id)
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT payload FROM event_store
            WHERE tipo_evento = 'ASIENTO_REGISTRADO'
            AND timestamp >= ? AND timestamp <= ?
        """, (inicio, fin))
        saldos = defaultdict(float)
        for (payload_json,) in cursor.fetchall():
            try:
                payload = json.loads(payload_json)
                for partida in payload.get('partidas', []):
                    cuenta = partida.get('cuenta')
                    monto = partida.get('monto', 0)
                    ubicacion = partida.get('ubicacion', '')
                    if ubicacion == 'DEBE':
                        saldos[cuenta] += monto
                    elif ubicacion == 'HABER':
                        saldos[cuenta] -= monto
                    else:
                        natura = partida.get('naturaleza', '')
                        mov = partida.get('movimiento', '')
                        if (natura == "DEUDORA" and mov == "AUMENTA") or \
                           (natura == "ACREEDORA" and mov == "DISMINUYE"):
                            saldos[cuenta] += monto
                        else:
                            saldos[cuenta] -= monto
            except:
                continue
        return dict(saldos)

    def _obtener_datos_diario(self, periodo_id):
        inicio, fin = self._timestamp_rango(periodo_id)
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT asiento_id, timestamp, total_debe, total_haber, hash_chain
            FROM negocio_diario
            WHERE timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp ASC
        """, (inicio, fin))
        return cursor.fetchall()

    def generar_csv_diario(self, periodo_id: str) -> str:
        filas = self._obtener_datos_diario(periodo_id)
        directorio = Path("libros")
        directorio.mkdir(exist_ok=True)
        archivo = directorio / f"diario_{periodo_id}.csv"
        with open(archivo, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Asiento ID", "Timestamp", "Total Debe", "Total Haber", "Hash Chain"])
            writer.writerows(filas)
        print(f"✅ CSV generado: {archivo}")
        return str(archivo)

    def generar_html_diario(self, periodo_id: str) -> str:
        filas = self._obtener_datos_diario(periodo_id)
        directorio = Path("libros")
        directorio.mkdir(exist_ok=True)
        archivo = directorio / f"diario_{periodo_id}.html"
        with open(archivo, 'w', encoding='utf-8') as f:
            f.write("<!DOCTYPE html><html><head><meta charset='UTF-8'>")
            f.write("<title>Diario {}</title>".format(periodo_id))
            f.write("<style>table{border-collapse:collapse;width:100%}th,td{border:1px solid #ddd;padding:8px;text-align:left}th{background-color:#4CAF50;color:white}</style>")
            f.write("</head><body><h1>Libro Diario - {}</h1>".format(periodo_id))
            f.write("<table><tr><th>Asiento ID</th><th>Timestamp</th><th>Total Debe</th><th>Total Haber</th><th>Hash Chain</th></tr>")
            for row in filas:
                f.write("<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(*row))
            f.write("</table></body></html>")
        print(f"✅ HTML generado: {archivo}")
        return str(archivo)

    def generar_pdf_diario(self, periodo_id: str) -> str:
        try:
            from fpdf import FPDF
            filas = self._obtener_datos_diario(periodo_id)
            directorio = Path("libros")
            directorio.mkdir(exist_ok=True)
            archivo = directorio / f"diario_{periodo_id}.pdf"
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=10)
            pdf.cell(200, 10, txt=f"Libro Diario - {periodo_id}", ln=True, align='C')
            pdf.ln(10)
            pdf.cell(40, 10, "Asiento ID", 1)
            pdf.cell(30, 10, "Timestamp", 1)
            pdf.cell(30, 10, "Total Debe", 1)
            pdf.cell(30, 10, "Total Haber", 1)
            pdf.cell(60, 10, "Hash Chain (corto)", 1)
            pdf.ln()
            for row in filas:
                pdf.cell(40, 8, str(row[0])[:8], 1)
                pdf.cell(30, 8, str(row[1]), 1)
                pdf.cell(30, 8, str(row[2])[:10], 1)
                pdf.cell(30, 8, str(row[3])[:10], 1)
                pdf.cell(60, 8, str(row[4])[:16] + "...", 1)
                pdf.ln()
            pdf.output(str(archivo))
            print(f"✅ PDF generado: {archivo}")
            return str(archivo)
        except ImportError:
            print("❌ fpdf no instalado. Ejecuta: pip install fpdf")
            return ""
        except Exception as e:
            print(f"❌ Error generando PDF: {e}")
            return ""

    def generar_csv_mayor(self, periodo_id: str) -> str:
        """Genera el Mayor real desde el Event Store."""
        saldos = self._obtener_saldos_mayor(periodo_id)
        directorio = Path("libros")
        directorio.mkdir(exist_ok=True)
        archivo = directorio / f"mayor_{periodo_id}.csv"
        with open(archivo, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Cuenta", "Saldo"])
            for cuenta, saldo in sorted(saldos.items()):
                writer.writerow([cuenta, saldo])
        print(f"✅ Mayor generado: {archivo}")
        return str(archivo)

    def generar_csv_inventario(self, periodo_id: str) -> str:
        """Genera reporte de inventario (stock y costo promedio)."""
        cursor = self.db.cursor()
        # Asegurar que la tabla existe, si no, crear
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='negocio_productos'")
        if not cursor.fetchone():
            print("⚠️ Tabla negocio_productos no existe. Creando...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS negocio_productos (
                    codigo TEXT PRIMARY KEY,
                    nombre TEXT,
                    stock_actual REAL DEFAULT 0,
                    costo_promedio REAL DEFAULT 0
                )
            """)
            self.db.commit()
        cursor.execute("""
            SELECT codigo, stock_actual, costo_promedio, nombre
            FROM negocio_productos
            ORDER BY codigo
        """)
        filas = cursor.fetchall()
        directorio = Path("libros")
        directorio.mkdir(exist_ok=True)
        archivo = directorio / f"inventario_{periodo_id}.csv"
        with open(archivo, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Producto", "Stock", "Costo Promedio", "Nombre"])
            for row in filas:
                writer.writerow(row)
        print(f"✅ Inventario generado: {archivo}")
        return str(archivo)

    def generar_csv_balance(self, periodo_id: str) -> str:
        """Genera Balance General desde el Mayor."""
        saldos = self._obtener_saldos_mayor(periodo_id)
        activo, pasivo, capital = 0, 0, 0
        for cuenta, saldo in saldos.items():
            if cuenta.startswith('1'):       # Activo
                activo += saldo
            elif cuenta.startswith('2'):     # Pasivo
                pasivo += saldo
            elif cuenta.startswith('3'):     # Capital
                capital += saldo
            elif cuenta.startswith('4'):     # Ingresos (parte del capital)
                capital += saldo
            elif cuenta.startswith('5'):     # Gastos (parte del capital)
                capital += saldo
        directorio = Path("libros")
        directorio.mkdir(exist_ok=True)
        archivo = directorio / f"balance_{periodo_id}.csv"
        with open(archivo, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Cuenta", "Saldo"])
            writer.writerow(["ACTIVO", activo])
            writer.writerow(["PASIVO", pasivo])
            writer.writerow(["CAPITAL", capital])
            writer.writerow(["TOTAL ACTIVO", activo])
            writer.writerow(["TOTAL PASIVO + CAPITAL", pasivo + capital])
        print(f"✅ Balance generado: {archivo}")
        return str(archivo)
