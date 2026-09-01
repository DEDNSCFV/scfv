#!/usr/bin/env python3
"""
SCFV v6.3 - Generador Automático de Estados Financieros
Autor: Domingo E. Díaz N.
"""
import csv
import json
import os
from pathlib import Path

CARPETA_LIBROS = "libros"
CONTEXTO_FILE = "reglas/SCFV.scfv"

def cargar_clasificacion():
    """Extrae la clasificación de cuentas desde el contexto."""
    clasificacion = {}
    if not os.path.exists(CONTEXTO_FILE):
        print("⚠️ No se encontró reglas/SCFV.scfv. Usando clasificación por defecto.")
        return {}
    
    with open(CONTEXTO_FILE, 'r', encoding='utf-8') as f:
        texto = f.read()
    
    # Buscar sección CLASIFICACION
    import re
    match = re.search(r'CLASIFICACION:\s*([\s\S]*?)(?=\n\w+:|$)', texto)
    if match:
        bloque = match.group(1)
        for linea in bloque.split('\n'):
            if '=' in linea:
                clave, valor = linea.split('=', 1)
                clave = clave.strip()
                valor = valor.strip()
                try:
                    # Evaluar listas como ['110101', '140101']
                    if valor.startswith('['):
                        for cuenta in eval(valor):
                            clasificacion[cuenta] = clave
                except:
                    pass
    return clasificacion

def leer_mayor():
    """Lee el archivo mayor.csv y devuelve dict {cuenta: saldo}."""
    mayor_path = os.path.join(CARPETA_LIBROS, "mayor.csv")
    if not os.path.exists(mayor_path):
        print("⚠️ Primero ejecuta 'python exportar_libros.py' para generar el Mayor.")
        return {}
    
    saldos = {}
    with open(mayor_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cuenta = row['Cuenta']
            saldo = float(row['Saldo'])
            saldos[cuenta] = saldo
    return saldos

def generar_eeff():
    clasificacion = cargar_clasificacion()
    saldos = leer_mayor()
    
    if not saldos:
        return

    # Inicializar totales
    activo = pasivo = patrimonio = ingresos = gastos = 0.0
    
    for cuenta, saldo in saldos.items():
        cat = clasificacion.get(cuenta, 'NO_CLASIFICADA')
        if cat == 'ACTIVO':
            activo += saldo
        elif cat == 'PASIVO':
            pasivo += saldo
        elif cat == 'PATRIMONIO':
            patrimonio += saldo
        elif cat == 'INGRESO':
            ingresos += saldo
        elif cat == 'GASTO':
            gastos += saldo
        else:
            print(f"⚠️ Cuenta {cuenta} sin clasificar. Se omite.")
    
    utilidad_neta = ingresos - gastos
    patrimonio_ajustado = patrimonio + utilidad_neta

    # Balance General
    balance_file = os.path.join(CARPETA_LIBROS, "balance_general.csv")
    with open(balance_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Cuenta", "Monto"])
        writer.writerow(["ACTIVO", round(activo, 2)])
        writer.writerow(["PASIVO", round(pasivo, 2)])
        writer.writerow(["PATRIMONIO", round(patrimonio_ajustado, 2)])
        writer.writerow(["TOTAL", round(activo, 2)])
    print(f"✅ Balance General exportado: {balance_file}")

    # Estado de Resultados
    resultados_file = os.path.join(CARPETA_LIBROS, "estado_resultados.csv")
    with open(resultados_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Cuenta", "Monto"])
        writer.writerow(["INGRESOS", round(ingresos, 2)])
        writer.writerow(["GASTOS", round(gastos, 2)])
        writer.writerow(["UTILIDAD NETA", round(utilidad_neta, 2)])
    print(f"✅ Estado de Resultados exportado: {resultados_file}")

if __name__ == "__main__":
    os.makedirs(CARPETA_LIBROS, exist_ok=True)
    generar_eeff()
