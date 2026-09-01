#!/usr/bin/env python3
"""
SCFV v8.0 - Script de actualización diaria de tasas de cambio
Ejecutar diariamente (cron) para mantener tasas actualizadas.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PODERES.CONTABLE.monedas.obtener_tasas import ObtenerTasasBCV

def main():
    print("🔄 Actualizando tasas de cambio desde BCV...")
    guardadas, errores = ObtenerTasasBCV.guardar_tasas()
    print(f"✅ Tasas guardadas: {guardadas}")
    if errores:
        print(f"⚠️ Errores: {errores}")
    return 0 if not errores else 1

if __name__ == "__main__":
    sys.exit(main())
