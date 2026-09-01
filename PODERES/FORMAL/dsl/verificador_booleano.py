#!/usr/bin/env python3
"""
SCFV v7.0 - Verificador Booleano de Reglas .scfv
Versión definitiva: funciona con sintaxis antigua y nueva.
Autor: Domingo E. Díaz N.
"""
import re
import sys
from pathlib import Path

class VerificadorBooleano:
    def __init__(self, archivo_scfv):
        self.archivo = archivo_scfv
        self.reglas = []
        self.tabla_verdad = {}
        self._cargar_reglas()

    def _cargar_reglas(self):
        with open(self.archivo, 'r', encoding='utf-8') as f:
            texto = f.read()
        
        # Sintaxis nueva (TABLA_VERDAD ... ->)
        patron = r'(?:TABLA_VERDAD|REGLA)\s+(\w+):\s*(.+?)\s*(?:->|→)\s*(.*?)(?=\n\s*(?:TABLA_VERDAD|REGLA)|\Z)'
        bloques = re.findall(patron, texto, re.DOTALL | re.IGNORECASE)
        
        # Sintaxis antigua (SI ... ENTONCES)
        if not bloques:
            patron_antiguo = r'(?:TABLA_VERDAD|REGLA)\s+(\w+):\s*SI\s+(.+?)\s+ENTONCES\s+(.*?)(?=\n\s*(?:TABLA_VERDAD|REGLA)|\Z)'
            bloques = re.findall(patron_antiguo, texto, re.DOTALL | re.IGNORECASE)

        for nombre, condicion, acciones in bloques:
            condicion = condicion.replace(' Y ', ' and ')
            condicion = condicion.replace(' O ', ' or ')
            self.reglas.append({
                'nombre': nombre,
                'condicion': condicion.strip(),
                'acciones': acciones.strip()
            })

        if not self.reglas:
            print("⚠️ No se encontraron reglas en el archivo.")
        else:
            print(f"✅ Se encontraron {len(self.reglas)} regla(s).")

    def _extraer_comparaciones(self, condicion):
        """Extrae todas las comparaciones usando una regex robusta que maneja comillas."""
        # Limpiar paréntesis para simplificar
        cond_limpia = condicion.replace('(', ' ').replace(')', ' ')
        partes = re.split(r'\s+and\s+|\s+or\s+', cond_limpia)
        comparaciones = []
        for parte in partes:
            parte = parte.strip()
            if not parte:
                continue
            # Buscar variable, operador, valor (con o sin comillas)
            m = re.match(r'(\b[a-zA-Z_][a-zA-Z0-9_]*\b)\s*(==|!=|>|<|>=|<=)\s*(.+?)$', parte)
            if m:
                var, op, val = m.groups()
                val = val.strip()
                # Quitar comillas si las tiene
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                comparaciones.append((var, op, val))
        return comparaciones

    def _reemplazar_comparaciones(self, condicion, comparaciones):
        """Reemplaza cada comparación por C0, C1, ... usando regex flexible."""
        cond = condicion
        for idx, (var, op, val) in enumerate(comparaciones):
            # Construir patrones posibles
            patrones = [
                rf'{var}\s*{op}\s*"{val}"',
                rf'{var}\s*{op}\s*\'{val}\'',
                rf'{var}\s*{op}\s*{val}',
                rf'\({var}\s*{op}\s*"{val}"\)',
                rf'\({var}\s*{op}\s*\'{val}\'\)',
                rf'\({var}\s*{op}\s*{val}\)'
            ]
            # Ordenar por longitud descendente
            patrones = sorted(set(patrones), key=len, reverse=True)
            for patron in patrones:
                if re.search(patron, cond):
                    cond = re.sub(patron, f'C{idx}', cond)
                    break
            # Si no se encontró, usar reemplazo simple
            if f'C{idx}' not in cond:
                cond = re.sub(rf'{var}\s*{op}\s*{val}', f'C{idx}', cond)
        return cond

    def generar_tabla_verdad(self):
        if not self.reglas:
            return
        regla = self.reglas[0]
        comparaciones = self._extraer_comparaciones(regla['condicion'])
        if not comparaciones:
            print("⚠️ No se encontraron comparaciones en la condición.")
            return
        
        cond_transformada = self._reemplazar_comparaciones(regla['condicion'], comparaciones)
        # Convertir operadores lógicos a minúsculas
        cond_transformada = cond_transformada.replace(' AND ', ' and ')
        cond_transformada = cond_transformada.replace(' OR ', ' or ')
        cond_transformada = cond_transformada.replace(' AND', ' and')
        cond_transformada = cond_transformada.replace(' OR', ' or')
        cond_transformada = cond_transformada.replace('AND ', 'and ')
        cond_transformada = cond_transformada.replace('OR ', 'or ')
        
        print(f"🔍 Condición transformada: {cond_transformada}")
        
        n = len(comparaciones)
        combinaciones = []
        for i in range(1 << n):
            combo = {}
            for j in range(n):
                combo[f'C{j}'] = bool(i & (1 << j))
            combinaciones.append(combo)
        
        for combo in combinaciones:
            try:
                if eval(cond_transformada, {"__builtins__": {}}, combo):
                    self.tabla_verdad[tuple(combo.values())] = regla['nombre']
            except:
                pass

    def verificar_consistencia(self):
        if not self.tabla_verdad:
            print("⚠️ No hay tabla de verdad generada.")
            return False
        inconsistencias = False
        for combo, regla in self.tabla_verdad.items():
            for combo2, regla2 in self.tabla_verdad.items():
                if combo == combo2 and regla != regla2:
                    print(f"⚠️ Contradicción: {combo} → {regla} y {combo2} → {regla2}")
                    inconsistencias = True
        if not inconsistencias:
            print("✅ No hay contradicciones en las reglas.")
        return not inconsistencias

    def generar_reporte(self):
        reporte = f"Reporte de verificación booleana para {self.archivo}\n"
        reporte += "="*60 + "\n"
        if self.tabla_verdad:
            reporte += "Tabla de verdad:\n"
            for combo, regla in self.tabla_verdad.items():
                reporte += f"  {combo} → {regla}\n"
        else:
            reporte += "No se generó tabla de verdad.\n"
        return reporte

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python verificador_booleano.py archivo.scfv")
        sys.exit(1)
    verif = VerificadorBooleano(sys.argv[1])
    verif.generar_tabla_verdad()
    verif.verificar_consistencia()
    print(verif.generar_reporte())
