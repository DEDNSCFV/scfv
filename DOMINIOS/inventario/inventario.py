from DOMINIOS.base_fractal import BaseFractal

class FractalInventario(BaseFractal):
    def evaluar(self, evidencia, contexto):
        # Por ahora, no generamos consecuencias contables para no duplicar partidas.
        # En el futuro, aquí se podría actualizar el stock (sin generar asientos).
        return []
