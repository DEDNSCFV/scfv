"""
SCFV v8.0 - Módulo de obtención de tasas de cambio
Prioriza entrada manual oficial. Si no hay, intenta APIs.
"""
import json
import sqlite3
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import urllib.request
import urllib.error

class ObtenerTasasBCV:
    MONEDAS_SOPORTADAS = ['USD', 'EUR', 'CNY', 'TRY', 'RUB', 'VES']

    @classmethod
    def _tasas_manuales(cls) -> Dict[str, float]:
        """Lee tasas oficiales ingresadas manualmente desde JSON."""
        json_path = Path(__file__).parent / "tasas_oficiales.json"
        if json_path.exists():
            try:
                with open(json_path, "r") as f:
                    data = json.load(f)
                fecha_archivo = data.get("fecha", "")
                hoy = date.today().isoformat()
                if fecha_archivo == hoy:
                    tasas = data.get("tasas", {})
                    if tasas:
                        tasas['VES'] = 1.0
                        return tasas
                else:
                    print(f"⚠️ Archivo manual tiene fecha {fecha_archivo}, hoy es {hoy}. Usando fallback.")
            except Exception as e:
                print(f"⚠️ Error leyendo archivo manual: {e}")
        return {}

    @classmethod
    def obtener_tasas(cls) -> Dict[str, float]:
        """Obtiene tasas: primero manual, luego APIs, luego fallback."""
        # 1. Intentar manual
        manual = cls._tasas_manuales()
        if manual:
            print("✅ Usando tasas oficiales ingresadas manualmente.")
            return manual

        # 2. Intentar APIs (solo como respaldo, pero ya sabemos que fallan)
        try:
            url = "https://bcv-api.rafnixg.dev/rates/"
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                tasas = cls._procesar_respuesta(data, "rafnixg")
                if tasas:
                    print("✅ Tasas obtenidas desde API (respaldo).")
                    return tasas
        except Exception:
            pass

        # 3. Fallback final (tasas fijas)
        print("⚠️ No hay tasas manuales ni API. Usando fallback (¡actualiza manualmente!).")
        return cls._tasas_fallback()

    @classmethod
    def _procesar_respuesta(cls, data: dict, parser: str) -> Dict[str, float]:
        tasas = {}
        if parser == "rafnixg":
            for moneda in cls.MONEDAS_SOPORTADAS:
                moneda_lower = moneda.lower()
                if moneda_lower in data:
                    tasas[moneda] = float(data[moneda_lower])
                elif moneda in data:
                    tasas[moneda] = float(data[moneda])
        tasas['VES'] = 1.0
        return tasas

    @classmethod
    def _tasas_fallback(cls) -> Dict[str, float]:
        return {
            'USD': 798.326,
            'EUR': 926.55312212,
            'CNY': 118.81265626,
            'TRY': 16.54335365,
            'RUB': 9.25863728,
            'VES': 1.0
        }

    @classmethod
    def guardar_tasas(cls, db_path: str = "scfv.db") -> Tuple[int, List[str]]:
        """Obtiene y guarda las tasas en la base de datos."""
        tasas = cls.obtener_tasas()
        fecha_valor = date.today().isoformat()
        guardadas = 0
        errores = []

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        for moneda, tasa in tasas.items():
            if moneda == 'VES':
                continue
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO negocio_tasas_cambio 
                    (moneda_origen, moneda_destino, tasa, fecha_valor, fuente)
                    VALUES (?, 'VES', ?, ?, 'MANUAL')
                ''', (moneda, tasa, fecha_valor))
                guardadas += 1
            except Exception as e:
                errores.append(f"{moneda}: {e}")
        conn.commit()
        conn.close()
        return guardadas, errores

    @classmethod
    def obtener_tasa(cls, moneda: str, fecha: Optional[str] = None, 
                     db_path: str = "scfv.db") -> Optional[float]:
        if moneda == 'VES':
            return 1.0
        if fecha is None:
            fecha = date.today().isoformat()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT tasa FROM negocio_tasas_cambio 
            WHERE moneda_origen = ? AND fecha_valor <= ?
            ORDER BY fecha_valor DESC LIMIT 1
        ''', (moneda, fecha))
        resultado = cursor.fetchone()
        conn.close()
        return resultado[0] if resultado else None

    @classmethod
    def convertir(cls, monto: float, moneda_origen: str, moneda_destino: str = 'VES',
                  fecha: Optional[str] = None, db_path: str = "scfv.db") -> float:
        if moneda_origen == moneda_destino:
            return monto
        tasa_origen = cls.obtener_tasa(moneda_origen, fecha, db_path)
        if tasa_origen is None:
            raise ValueError(f"No hay tasa para {moneda_origen} en fecha {fecha}")
        if moneda_destino == 'VES':
            return monto * tasa_origen
        tasa_destino = cls.obtener_tasa(moneda_destino, fecha, db_path)
        if tasa_destino is None:
            raise ValueError(f"No hay tasa para {moneda_destino} en fecha {fecha}")
        en_ves = monto * tasa_origen
        return en_ves / tasa_destino
