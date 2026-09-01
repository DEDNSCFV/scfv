#!/usr/bin/env python3
"""
SCFV v7.0 - Generador de Fractales .scfv (sintaxis antigua)
Autor: Domingo E. Díaz N.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import re
import json
from pathlib import Path
from PODERES.FORMAL.dsl.scfv_loader import SCFVLoader

class SCFVArchitect:
    def __init__(self):
        self.contexto = SCFVLoader.cargar_contexto()
        self.templates = self._cargar_templates()

    def _cargar_templates(self):
        template_path = Path("reglas/templates.json")
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "ventas": {
                "nombre": "VENTAS",
                "condicion": "monto > 0 Y tipo == \"venta\"",
                "acciones": [
                    "base = monto / (1 + IVA_TASA)",
                    "iva = monto - base",
                    "GENERAR CONSECUENCIA (cuenta=CUENTA_CAJA, naturaleza=DEUDORA, movimiento=AUMENTA, monto=monto)",
                    "GENERAR CONSECUENCIA (cuenta=CUENTA_VENTAS, naturaleza=ACREEDORA, movimiento=AUMENTA, monto=base)",
                    "GENERAR CONSECUENCIA (cuenta=CUENTA_IVA_PAGAR, naturaleza=ACREEDORA, movimiento=AUMENTA, monto=iva)"
                ]
            },
            "compras": {
                "nombre": "COMPRAS",
                "condicion": "monto > 0 Y tipo == \"compra\"",
                "acciones": [
                    "iva = monto * IVA_TASA / 100000000",
                    "total = monto + iva",
                    "GENERAR CONSECUENCIA (cuenta=CUENTA_INVENTARIO, naturaleza=DEUDORA, movimiento=AUMENTA, monto=monto)",
                    "GENERAR CONSECUENCIA (cuenta=CUENTA_IVA_COBRAR, naturaleza=DEUDORA, movimiento=AUMENTA, monto=iva)",
                    "GENERAR CONSECUENCIA (cuenta=CUENTA_PROVEEDORES, naturaleza=ACREEDORA, movimiento=AUMENTA, monto=total)"
                ]
            }
        }

    def generar_desde_template(self, template_key, nombre=None, variables_override=None):
        template = self.templates.get(template_key)
        if not template:
            print(f"⚠️ Template '{template_key}' no encontrado.")
            return
        nombre_fractal = nombre or template['nombre']
        contenido = f"FRACTAL {nombre_fractal} DOMINIO CONTABLE:\n\n"
        contenido += f"  REGLA {nombre_fractal}_BASE:\n"
        contenido += f"    SI {template['condicion']} ENTONCES\n"
        for accion in template['acciones']:
            contenido += f"      {accion}\n"
        if variables_override:
            for var, val in variables_override.items():
                contenido = contenido.replace(var, str(val))
        archivo_salida = f"reglas/{nombre_fractal.lower()}.scfv"
        with open(archivo_salida, 'w', encoding='utf-8') as f:
            f.write(contenido)
        print(f"✅ Fractal generado: {archivo_salida}")
        return archivo_salida

    def clonar_y_escalar(self, archivo_original, nuevo_nombre, factor_escala):
        with open(archivo_original, 'r', encoding='utf-8') as f:
            contenido = f.read()
        for var, nuevo_valor in factor_escala.items():
            contenido = contenido.replace(var, nuevo_valor)
        nombre_original = re.search(r'FRACTAL\s+(\w+)', contenido).group(1)
        contenido = contenido.replace(nombre_original, nuevo_nombre)
        archivo_salida = f"reglas/{nuevo_nombre.lower()}.scfv"
        with open(archivo_salida, 'w', encoding='utf-8') as f:
            f.write(contenido)
        print(f"✅ Fractal escalado generado: {archivo_salida}")
        return archivo_salida

    def validar(self, archivo):
        from PODERES.FORMAL.dsl.verificador_booleano import VerificadorBooleano
        verif = VerificadorBooleano(archivo)
        verif.generar_tabla_verdad()
        if verif.verificar_consistencia():
            print(f"✅ El archivo {archivo} es válido.")
        else:
            print(f"❌ El archivo {archivo} tiene inconsistencias.")

if __name__ == "__main__":
    arch = SCFVArchitect()
    if len(sys.argv) < 2:
        print("Uso: python scfv_architect.py [comando]")
        print("  --generar <template> [nombre]")
        print("  --clonar <original> <nuevo> <variable=valor>")
        print("  --validar <archivo>")
        sys.exit(1)
    comando = sys.argv[1]
    if comando == "--generar":
        template = sys.argv[2]
        nombre = sys.argv[3] if len(sys.argv) > 3 else None
        arch.generar_desde_template(template, nombre)
    elif comando == "--clonar":
        original = sys.argv[2]
        nuevo = sys.argv[3]
        factor = {}
        for item in sys.argv[4:]:
            k, v = item.split('=')
            factor[k.strip()] = v.strip()
        arch.clonar_y_escalar(original, nuevo, factor)
    elif comando == "--validar":
        arch.validar(sys.argv[2])
    else:
        print("⚠️ Comando no reconocido.")
