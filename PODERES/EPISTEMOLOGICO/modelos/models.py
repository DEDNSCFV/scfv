"""
SCFV v6.1 — Modelos del Núcleo Epistemológico
Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
Fecha: 2026-08-30
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from PODERES.CONTABLE.estados import EstadoPropuesta, EstadoEpistemico


@dataclass
class MetricasH1:
    r: float = 0.0
    s: float = 0.0
    o: float = 0.0
    t: float = 0.0
    v: float = 0.0


@dataclass
class EntidadExtraida:
    campo: str
    valor: Any
    confianza: float


@dataclass
class ObservacionH1:
    observacion_id: str
    evidencia_id: str
    entidades: List[EntidadExtraida]
    confianza_global: float
    timestamp: int
    correlation_id: str
    estado_epistemico: EstadoEpistemico = EstadoEpistemico.OBSERVADO


@dataclass
class HechoEconomico:
    hecho_id: str
    descripcion: str
    entidades: Dict[str, Any]
    temporalidad: str
    magnitud: float
    evidencia_ids: List[str]
    estado: EstadoEpistemico
    origen: str
    correlation_id: str
    idempotency_key: str


@dataclass
class PropuestaH1:
    propuesta_id: str
    hecho_id: str
    observacion_id: str
    metricas: MetricasH1
    soporte_C: float
    proposicion: str
    propuesta_padre_id: Optional[str] = None
    version_propuesta: int = 1
    estado_operacional: EstadoPropuesta = EstadoPropuesta.PROPUESTO
    timestamp: int = 0
    correlation_id: str = ""
    estado_epistemico: EstadoEpistemico = EstadoEpistemico.INFERIDO
    idempotency_key: str = ""


@dataclass
class DecisionProfesional:
    decision_id: str
    propuesta_h1_id: str
    propuesta_h2_id: Optional[str]
    tipo_decision: str
    justificacion: str
    autor: str
    timestamp: int
    correlation_id: str
    idempotency_key: str

@dataclass
class Tetrada:
    """Estructura universal del hecho económico situado (v6.2)."""
    H: str  # Hecho
    C: str  # Contraparte
    E: float  # Efecto
    M: str  # Medio
    V: str  # Evidencia
    X: Dict[str, Any]  # Contexto
    K: Dict[str, Any]  # Conocimiento
    completitud: str = "PENDIENTE"
