"""
SCFV v6.1 — Perceptum (Extracción de entidades)
Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
Fecha: 2026-08-30
"""

import uuid
import re
import time
from typing import Dict, Any, List
from PODERES.CONTABLE.estados import EstadoEpistemico
from PODERES.EPISTEMOLOGICO.modelos.models import ObservacionH1, EntidadExtraida


class Perceptum:
    @staticmethod
    def extraer(evidencia: Dict[str, Any]) -> ObservacionH1:
        """
        Extrae entidades de la evidencia y genera una ObservacionH1.
        Simula OCR/parser; en producción se usaría Tesseract, PyPDF2, etc.
        """
        correlation_id = str(uuid.uuid4())
        observacion_id = str(uuid.uuid4())
        timestamp = int(time.time())

        # Extraer entidades de los metadatos de la evidencia
        entidades = []
        for campo, valor in evidencia.get('metadatos', {}).get('entidades', {}).items():
            confianza = 0.95 if valor else 0.0
            entidades.append(EntidadExtraida(campo=campo, valor=valor, confianza=confianza))

        confianza_global = min((e.confianza for e in entidades), default=0.0)
        if confianza_global < 0.60:
            print(f"⚠️ ALTA_INCERTIDUMBRE: confianza_global={confianza_global}")

        return ObservacionH1(
            observacion_id=observacion_id,
            evidencia_id=evidencia.get('id', ''),
            entidades=entidades,
            confianza_global=confianza_global,
            timestamp=timestamp,
            correlation_id=correlation_id,
            estado_epistemico=EstadoEpistemico.OBSERVADO
        )
