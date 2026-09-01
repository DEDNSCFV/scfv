"""
SCFV v7.2 - Cargador de .scfv con parser formal (Lark)
"""
from pathlib import Path
from typing import Dict, List, Any, Optional
from .parser import SCFVParser

class SCFVLoader:
    _parser = SCFVParser()

    @classmethod
    def cargar_contexto(cls, ruta: Optional[str] = None) -> Dict:
        """Carga el contexto global desde SCFV.scfv."""
        if ruta is None:
            ruta = Path(__file__).parent / "contexto" / "SCFV.scfv"
        if not Path(ruta).exists():
            print(f"⚠️ Contexto no encontrado en {ruta}, usando defaults")
            return cls._default_contexto()
        ast = cls._parser.parse_file(str(ruta))
        return ast.get("contexto", {})

    @classmethod
    def cargar_fractal(cls, ruta: str, contexto: Dict) -> List[Dict]:
        """Carga un fractal y lo compila a funciones ejecutables (por ahora devuelve AST)."""
        ast = cls._parser.parse_file(ruta)
        # Por ahora devolvemos el AST crudo. Más adelante compilaremos a funciones Python.
        return ast.get("fractales", {})

    @classmethod
    def validar_semantica(cls, ruta: str) -> List[str]:
        """Valida semántica de un archivo .scfv (tipos, referencias)."""
        errores = []
        try:
            ast = cls._parser.parse_file(ruta)
            # Validar que las referencias a cuentas existan, etc.
            # (Implementación futura)
        except SyntaxError as e:
            errores.append(str(e))
        return errores

    @classmethod
    def _default_contexto(cls) -> Dict:
        return {
            "NORMATIVO": {"IVA_TASA": 0.12},
            "CONTABLE": {
                "CUENTA_CAJA": "110101",
                "CUENTA_VENTAS": "410101",
                "CUENTA_IVA_PAGAR": "210201",
                "CUENTA_IVA_COBRAR": "210202",
                "CUENTA_PROVEEDORES": "210101",
                "CUENTA_INVENTARIO": "140101",
                "CUENTA_COSTO_VENTA": "610101",
            }
        }

    @classmethod
    def validar_tipos(cls, ast: Dict) -> List[str]:
        """Valida tipos en el AST (e.g., monto como número, cuentas como string)."""
        errores = []
        for fractal, reglas in ast.get("fractales", {}).items():
            for regla in reglas:
                for accion in regla["actions"]:
                    if accion.startswith("GENERAR"):
                        # Verificar que los parámetros tengan tipos correctos
                        # Simplificado: solo imprimimos advertencia por ahora
                        pass
        return errores
