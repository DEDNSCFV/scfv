#!/usr/bin/env python3
"""
SCFV v6.3 - Generador de Libros en PDF
Autor: Domingo E. Díaz N.
"""
import csv
import os
from fpdf import FPDF

CARPETA_LIBROS = "libros"

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'SCFV v6.3 - Libro Legal', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def csv_a_pdf(nombre_csv, titulo):
    ruta_csv = os.path.join(CARPETA_LIBROS, nombre_csv)
    if not os.path.exists(ruta_csv):
        print(f"⚠️ {nombre_csv} no encontrado. Ejecuta exportar_libros.py primero.")
        return
    
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, titulo, 0, 1, 'C')
    pdf.ln(5)
    
    with open(ruta_csv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header:
            return
        
        # Ancho de columnas
        col_width = pdf.w / (len(header) + 1) - 10
        
        # Cabecera
        pdf.set_font('Arial', 'B', 10)
        for col in header:
            pdf.cell(col_width, 10, col, 1, 0, 'C')
        pdf.ln()
        
        # Datos
        pdf.set_font('Arial', '', 9)
        for row in reader:
            for i, item in enumerate(row):
                pdf.cell(col_width, 8, str(item)[:20], 1, 0, 'L' if i > 0 else 'C')
            pdf.ln()
    
    # Guardar
    ruta_pdf = os.path.join(CARPETA_LIBROS, nombre_csv.replace('.csv', '.pdf'))
    pdf.output(ruta_pdf)
    print(f"✅ {titulo} exportado a PDF: {ruta_pdf}")

def generar_todos_pdf():
    print("📄 Generando PDFs...")
    csv_a_pdf("diario.csv", "Libro Diario")
    csv_a_pdf("mayor.csv", "Libro Mayor")
    csv_a_pdf("balance_general.csv", "Balance General")
    csv_a_pdf("estado_resultados.csv", "Estado de Resultados")
    csv_a_pdf("inventario.csv", "Libro de Inventario")
    print("✅ Todos los PDFs generados en la carpeta 'libros/'.")

if __name__ == "__main__":
    os.makedirs(CARPETA_LIBROS, exist_ok=True)
    generar_todos_pdf()
