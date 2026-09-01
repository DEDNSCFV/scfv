#!/usr/bin/env python3
"""
SCFV v7.0 - Validador de Fractalidad, Endogeneidad, Inmanencia y Heterogeneidad
Autor: Domingo E. Díaz N.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import ast
import re
from pathlib import Path
from PODERES.FORMAL.dsl.scfv_loader import SCFVLoader

class SCFVValidator:
    def __init__(self):
        self.contexto = SCFVLoader.cargar_contexto()
        self.reglas = self._cargar_reglas()
        self.codigo_python = self._analizar_codigo_python()

    def _cargar_reglas(self):
        reglas = {}
        for f in Path("reglas").glob("*.scfv"):
            if f.name != "SCFV.scfv":
                with open(f, 'r', encoding='utf-8') as file:
                    reglas[f.name] = file.read()
        return reglas

    def _analizar_codigo_python(self):
        patrones = []
        for f in Path("src").rglob("*.py"):
            if "test" not in str(f) and "__pycache__" not in str(f):
                with open(f, 'r', encoding='utf-8') as file:
                    try:
                        tree = ast.parse(file.read())
                        for node in ast.walk(tree):
                            if isinstance(node, ast.If):
                                codigo = ast.unparse(node)
                                if re.search(r'naturaleza|movimiento|DEBE|HABER', codigo):
                                    patrones.append({
                                        "archivo": str(f),
                                        "linea": node.lineno,
                                        "codigo": codigo,
                                        "tipo": "condicional_contable"
                                    })
                    except:
                        pass
        return patrones

    def evaluar_fractalidad(self):
        # La fractalidad se mide por la presencia de reglas .scfv (independientemente de la sintaxis)
        total_reglas = len(self.reglas)
        # Consideramos que un sistema es 100% fractal si tiene al menos 1 regla .scfv (puedes ajustar)
        return min(100, total_reglas * 25)  # 1 regla = 25%, 2 = 50%, 3 = 75%, 4+ = 100%

    def evaluar_endogeneidad(self):
        lineas_scfv = sum(len(r.split('\n')) for r in self.reglas.values())
        lineas_python_contables = sum(1 for p in self.codigo_python if p['tipo'] == 'condicional_contable')
        total = lineas_scfv + lineas_python_contables
        return (lineas_scfv / total) * 100 if total > 0 else 0

    def generar_propuestas(self):
        propuestas = []
        endo = self.evaluar_endogeneidad()
        if endo < 80:
            propuestas.append("⚠️ La endogeneidad es baja. Migrar lógica contable de Python a .scfv.")
            for p in self.codigo_python[:3]:
                propuestas.append(f"  - En {p['archivo']}: línea {p['linea']} → puede convertirse a regla .scfv.")
        fractalidad = self.evaluar_fractalidad()
        if fractalidad < 50:
            propuestas.append("⚠️ La fractalidad es baja. Crear más fractales .scfv para cubrir dominios contables.")
        return propuestas

    def generar_reporte(self):
        reporte = "📊 INFORME DE VALIDACIÓN FRACTAL DEL SCFV\n"
        reporte += "="*60 + "\n"
        reporte += f"Fractalidad: {self.evaluar_fractalidad():.1f}%\n"
        reporte += f"Endogeneidad: {self.evaluar_endogeneidad():.1f}%\n"
        reporte += "\n📌 Propuestas:\n"
        for p in self.generar_propuestas():
            reporte += f"  - {p}\n"
        return reporte

if __name__ == "__main__":
    val = SCFVValidator()
    print(val.generar_reporte())
