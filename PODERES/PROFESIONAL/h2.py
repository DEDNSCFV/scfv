"""
SCFV v6.1 — H₂ (Decisión Profesional)
Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
Fecha: 2026-08-30
"""

import uuid
import time
from typing import Dict, List, Optional
from PODERES.CONTABLE.estados import TipoDecisionH2, EstadoEpistemico, EstadoPropuesta
from PODERES.EPISTEMOLOGICO.models import PropuestaH1, DecisionProfesional, HechoEconomico
from PODERES.CONTABLE.event_store import EventStore
from PODERES.CONTABLE.estados import TipoEvento, VersionContexto
from PODERES.EPISTEMOLOGICO.intellectus import Intellectus


class H2Decision:
    @staticmethod
    def decidir(
        propuesta_original: PropuestaH1,
        alertas: List[str],
        contexto: VersionContexto,
        event_store: EventStore,
        modo_auto: bool = True
    ) -> Dict:
        """
        Simula la decisión profesional humana.
        En modo auto (para pruebas), acepta siempre.
        En modo real, se mostraría interfaz CLI.
        """
        propuesta_actual = propuesta_original
        decision_final = None
        justificacion = ""

        if modo_auto:
            decision_final = TipoDecisionH2.ACEPTAR
            justificacion = "Decisión automática en prueba"
        else:
            # Aquí iría la interfaz con el contador
            decision_final = TipoDecisionH2.ACEPTAR
            justificacion = input("Justificación: ")

        # Si se acepta, confirmar el hecho
        hecho = HechoEconomico(
            hecho_id=propuesta_original.hecho_id,
            descripcion=f"Hecho confirmado para {propuesta_original.correlation_id}",
            entidades={},
            temporalidad=time.strftime("%Y-%m-%d"),
            magnitud=0.0,
            evidencia_ids=[],
            estado=EstadoEpistemico.CONFIRMADO,
            origen="H2",
            correlation_id=propuesta_original.correlation_id,
            idempotency_key=f"hecho_confirmado_{propuesta_original.correlation_id}"
        )

        # Registrar decisión y hecho en Event Store
        decision = DecisionProfesional(
            decision_id=str(uuid.uuid4()),
            propuesta_h1_id=propuesta_original.propuesta_id,
            propuesta_h2_id=None,
            tipo_decision=decision_final,
            justificacion=justificacion,
            autor="CPC-183594",
            timestamp=int(time.time()),
            correlation_id=propuesta_original.correlation_id,
            idempotency_key=f"decision_{propuesta_original.correlation_id}"
        )

        event_store.guardar(
            TipoEvento.DECISION_H2,
            decision,
            decision.correlation_id,
            decision.idempotency_key,
            contexto
        )

        event_store.guardar(
            TipoEvento.HECHO_CONFIRMADO,
            hecho,
            hecho.correlation_id,
            hecho.idempotency_key,
            contexto
        )

        return {
            "decision": decision,
            "hecho": hecho,
            "tipo": decision_final.name
        }

