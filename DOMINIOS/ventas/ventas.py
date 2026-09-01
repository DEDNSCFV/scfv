"""
Fractal de Ventas - SCFV v6.2 LTS
"""
class FractalVentas:
    @staticmethod
    def evaluar(evidencia, contexto):
        monto = evidencia.get('monto', 0)
        if monto <= 0:
            return []
        iva_tasa = 0.12
        base = monto / (1 + iva_tasa)
        iva = monto - base
        return [
            {
                "cuenta": "110101",
                "naturaleza": "DEUDORA",
                "movimiento": "AUMENTA",
                "monto": monto
            },
            {
                "cuenta": "410101",
                "naturaleza": "ACREEDORA",
                "movimiento": "AUMENTA",
                "monto": base
            },
            {
                "cuenta": "210201",
                "naturaleza": "ACREEDORA",
                "movimiento": "AUMENTA",
                "monto": iva
            }
        ]
