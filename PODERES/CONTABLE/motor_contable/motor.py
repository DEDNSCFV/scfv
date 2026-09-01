"""
SCFV v6.1 — Motor Contable (Refactorizado)
Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
Fecha: 2026-08-30
"""

import json
import hashlib
import sqlite3
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from PODERES.CONTABLE.estados import TipoEvento, VersionContexto
from PODERES.CONTABLE.event_store.event_store import EventStore


class MotorContable:
    def __init__(self, db_connection: Optional[sqlite3.Connection] = None):
        self.db = db_connection
        if self.db is not None:
            self.db.row_factory = sqlite3.Row

    # ==========================================================>
    # 1. VALIDACIÓN DE PARTIDA DOBLE
    # ==========================================================>

    @staticmethod
    def validar_partida_doble(partidas: List[Dict]) -> Tuple[bool, int, int]:
        total_debe = 0
        total_haber = 0
        for p in partidas:
            monto = int(p.get('monto', 0))
            ubicacion = p.get('ubicacion', '').upper()
            if ubicacion == 'DEBE':
                total_debe += monto
            elif ubicacion == 'HABER':
                total_haber += monto
            else:
                raise ValueError(f"Ubicación inválida: {ubicacion}")
        return (total_debe == total_haber, total_debe, total_haber)

    # ==========================================================>
    # 2. AXIOMA BOOLEANO (U = N ⊙ M)
    # ==========================================================>

    @staticmethod
    def aplicar_axioma_booleano(naturaleza: str, movimiento: str) -> str:
        if naturaleza.upper() == 'DEUDORA':
            N = 1
        elif naturaleza.upper() == 'ACREEDORA':
            N = 0
        else:
            raise ValueError(f"Naturaleza inválida: {naturaleza}")

        if movimiento.upper() == 'AUMENTA':
            M = 1
        elif movimiento.upper() == 'DISMINUYE':
            M = 0
        else:
            raise ValueError(f"Movimiento inválido: {movimiento}")

        U = 1 if N == M else 0
        return 'DEBE' if U == 1 else 'HABER'

    # ==========================================================>
    # 3. GENERACIÓN DE ASIENTO
    # ==========================================================>

    def generar_asiento(self, decision: Dict[str, Any]) -> Tuple[Dict, List[Dict]]:
        periodo_id = decision.get('periodo_id')
        if periodo_id and not self._periodo_abierto(periodo_id):
            raise PeriodoCerradoError(f"El período {periodo_id} no está abierto.")

        partidas = decision.get('partidas', [])
        valido, total_debe, total_haber = self.validar_partida_doble(partidas)
        if not valido:
            raise PartidaDobleError(f"ΣDEBE ({total_debe}) != ΣHABER ({total_haber})")

        partidas_validas = []
        for p in partidas:
            cuenta = self._obtener_cuenta(p.get('cuenta_codigo'), p.get('cuenta_version'))
            if not cuenta:
                raise CuentaNoExisteError(f"Cuenta {p.get('cuenta_codigo')} no existe")
            ubicacion_calculada = self.aplicar_axioma_booleano(
                cuenta['naturaleza'],
                p.get('movimiento', 'AUMENTA')
            )
            if p.get('ubicacion').upper() != ubicacion_calculada:
                raise AxiomaBooleanoError(
                    f"Cuenta {p['cuenta_codigo']}: ubicación {p['ubicacion']} no coincide con axioma ({ubicacion_calculada})"
                )
            partidas_validas.append(p)

        asiento_id = str(uuid.uuid4())
        asiento = {
            'asiento_id': asiento_id,
            'fecha': decision.get('fecha', int(datetime.now().timestamp())),
            'periodo_id': periodo_id,
            'descripcion': decision.get('descripcion', ''),
            'total_debe': total_debe,
            'total_haber': total_haber,
            'decision_id': decision.get('decision_id'),
            'evidencia_hash': decision.get('evidencia_hash', ''),
            'creado_en': int(datetime.now().timestamp())
        }
        return asiento, partidas_validas

    # ==========================================================>
    # 4. ESCRITURA EN DIARIO (VIA EVENT STORE)
    # ==========================================================>

    def escribir_diario(self, asiento: Dict, partidas: List[Dict],
                        correlation_id: str, version_contexto: VersionContexto) -> str:
        total_debe = sum(p['monto'] for p in partidas if p['ubicacion'] == 'DEBE')
        total_haber = sum(p['monto'] for p in partidas if p['ubicacion'] == 'HABER')
        if abs(total_debe - total_haber) > 0.001:
            raise PartidaDobleError(f"ΣDEBE ({total_debe}) != ΣHABER ({total_haber})")

        asiento_id = asiento.get('asiento_id', str(uuid.uuid4()))
        asiento_obj = {
            'asiento_id': asiento_id,
            'evento_id': asiento.get('evento_id', ''),
            'fecha': asiento.get('fecha', datetime.now().isoformat()),
            'descripcion': asiento.get('descripcion', ''),
            'partidas': partidas,
            'total_debe': total_debe,
            'total_haber': total_haber,
            'correlation_id': correlation_id,
            'idempotency_key': self._generar_idempotency_key("ASIENTO", asiento_id)
        }

        event_store = EventStore()
        event_store.guardar(
            TipoEvento.ASIENTO_REGISTRADO,
            asiento_obj,
            correlation_id,
            asiento_obj['idempotency_key'],
            version_contexto
        )
        return asiento_id

    def _generar_idempotency_key(self, tipo: str, identidad: str) -> str:
        return hashlib.sha256((tipo + ":" + identidad).encode('utf-8')).hexdigest()

    # ==========================================================>
    # 5. RECONSTRUCCIÓN DEL MAYOR (DESDE EVENT STORE)
    # ==========================================================>

    def reconstruir_mayor(self) -> Dict[str, Dict]:
        """
        Reconstruye el Mayor directamente desde el Event Store,
        sumando todas las partidas de los asientos registrados.
        """
        event_store = EventStore()
        eventos = event_store.obtener_todos()
        asientos = [e for e in eventos if e['tipo_evento'] == 'ASIENTO_REGISTRADO']

        mayor = {}

        for e in asientos:
            payload = json.loads(e['payload'])
            partidas = payload.get('partidas', [])
            for p in partidas:
                cuenta = p.get('cuenta_codigo', '')
                if not cuenta:
                    continue
                if cuenta not in mayor:
                    mayor[cuenta] = {'saldo_debe': 0.0, 'saldo_haber': 0.0, 'saldo_neto': 0.0}
                if p.get('ubicacion') == 'DEBE':
                    mayor[cuenta]['saldo_debe'] += p.get('monto', 0.0)
                else:
                    mayor[cuenta]['saldo_haber'] += p.get('monto', 0.0)

        for cuenta in mayor:
            mayor[cuenta]['saldo_neto'] = mayor[cuenta]['saldo_debe'] - mayor[cuenta]['saldo_haber']

        return mayor

    # ==========================================================>
    # 6. MÉTODOS AUXILIARES (BD)
    # ==========================================================>

    def _periodo_abierto(self, periodo_id: str) -> bool:
        if self.db is None:
            return True
        cursor = self.db.cursor()
        cursor.execute("SELECT estado FROM negocio_periodos WHERE id = ?", (periodo_id,))
        row = cursor.fetchone()
        return row is not None and row[0] == 'ABIERTO'

    def _obtener_cuenta(self, codigo: str, version: str) -> Optional[Dict]:
        if self.db is None:
            return {'codigo': codigo, 'nombre': 'Cuenta', 'naturaleza': 'DEUDORA'}
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT codigo, nombre, naturaleza FROM negocio_pcu WHERE codigo = ? AND version = ? AND activa = 1",
            (codigo, version)
        )
        row = cursor.fetchone()
        if row:
            return {'codigo': row[0], 'nombre': row[1], 'naturaleza': row[2]}
        return None


# =============================================================================
# EXCEPCIONES
# =============================================================================

class MotorContableError(Exception):
    pass

class PeriodoCerradoError(MotorContableError):
    pass

class PartidaDobleError(MotorContableError):
    pass

class AxiomaBooleanoError(MotorContableError):
    pass

class CuentaNoExisteError(MotorContableError):
    pass
