"""
SCFV v6.1 — Dictum (Orientación y alertas)
Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
Fecha: 2026-08-30
"""

from typing import List
from PODERES.EPISTEMOLOGICO.models import PropuestaH1

class Dictum:
    @staticmethod
    def orientar(propuesta: PropuestaH1) -> List[str]:
        alertas = []
        if propuesta.soporte_C < 0.75:
            alertas.append("ALERTA: Bajo soporte normativo (C < 0.75)")
        if propuesta.metricas.s < 0.60:
            alertas.append("ALERTA: Similitud formal-legal insuficiente")
        if propuesta.metricas.v > 0.50:
            alertas.append("ALERTA: Alta volatilidad contextual")
        return alertas
