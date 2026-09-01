"""
SCFV v6.3 - Motor Causal con enteros escalados
"""
import uuid
import time
from typing import List, Any, Dict
from PODERES.CONTABLE.monedas.obtener_tasas import ObtenerTasasBCV

class MotorCausal:
    @staticmethod
    def generar_evento(evidencia: Dict, contexto, event_store, fecha_evaluacion: str, fractales: List[Any] = None) -> Dict:
        print(f"DEBUG MotorCausal: recibidos {len(fractales) if fractales else 0} fractales")
        correlation_id = evidencia.get('correlation_id', evidencia.get('id', str(uuid.uuid4())))

        evento = {
            "id": str(uuid.uuid4()),
            "timestamp": int(time.time()),
            "fecha_evaluacion": fecha_evaluacion,
            "monto": evidencia.get("monto", 0),
            "correlation_id": correlation_id,
            "consecuencias": []
        }

        if not fractales:
            return evento

        # Convertir montos a VES si vienen en otra moneda
        moneda = evidencia.get("moneda", "VES")
        if moneda != "VES":
            monto_original = evidencia.get("monto", 0)
            if monto_original:
                try:
                    monto_ves = ObtenerTasasBCV.convertir(monto_original, moneda, "VES", fecha_evaluacion)
                    evidencia["monto"] = monto_ves
                    evidencia["moneda_original"] = moneda
                    evidencia["tasa_usada"] = monto_ves / monto_original if monto_original else 0
                except Exception as e:
                    print(f"⚠️ Error convirtiendo {moneda}: {e}")
        for fractal in fractales:
            try:
                if isinstance(fractal, type):
                    fractal = fractal()
                cons = fractal.evaluar(evidencia, contexto)
                if cons:
                    evento["consecuencias"].extend(cons)
            except Exception as e:
                event_store.guardar(
                    "FRACTAL_FALLIDO",
                    {"error": str(e), "fractal": fractal.__class__.__name__},
                    correlation_id,
                    f"FALL_{uuid.uuid4()}"
                )

        return evento
