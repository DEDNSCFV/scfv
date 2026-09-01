#!/usr/bin/env python3
"""
SCFV v8.0 - Ingreso manual de tasas oficiales del BCV
Uso: python3 SCRIPTS/ingresar_tasas.py --usd 820.00 --eur 950.00 --cny 120.00
"""
import sys
import os
import json
import argparse
from datetime import date
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from PODERES.CONTABLE.monedas.obtener_tasas import ObtenerTasasBCV

def main():
    parser = argparse.ArgumentParser(description="Ingresar tasas oficiales del BCV")
    parser.add_argument("--usd", type=float, help="Tasa USD/VES")
    parser.add_argument("--eur", type=float, help="Tasa EUR/VES")
    parser.add_argument("--cny", type=float, help="Tasa CNY/VES")
    parser.add_argument("--try", type=float, dest="try_rate", help="Tasa TRY/VES")
    parser.add_argument("--rub", type=float, help="Tasa RUB/VES")
    parser.add_argument("--todas", action="store_true", help="Ingresar interactivamente todas las tasas")
    args = parser.parse_args()

    json_path = Path("PODERES/CONTABLE/monedas/tasas_oficiales.json")
    
    # Cargar tasas existentes
    if json_path.exists():
        with open(json_path, "r") as f:
            data = json.load(f)
    else:
        data = {"fecha": "", "tasas": {}}

    # Si --todas, pedir interactivamente
    if args.todas:
        print("📝 Ingresa las tasas del BCV para hoy:")
        for moneda in ["USD", "EUR", "CNY", "TRY", "RUB"]:
            valor = input(f"  {moneda}/VES: ")
            if valor:
                data["tasas"][moneda] = float(valor.replace(',', '.'))
    else:
        if args.usd: data["tasas"]["USD"] = args.usd
        if args.eur: data["tasas"]["EUR"] = args.eur
        if args.cny: data["tasas"]["CNY"] = args.cny
        if args.try_rate: data["tasas"]["TRY"] = args.try_rate
        if args.rub: data["tasas"]["RUB"] = args.rub

    if not data["tasas"]:
        print("❌ No se ingresó ninguna tasa.")
        sys.exit(1)

    data["fecha"] = date.today().isoformat()

    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Tasas guardadas para {data['fecha']}")

    # Guardar también en la base de datos
    print("🔄 Guardando en base de datos...")
    ObtenerTasasBCV.guardar_tasas()
    print("✅ Listo.")

if __name__ == "__main__":
    main()
