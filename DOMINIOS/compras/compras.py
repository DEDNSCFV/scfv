from DOMINIOS.base_fractal import BaseFractal

class FractalCompras(BaseFractal):
    def evaluar(self, evidencia, contexto):
        tipo = evidencia.get('tipo', '').lower().strip()
        monto = evidencia.get('monto', 0)
        if tipo == 'compra' and monto > 0:
            return [
                {"cuenta": contexto.get('CONTABLE', {}).get('CUENTA_INVENTARIO', '140101'), 
                 "naturaleza": "DEUDORA", "movimiento": "AUMENTA", "monto": monto},
                {"cuenta": contexto.get('CONTABLE', {}).get('CUENTA_PROVEEDORES', '210101'), 
                 "naturaleza": "ACREEDORA", "movimiento": "AUMENTA", "monto": monto}
            ]
        return []
