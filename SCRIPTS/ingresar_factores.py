#!/usr/bin/env python3
"""
SCFV v8.0 - Ingreso manual de factor de inflación (IPC)
Uso: python3 SCRIPTS/ingresar_factores.py --factor 1.800 --ipc 180.0
"""
import sys
import os
import json
import argparse
from datetime import date
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from PODERES.CONTABLE.inflacion.factores import FactoresInflacion

def main():
    parser = argparse.ArgumentParser(description="Ingresar factor de inflación oficial")
    parser.add_argument("--factor", type=float, help="Factor acumulado (ej. 1.800)")
    parser.add_argument("--ipc", type=float, help="Índice de Precios al Consumidor (base 100)")
    parser.add_argument("--fecha", type=str, help="Fecha (YYYY-MM-DD). Por defecto hoy.")
    args = parser.parse_args()

    fecha = args.fecha if args.fecha else date.today().isoformat()
    json_path = Path("PODERES/CONTABLE/inflacion/factores_oficiales.json")

    if args.factor is None and args.ipc is None:
        print("📝 Ingresa el factor de inflación del BCV:")
        factor = input("Factor acumulado (ej. 1.800): ")
        if not factor:
            print("❌ Factor requerido.")
            sys.exit(1)
        args.factor = float(factor.replace(',', '.'))
        ipc_input = input("IPC (opcional, presiona Enter para omitir): ")
        args.ipc = float(ipc_input.replace(',', '.')) if ipc_input else None

    data = {
        "fecha": fecha,
        "factor": args.factor,
        "ipc": args.ipc if args.ipc else 100.0 * args.factor
    }

    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Factor guardado en manual para {fecha}: {data['factor']} (IPC: {data['ipc']})")

    # Guardar también en BD (para histórico)
    print("🔄 Guardando en base de datos...")
    FactoresInflacion.guardar_factor(fecha, data['factor'], data['ipc'])
    print("✅ Listo.")

if __name__ == "__main__":
    main()
