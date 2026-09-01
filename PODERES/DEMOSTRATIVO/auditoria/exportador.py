"""
SCFV v6.1 — Exportador de Auditoría (Paquete de Demostración)
Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
Fecha: 2026-08-30
"""

import json
import hashlib
from typing import Dict, Any, List
from PODERES.CONTABLE.event_store import EventStore
from PODERES.CONTABLE.estados import VersionContexto


class ExportadorAuditoria:
    def __init__(self, event_store: EventStore):
        self.event_store = event_store

    def generar_paquete(self, periodo: Dict, contexto: VersionContexto) -> Dict:
        """
        Genera el paquete de demostración con todas las versiones y hashes.
        """
        eventos = self.event_store.obtener_todos()
        # Filtrar eventos del período (simplificado)
        eventos_periodo = eventos  # En producción se filtra por timestamp

        # Obtener versiones de contexto utilizadas (T-09)
        versiones_utilizadas = list(set(
            e.get('version_contexto') for e in eventos_periodo if e.get('version_contexto')
        ))

        diario = self._materializar_diario()
        mayor = self._reconstruir_mayor()
        eeff = self._proyectar_eeff(mayor)

        paquete = {
            "mandante_id": contexto.version_id,
            "periodo": periodo,
            "version_contexto_actual": self._serializar_contexto(contexto),
            "versiones_contexto_utilizadas": versiones_utilizadas,  # <--- T-09
            "hash_chain_final": self.event_store.obtener_hash_final(),
            "eventos": eventos_periodo,
            "diario": diario,
            "mayor": mayor,
            "eeff": eeff,
            "invariantes_verificadas": self._verificar_invariantes()
        }

        # T-10: integridad (hash) en lugar de firma
        paquete["integridad"] = self._calcular_integridad(paquete)

        return paquete

    def _materializar_diario(self):
        # Simulación: leer del Diario materializado
        import sqlite3
        conn = sqlite3.connect("scfv_diario.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM negocio_diario")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def _reconstruir_mayor(self):
        from PODERES.CONTABLE.motor_contable.motor import MotorContable
        motor = MotorContable(None)
        return motor.reconstruir_mayor()

    def _proyectar_eeff(self, mayor):
        # Simulación: Balance y Resultados
        return {
            "balance": {"activo": mayor, "pasivo": {}, "patrimonio": {}},
            "resultados": {"ingresos": 0, "gastos": 0, "resultado": 0}
        }

    def _serializar_contexto(self, contexto: VersionContexto) -> Dict:
        return {
            "version_id": contexto.version_id,
            "fecha_inicio": contexto.fecha_inicio,
            "fecha_fin": contexto.fecha_fin,
            "PCU_version": contexto.PCU_version,
            "reglas_version": contexto.reglas_version,
            "politica_inventario_version": contexto.politica_inventario_version,
            "marco_contable_version": contexto.marco_contable_version,
            "politica_monetaria_version": contexto.politica_monetaria_version
        }

    def _calcular_integridad(self, paquete: Dict) -> str:
        # T-10: hash de integridad (sin clave privada)
        return hashlib.sha256(
            json.dumps(paquete, sort_keys=True, default=str).encode('utf-8')
        ).hexdigest()

    def _verificar_invariantes(self) -> bool:
        return True  # Simulación
