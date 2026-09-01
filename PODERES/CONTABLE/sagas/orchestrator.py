"""
SCFV v6 — Orquestador de Eventos y Sagas (CORREGIDO)
Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
Fecha: 2026-08-26
"""

import time
import json
import uuid
import logging
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime

from PODERES.CONTABLE.event_store import EventStoreRepository, SagaRepository
from PODERES.CONTABLE.motor_contable.motor import MotorContable


class Orquestador:
    """
    Coordinador central del SCFV v6.
    Procesa eventos y los distribuye a todos los consumidores registrados.
    """

    def __init__(self, db_connection, motor_contable: MotorContable):
        self.db = db_connection
        self.motor = motor_contable

        self.event_store = EventStoreRepository(db_connection)
        self.saga_repo = SagaRepository(db_connection)

        # Diccionario: tipo_evento -> lista de (nombre_consumidor, handler)
        self._handlers = {}

        self._running = False

    def registrar_consumidor(self, tipo_evento: str, handler: Callable, consumidor_nombre: str):
        """
        Registra una función manejadora para un tipo de evento.

        Args:
            tipo_evento: Ej. 'VENTA_CONFIRMADA'
            handler: Función que recibe el evento y devuelve un resultado.
            consumidor_nombre: Nombre del consumidor (ej. 'inventario', 'fiscal')
        """
        if tipo_evento not in self._handlers:
            self._handlers[tipo_evento] = []
        self._handlers[tipo_evento].append((consumidor_nombre, handler))

    def procesar_evento(self, evento: Dict[str, Any]) -> Dict:
        """
        Procesa un evento individual, ejecutándolo para cada consumidor registrado.
        """
        event_id = evento['event_id']
        tipo = evento['tipo']

        handlers = self._handlers.get(tipo, [])
        if not handlers:
            return {
                'exitoso': False,
                'mensaje': f"No hay handlers registrados para evento tipo {tipo}"
            }

        resultados = []
        todos_fallidos = True

        for consumidor, handler in handlers:
            # Verificar idempotencia
            if self.event_store.ya_procesado(event_id, consumidor):
                resultados.append({
                    'exitoso': True,
                    'consumidor': consumidor,
                    'mensaje': f"Ya procesado (idempotente)"
                })
                continue

            try:
                resultado = handler(evento)
                self.event_store.marcar_procesado(event_id, consumidor, 'EXITOSO')
                resultados.append({
                    'exitoso': True,
                    'consumidor': consumidor,
                    'resultado': resultado
                })
                todos_fallidos = False
            except Exception as e:
                error_msg = str(e)
                self.event_store.marcar_procesado(event_id, consumidor, 'FALLIDO', error_msg)
                resultados.append({
                    'exitoso': False,
                    'consumidor': consumidor,
                    'error': error_msg
                })

                # Si falla, activar compensación si es parte de una Saga
                if evento.get('saga_id'):
                    self._compensar_saga(evento['saga_id'], error_msg)

        if todos_fallidos:
            return {
                'exitoso': False,
                'mensaje': "Todos los consumidores fallaron",
                'resultados': resultados
            }
        else:
            return {
                'exitoso': True,
                'mensaje': f"Evento {event_id} procesado por al menos un consumidor",
                'resultados': resultados
            }

    def ejecutar_ciclo(self, limite: int = 10, intervalo: float = 1.0):
        """
        Ejecuta un ciclo de procesamiento de eventos.
        Obtiene TODOS los eventos y los distribuye a los consumidores.
        """
        eventos = self.event_store.obtener_eventos_no_procesados(limite)

        if not eventos:
            time.sleep(intervalo)
            return

        for evento in eventos:
            self.procesar_evento(evento)

    def ejecutar_continuamente(self):
        self._running = True
        while self._running:
            self.ejecutar_ciclo()

    def detener(self):
        self._running = False

    # ========================================================================
    # GESTIÓN DE SAGAS (simplificado para pruebas)
    # ========================================================================

    def iniciar_saga(self, nombre: str, pasos: list, payload: Dict) -> str:
        """Inicia una nueva Saga (ejecuta todos los pasos secuencialmente)."""
        saga_id = str(uuid.uuid4())
        saga = {
            'saga_id': saga_id,
            'nombre': nombre,
            'estado': 'INICIADA',
            'paso_actual': 0,
            'payload': payload,
            'contexto': {'pasos': pasos, 'resultados': []}
        }
        self.saga_repo.crear_saga(saga)

        self._ejecutar_paso_saga(saga_id, 0)
        return saga_id

    def _ejecutar_paso_saga(self, saga_id: str, paso_idx: int):
        saga = self.saga_repo.obtener_saga(saga_id)
        if not saga:
            raise ValueError(f"Saga {saga_id} no encontrada")

        pasos = json.loads(saga['contexto'])['pasos']
        if paso_idx >= len(pasos):
            self.saga_repo.actualizar_estado(saga_id, 'COMPLETADA')
            return

        paso = pasos[paso_idx]
        try:
            resultado = self._ejecutar_accion(paso['accion'], paso['fractal'], saga['payload'])
            contexto = json.loads(saga['contexto'])
            contexto['resultados'].append({'paso': paso_idx, 'resultado': resultado})
            self.saga_repo.actualizar_contexto(saga_id, contexto)
            self.saga_repo.actualizar_estado(saga_id, 'EN_PROCESO', paso_idx + 1)
            self._ejecutar_paso_saga(saga_id, paso_idx + 1)
        except Exception as e:
            self.saga_repo.actualizar_estado(saga_id, 'ERROR_DE_COMPENSACION', error=str(e))
            self._compensar_saga(saga_id, str(e))

    def _ejecutar_accion(self, accion: str, fractal: str, payload: Dict) -> Any:
        if fractal == 'motor_contable':
            if accion == 'generar_asiento':
                return self.motor.generar_asiento(payload)
            elif accion == 'revertir_asiento':
                return self.motor.revertir_asiento(payload['asiento_id'], payload.get('justificacion', ''))
        else:
            # Simulación para pruebas
            return {'estado': 'ok', 'mensaje': f"Acción {accion} en {fractal} ejecutada"}
        raise ValueError(f"Acción {accion} no reconocida")

    def _compensar_saga(self, saga_id: str, error: str):
        saga = self.saga_repo.obtener_saga(saga_id)
        if not saga:
            return

        contexto = json.loads(saga['contexto'])
        pasos = contexto.get('pasos', [])
        resultados = contexto.get('resultados', [])

        for paso_idx in range(len(resultados) - 1, -1, -1):
            paso = pasos[paso_idx]
            try:
                self._ejecutar_compensacion(paso.get('compensacion', ''), paso['fractal'], resultados[paso_idx]['resultado'])
            except Exception as e:
                self.saga_repo.actualizar_estado(saga_id, 'ERROR_DE_COMPENSACION', error=f"Compensación fallida: {e}")
                return

        self.saga_repo.actualizar_estado(saga_id, 'COMPENSADA')

    def _ejecutar_compensacion(self, compensacion: str, fractal: str, resultado: Any):
        # Simulación
        print(f"Compensación {compensacion} ejecutada en {fractal}")
        return True

    def recuperar_sagas_pendientes(self):
        """Reanuda Sagas que quedaron en EN_PROCESO tras un crash."""
        sagas = self.saga_repo.obtener_sagas_por_estado('EN_PROCESO')
        for saga in sagas:
            self._ejecutar_paso_saga(saga['saga_id'], saga['paso_actual'])
