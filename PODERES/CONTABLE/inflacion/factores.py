"""
SCFV v8.0 - Módulo de Inflación (NIC 29)
Con soporte para entrada manual oficial.
"""
import sqlite3
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json

class FactoresInflacion:

    @classmethod
    def _factor_manual(cls, fecha_buscar: str = None) -> Optional[Dict]:
        """Lee factor oficial ingresado manualmente desde JSON."""
        json_path = Path(__file__).parent / "factores_oficiales.json"
        if json_path.exists():
            try:
                with open(json_path, "r") as f:
                    data = json.load(f)
                fecha_archivo = data.get("fecha", "")
                if fecha_buscar is None or fecha_archivo == fecha_buscar:
                    return data
                else:
                    # Si la fecha del archivo no coincide, no usarlo
                    return None
            except Exception as e:
                print(f"⚠️ Error leyendo archivo manual: {e}")
        return None

    @classmethod
    def obtener_factor(cls, fecha: str, db_path: str = "scfv.db") -> Optional[float]:
        """Obtiene factor: primero manual (si existe y coincide fecha), luego BD."""
        # 1. Intentar manual
        manual = cls._factor_manual(fecha)
        if manual:
            return manual.get("factor")
        # 2. Buscar en BD
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT factor FROM negocio_inflacion WHERE fecha <= ? ORDER BY fecha DESC LIMIT 1", (fecha,))
        resultado = cursor.fetchone()
        conn.close()
        return resultado[0] if resultado else None

    @classmethod
    def cargar_factores(cls, db_path: str = "scfv.db") -> Dict[str, float]:
        """Carga todos los factores desde la BD (ignora manual)."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT fecha, factor FROM negocio_inflacion ORDER BY fecha")
        resultados = cursor.fetchall()
        conn.close()
        return {fecha: factor for fecha, factor in resultados}

    @classmethod
    def guardar_factor(cls, fecha: str, factor: float, ipc: float = None, db_path: str = "scfv.db"):
        if ipc is None:
            ipc = 100.0 * factor
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO negocio_inflacion (fecha, factor, ipc, fuente)
            VALUES (?, ?, ?, 'MANUAL')
        """, (fecha, factor, ipc))
        conn.commit()
        conn.close()
        print(f"✅ Factor guardado en BD para {fecha}: {factor} (IPC: {ipc})")

    @classmethod
    def factor_reexpresion(cls, fecha_original: str, fecha_cierre: str, db_path: str = "scfv.db") -> float:
        factor_original = cls.obtener_factor(fecha_original, db_path)
        factor_cierre = cls.obtener_factor(fecha_cierre, db_path)
        if factor_original is None or factor_cierre is None:
            raise ValueError(f"No hay factores para {fecha_original} o {fecha_cierre}")
        return factor_cierre / factor_original

    @classmethod
    def reexpresar_saldo(cls, saldo: float, fecha_original: str, fecha_cierre: str, db_path: str = "scfv.db") -> float:
        factor = cls.factor_reexpresion(fecha_original, fecha_cierre, db_path)
        return saldo * factor

    @classmethod
    def cargar_factores_desde_csv(cls, ruta_csv: str, db_path: str = "scfv.db"):
        import csv
        with open(ruta_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cls.guardar_factor(row['fecha'], float(row['factor']), float(row.get('ipc', 0)), db_path)
        print("✅ Factores cargados desde CSV.")
