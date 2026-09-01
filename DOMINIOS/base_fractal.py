"""
SCFV v6 — Fractal Base
Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
Fecha: 2026-08-26
"""

import json
import uuid
from typing import Dict, Any, Callable, Optional
from datetime import datetime

from PODERES.CONTABLE.event_store import EventStore


class BaseFractal:
    def __init__(self, db_connection, nombre: str, event_store: EventStore):
        self.db = db_connection
        self.nombre = nombre
        self.event_store = event_store
        self._handlers = {}

    def registrar_handler(self, tipo_evento: str, handler: Callable):
        self._handlers[tipo_evento] = handler

    def procesar_evento(self, evento: Dict[str, Any]) -> Dict[str, Any]:
        # Convertir payload de JSON string a dict si es necesario
        if isinstance(evento.get('payload'), str):
            evento['payload'] = json.loads(evento['payload'])

        event_id = evento['event_id']
        tipo = evento['tipo']

        if self.event_store.ya_procesado(event_id, self.nombre):
            return {
                'exitoso': True,
                'mensaje': f"Evento {event_id} ya procesado por {self.nombre} (idempotente)"
            }

        handler = self._handlers.get(tipo)
        if not handler:
            return {
                'exitoso': False,
                'mensaje': f"No hay handler registrado para evento tipo {tipo} en {self.nombre}"
            }

        try:
            resultado = handler(evento)
            self.event_store.marcar_procesado(event_id, self.nombre, 'EXITOSO')
            return {
                'exitoso': True,
                'mensaje': f"Evento {event_id} procesado por {self.nombre}",
                'resultado': resultado
            }
        except Exception as e:
            error_msg = str(e)
            self.event_store.marcar_procesado(event_id, self.nombre, 'FALLIDO', error_msg)
            return {
                'exitoso': False,
                'mensaje': f"Error procesando evento {event_id} por {self.nombre}: {error_msg}"
            }

    def publicar_evento(self, tipo: str, payload: Dict, saga_id: Optional[str] = None) -> str:
        evento = {
            'event_id': str(uuid.uuid4()),
            'saga_id': saga_id,
            'tipo': tipo,
            'origen': self.nombre,
            'payload': payload,
            'timestamp': int(datetime.now().timestamp()),
            'version': 1
        }
        return self.event_store.guardar_evento(evento)

    def validar_transicion(self, estado_actual: str, nuevo_estado: str) -> bool:
        raise NotImplementedError("Los fractales deben implementar validar_transicion()")

    def aplicar_reglas(self, evento: Dict) -> Dict:
        raise NotImplementedError("Los fractales deben implementar aplicar_reglas()")

    def generar_evento_salida(self, consecuencia: Dict) -> Dict:
        raise NotImplementedError("Los fractales deben implementar generar_evento_salida()")
