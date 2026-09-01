"""
SCFV v6 — Fractal de Fiscal
Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
Fecha: 2026-08-26
"""

import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from DOMINIOS.base_fractal import BaseFractal


class FractalFiscal(BaseFractal):
    """
    Fractal de Fiscal: gestiona impuestos, declaraciones y retenciones.
    """

    def __init__(self, db_connection, event_store):
        super().__init__(db_connection, 'fiscal', event_store)

        self.registrar_handler('VENTA_CONFIRMADA', self._handler_venta_confirmada)
        self.registrar_handler('COMPRA_CONFIRMADA', self._handler_compra_confirmada)
        self.registrar_handler('CALCULAR_DECLARACION', self._handler_calcular_declaracion)

    # ========================================================================
    # CONFIGURACIÓN DE TASAS (por período)
    # ========================================================================

    def _obtener_tasa_iva(self, periodo_id: str) -> int:
        """Obtiene la tasa de IVA configurada para el período."""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT tasa FROM negocio_fiscal_config
            WHERE periodo_id = ? AND impuesto = 'IVA' AND activo = 1
        """, (periodo_id,))
        row = cursor.fetchone()
        if not row:
            # Tasa por defecto 16% (1600 en base 10000)
            return 1600
        return row['tasa']

    def _obtener_tasa_retencion(self, periodo_id: str, tipo: str) -> int:
        """Obtiene la tasa de retención configurada para el período."""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT tasa FROM negocio_fiscal_config
            WHERE periodo_id = ? AND impuesto = ? AND activo = 1
        """, (periodo_id, f"RETENCION_{tipo}"))
        row = cursor.fetchone()
        return row['tasa'] if row else 0

    # ========================================================================
    # HANDLERS DE EVENTOS
    # ========================================================================

    def _handler_venta_confirmada(self, evento: Dict) -> Dict:
        """
        Procesa una venta confirmada: calcula IVA débito y retenciones.
        """
        payload = evento['payload']
        venta_id = payload['venta_id']
        total_neto = payload.get('total_neto', 0)
        total_iva = payload.get('total_iva', 0)
        periodo_id = payload.get('periodo_id')

        if not periodo_id:
            raise ValueError("No se especificó período_id para la venta.")

        cursor = self.db.cursor()

        # 1. Registrar IVA débito (si la venta tiene IVA)
        if total_iva > 0:
            # Verificar que exista una declaración abierta para el período
            decl_id = self._obtener_declaracion_activa(periodo_id, 'IVA')
            if not decl_id:
                # Crear declaración automáticamente
                decl_id = self._crear_declaracion(periodo_id, 'IVA')

            cursor.execute("""
                UPDATE negocio_fiscal_declaraciones
                SET total_debito = total_debito + ?
                WHERE id = ?
            """, (total_iva, decl_id))

        # 2. Calcular retención de IVA si aplica (ej. compras con retención)
        # Por simplicidad, asumimos que algunas ventas tienen retención
        # (Se podría parametrizar por tipo de cliente)
        retencion_iva = 0
        tasa_retencion_iva = self._obtener_tasa_retencion(periodo_id, 'IVA')
        if tasa_retencion_iva > 0 and payload.get('aplica_retencion_iva', False):
            retencion_iva = (total_neto * tasa_retencion_iva) // 10000
            self._registrar_retencion(
                periodo_id,
                payload['cliente_id'],
                'IVA',
                total_neto,
                tasa_retencion_iva,
                retencion_iva,
                venta_id,
                'VENTA'
            )

        self.db.commit()

        return {
            'venta_id': venta_id,
            'iva_debito': total_iva,
            'retencion_iva': retencion_iva
        }

    def _handler_compra_confirmada(self, evento: Dict) -> Dict:
        """
        Procesa una compra confirmada: calcula IVA crédito y retenciones.
        """
        payload = evento['payload']
        compra_id = payload['compra_id']
        total_neto = payload.get('total_neto', 0)
        total_iva = payload.get('total_iva', 0)
        periodo_id = payload.get('periodo_id')

        if not periodo_id:
            raise ValueError("No se especificó período_id para la compra.")

        cursor = self.db.cursor()

        # 1. Registrar IVA crédito (si la compra tiene IVA)
        if total_iva > 0:
            decl_id = self._obtener_declaracion_activa(periodo_id, 'IVA')
            if not decl_id:
                decl_id = self._crear_declaracion(periodo_id, 'IVA')

            cursor.execute("""
                UPDATE negocio_fiscal_declaraciones
                SET total_credito = total_credito + ?
                WHERE id = ?
            """, (total_iva, decl_id))

        # 2. Calcular retención de ISLR si aplica (ej. compras a proveedores)
        retencion_islr = 0
        tasa_retencion_islr = self._obtener_tasa_retencion(periodo_id, 'ISLR')
        if tasa_retencion_islr > 0 and payload.get('aplica_retencion_islr', False):
            retencion_islr = (total_neto * tasa_retencion_islr) // 10000
            self._registrar_retencion(
                periodo_id,
                payload['proveedor_id'],
                'ISLR',
                total_neto,
                tasa_retencion_islr,
                retencion_islr,
                compra_id,
                'COMPRA'
            )

        self.db.commit()

        return {
            'compra_id': compra_id,
            'iva_credito': total_iva,
            'retencion_islr': retencion_islr
        }

    def _handler_calcular_declaracion(self, evento: Dict) -> Dict:
        """
        Calcula el saldo a pagar de una declaración (débito - crédito + retenciones).
        """
        payload = evento['payload']
        declaracion_id = payload['declaracion_id']

        cursor = self.db.cursor()
        cursor.execute("""
            SELECT total_debito, total_credito, total_retenciones
            FROM negocio_fiscal_declaraciones
            WHERE id = ?
        """, (declaracion_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Declaración {declaracion_id} no encontrada.")

        total_debito = row['total_debito'] or 0
        total_credito = row['total_credito'] or 0
        total_retenciones = row['total_retenciones'] or 0

        saldo = total_debito - total_credito + total_retenciones

        cursor.execute("""
            UPDATE negocio_fiscal_declaraciones
            SET saldo_a_pagar = ?, estado = 'CALCULADA', actualizado_en = ?
            WHERE id = ?
        """, (saldo, int(datetime.now().timestamp()), declaracion_id))

        self.db.commit()

        return {
            'declaracion_id': declaracion_id,
            'saldo_a_pagar': saldo,
            'total_debito': total_debito,
            'total_credito': total_credito,
            'total_retenciones': total_retenciones
        }

    # ========================================================================
    # MÉTODOS PRIVADOS
    # ========================================================================

    def _obtener_declaracion_activa(self, periodo_id: str, tipo: str) -> Optional[str]:
        """Obtiene la declaración activa (BORRADOR) para un período y tipo."""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT id FROM negocio_fiscal_declaraciones
            WHERE periodo_id = ? AND tipo = ? AND estado = 'BORRADOR'
            LIMIT 1
        """, (periodo_id, tipo))
        row = cursor.fetchone()
        return row['id'] if row else None

    def _crear_declaracion(self, periodo_id: str, tipo: str) -> str:
        """Crea una nueva declaración fiscal en estado BORRADOR."""
        decl_id = str(uuid.uuid4())
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO negocio_fiscal_declaraciones
            (id, periodo_id, tipo, fecha_inicio, fecha_fin, estado, creado_en, actualizado_en)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            decl_id,
            periodo_id,
            tipo,
            int(datetime.now().timestamp()),
            int(datetime.now().timestamp()),
            'BORRADOR',
            int(datetime.now().timestamp()),
            int(datetime.now().timestamp())
        ))
        self.db.commit()
        return decl_id

    def _registrar_retencion(self, periodo_id: str, tercero_id: str, tipo: str,
                             base: int, tasa: int, monto: int,
                             referencia_id: str, referencia_tipo: str):
        """Registra una retención fiscal."""
        cursor = self.db.cursor()

        # Obtener o crear declaración de retenciones
        decl_id = self._obtener_declaracion_activa(periodo_id, 'RETENCIONES')
        if not decl_id:
            decl_id = self._crear_declaracion(periodo_id, 'RETENCIONES')

        # Registrar retención
        retencion_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO negocio_fiscal_retenciones
            (id, declaracion_id, tercero_id, tipo, base_imponible, tasa, monto_retenido,
             fecha, referencia_id, referencia_tipo, creado_en)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            retencion_id,
            decl_id,
            tercero_id,
            tipo,
            base,
            tasa,
            monto,
            int(datetime.now().timestamp()),
            referencia_id,
            referencia_tipo,
            int(datetime.now().timestamp())
        ))

        # Actualizar total_retenciones en la declaración
        cursor.execute("""
            UPDATE negocio_fiscal_declaraciones
            SET total_retenciones = total_retenciones + ?
            WHERE id = ?
        """, (monto, decl_id))

        self.db.commit()

    # ========================================================================
    # MÉTODOS REQUERIDOS POR BaseFractal
    # ========================================================================

    def validar_transicion(self, estado_actual: str, nuevo_estado: str) -> bool:
        return True

    def aplicar_reglas(self, evento: Dict) -> Dict:
        return {}

    def generar_evento_salida(self, consecuencia: Dict) -> Dict:
        return {}
