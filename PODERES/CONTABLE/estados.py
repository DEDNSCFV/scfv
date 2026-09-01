"""
SCFV v6.1 — Estados y Enumeraciones
Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
Fecha: 2026-08-30
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

class VersionContexto:
    def __init__(self, version_id, fecha_inicio, fecha_fin, 
                 PCU_version, reglas_version, 
                 politica_inventario_version, 
                 marco_contable_version, 
                 politica_monetaria_version):
        self.version_id = version_id
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        self.PCU_version = PCU_version
        self.reglas_version = reglas_version
        self.politica_inventario_version = politica_inventario_version
        self.marco_contable_version = marco_contable_version
        self.politica_monetaria_version = politica_monetaria_version

class EstadoEpistemico(Enum):
    OBSERVADO = auto()
    INFERIDO = auto()
    PROPUESTO = auto()
    CONFIRMADO = auto()
    RECHAZADO = auto()

class EstadoPropuesta(Enum):
    PROPUESTO = auto()
    ACEPTADO = auto()
    RECHAZADO = auto()
    MODIFICADO = auto()

class EstadoConsecuencia(Enum):
    GENERADA = auto()
    VALIDADA = auto()
    APLICADA = auto()
    RECHAZADA = auto()

class EstadoAsiento(Enum):
    PROPUESTO = auto()
    VALIDADO = auto()
    REGISTRADO = auto()
    ANULADO = auto()

class TipoDecisionH2(Enum):
    ACEPTAR = auto()
    MODIFICAR = auto()
    RECHAZAR = auto()

class TipoEvento(Enum):
    EVIDENCIA_ADQUIRIDA = auto()
    OBSERVACION_GENERADA = auto()
    PROPUESTA_GENERADA = auto()
    PROPUESTA_MODIFICADA = auto()
    PROPUESTA_ACEPTADA = auto()
    PROPUESTA_RECHAZADA = auto()
    HECHO_CONFIRMADO = auto()
    HECHO_RECHAZADO = auto()
    DECISION_H2 = auto()
    EVENTO_ECONOMICO = auto()
    CONSECUENCIA_GENERADA = auto()
    CONSECUENCIA_VALIDADA = auto()
    ASIENTO_PROPUESTO = auto()
    ASIENTO_REGISTRADO = auto()
    ASIENTO_ANULADO = auto()
    FRACTAL_FALLIDO = auto()
    CONSECUENCIAS_GENERADAS = auto()

class TipoDecisionH2(Enum):
    ACEPTAR = auto()
    MODIFICAR = auto()
    RECHAZAR = auto()
