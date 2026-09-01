#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from PODERES.PROFESIONAL.interfaces.loader.batch_processor import BatchProcessor

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python run_lote.py archivo.csv")
        sys.exit(1)

    ruta = sys.argv[1]
    bp = BatchProcessor()
    reporte = bp.procesar_csv(ruta)

    print(f"\n=== RESUMEN ===")
    print(f"Total filas: {reporte['total']}")
    print(f"Procesadas OK: {len(reporte['convergencias'])}")
    print(f"Divergencias: {len(reporte['divergencias'])}")
    print(f"Hash final: {reporte['hash_final'][:16]}...")
    if reporte['divergencias']:
        print("\n⚠️ Hay divergencias. Revisa 'reporte_mensual.json'.")
    else:
        print("\n✅ ¡Todo el lote fue procesado exitosamente!")
