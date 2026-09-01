"""
SCFV v6.3 - Integrador con soporte para enteros escalados
"""
import uuid
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
import importlib
from pathlib import Path

from PODERES.CONTABLE.event_store import EventStore
from PODERES.CONTABLE.motor_causal import MotorCausal

class Integrador:
    def __init__(self, db_path: str = "scfv.db", fractales=None):
        print(f"DEBUG: Integrador creado con {len(fractales) if fractales else 0} fractales")
        self.event_store = EventStore(db_path)
        self.event_store.conn = self.event_store.conn
        self.contexto = self._cargar_contexto()
        self.fractales = fractales

    def _cargar_contexto(self):
        from PODERES.FORMAL.dsl.scfv_loader import SCFVLoader
        return SCFVLoader.cargar_contexto()

    def _generar_idempotency_key(self, tipo: str, identidad: str) -> str:
        return hashlib.sha256((tipo + ":" + identidad).encode('utf-8')).hexdigest()

    def _aplicar_xnor(self, naturaleza: str, movimiento: str) -> str:
        """Aplica XNOR: DEBE si naturaleza == movimiento."""
        if naturaleza == "DEUDORA" and movimiento == "AUMENTA":
            return "DEBE"
        elif naturaleza == "ACREEDORA" and movimiento == "DISMINUYE":
            return "DEBE"
        elif naturaleza == "DEUDORA" and movimiento == "DISMINUYE":
            return "HABER"
        elif naturaleza == "ACREEDORA" and movimiento == "AUMENTA":
            return "HABER"
        else:
            raise ValueError(f"XNOR inválido: naturaleza={naturaleza}, movimiento={movimiento}")

    def procesar_evidencia(self, evidencia: Dict, fractales: Optional[List] = None) -> Dict:
        print(f"DEBUG: self.fractales tiene {len(self.fractales) if self.fractales else 0} fractales")
        correlation_id = evidencia.get('id', str(uuid.uuid4()))

        # 1. Guardar evidencia
        evidencia_key = self._generar_idempotency_key("EVIDENCIA", evidencia.get('id', correlation_id))
        self.event_store.guardar(
            "EVIDENCIA_ADQUIRIDA",
            evidencia,
            correlation_id,
            evidencia_key
        )

        # 2. Generar evento con Motor Causal
        fecha_evaluacion = datetime.now().isoformat()
        evento = MotorCausal.generar_evento(
            evidencia,
            self.contexto,
            self.event_store,
            fecha_evaluacion,
            self.fractales
        )

        # 3. Obtener consecuencias y aplicar XNOR
        consecuencias = evento.get("consecuencias", [])
        if not consecuencias:
            return {"estado": "sin_consecuencias", "correlation_id": correlation_id}

        for p in consecuencias:
            if 'ubicacion' not in p:
                natura = p.get('naturaleza')
                mov = p.get('movimiento')
                if natura and mov:
                    p['ubicacion'] = self._aplicar_xnor(natura, mov)

        total_debe = sum(p.get('monto', 0) for p in consecuencias if p.get('ubicacion') == 'DEBE')
        total_haber = sum(p.get('monto', 0) for p in consecuencias if p.get('ubicacion') == 'HABER')

        if abs(total_debe - total_haber) > 0:
            raise ValueError(f"I1_VIOLACION_PARTIDA_DOBLE: debe={total_debe}, haber={total_haber}")

        asiento = {
            "id": str(uuid.uuid4()),
            "correlation_id": correlation_id,
            "partidas": consecuencias,
            "total_debe": total_debe,
            "total_haber": total_haber
        }
        asiento_key = self._generar_idempotency_key("ASIENTO", asiento["id"])
        self.event_store.guardar(
            "ASIENTO_REGISTRADO",
            asiento,
            correlation_id,
            asiento_key
        )

        self.event_store.materializar_diario()

        return {
            "estado": "completado",
            "correlation_id": correlation_id,
            "asiento_id": asiento["id"],
            "total_debe": total_debe,
            "total_haber": total_haber
        }
    def _cargar_fractales(self):
        """Carga dinámicamente todos los fractales de DOMINIOS/"""
        fractales = []
        base_path = Path("DOMINIOS")
        for item in base_path.iterdir():
            if item.is_dir() and not item.name.startswith("_"):
                try:
                    module_name = f"DOMINIOS.{item.name}.{item.name}"
                    modulo = importlib.import_module(module_name)
                    for attr_name in dir(modulo):
                        attr = getattr(modulo, attr_name)
                        if isinstance(attr, type) and hasattr(attr, "procesar_evento"):
                            fractales.append(attr())
                except Exception as e:
                    print(f"⚠️ No se pudo cargar fractal {item.name}: {e}")
        return fractales
    def _instanciar_fractales(self, clases_fractales):
        """Instancia fractales pasándoles db_connection y event_store."""
        instancias = []
        for cls in clases_fractales:
            try:
                instancia = cls(self.event_store.conn, self.event_store)
                instancias.append(instancia)
            except Exception as e:
                print(f"⚠️ No se pudo instanciar fractal {cls.__name__}: {e}")
        return instancias
