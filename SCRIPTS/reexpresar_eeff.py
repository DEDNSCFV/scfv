#!/usr/bin/env python3
"""
SCFV v8.0 - Reexpresión de Estados Financieros (NIC 29)
Solo reexpresa activos y pasivos NO MONETARIOS.
"""
import sys
import os
import sqlite3
import json
from datetime import datetime, date
from collections import defaultdict
import calendar

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from PODERES.CONTABLE.inflacion.factores import FactoresInflacion
from PODERES.CONTABLE.event_store.event_store import EventStore

# ============================================================
# CLASIFICACIÓN DE CUENTAS (MONETARIAS / NO MONETARIAS)
# ============================================================
# Cuentas NO MONETARIAS (se reexpresan)
CUENTAS_NO_MONETARIAS = {
    # Activos no monetarios
    '140101',  # Inventario
    '160101',  # Activos Fijos
    '160102',  # Depreciación Acumulada
    # Ingresos no monetarios
    '410101',  # Ventas
    '410102',  # Ingresos por Servicios
    # Gastos no monetarios
    '610101',  # Costo de Ventas
    '620101',  # Gastos Administrativos
    '630101',  # Depreciación
}

def es_no_monetaria(cuenta: str) -> bool:
    """Retorna True si la cuenta debe ser reexpresada (no monetaria)."""
    # 1. Si está en la lista explícita
    if cuenta in CUENTAS_NO_MONETARIAS:
        return True
    # 2. Si comienza con '14' (Inventario) o '16' (Activos Fijos) o '4' (Ingresos) o '6' (Gastos)
    #    pero excluyendo cuentas que sabemos son monetarias (ej. 410...)
    if cuenta.startswith('14') or cuenta.startswith('16'):
        return True
    if cuenta.startswith('4') or cuenta.startswith('6'):
        # Excluir cuentas de ingresos financieros que sí son monetarias
        if cuenta.startswith('4105') or cuenta.startswith('4201'):
            return False
        return True
    return False

def obtener_saldos_mayor(periodo: str, db_path: str = "scfv.db") -> dict:
    """Reconstruye el Mayor desde Event Store para un período dado."""
    es = EventStore(db_path)
    eventos = es.obtener_eventos_por_tipo("ASIENTO_REGISTRADO")
    saldos = defaultdict(float)
    
    anio_mes = periodo.split('-')
    if len(anio_mes) == 2:
        anio, mes = int(anio_mes[0]), int(anio_mes[1])
        fecha_inicio = f"{anio}-{mes:02d}-01"
        ultimo_dia = calendar.monthrange(anio, mes)[1]
        fecha_fin = f"{anio}-{mes:02d}-{ultimo_dia}"
    else:
        fecha_inicio = "1900-01-01"
        fecha_fin = "2099-12-31"

    for evento in eventos:
        payload = evento.get('payload', {})
        fecha_asiento = payload.get('fecha')
        if not fecha_asiento:
            ts = evento.get('timestamp')
            if ts:
                fecha_asiento = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            else:
                continue
        
        if fecha_inicio <= fecha_asiento <= fecha_fin:
            partidas = payload.get('partidas', [])
            for p in partidas:
                cuenta = p.get('cuenta')
                monto = p.get('monto', 0)
                ubicacion = p.get('ubicacion', '')
                if ubicacion == 'DEBE':
                    saldos[cuenta] += monto
                elif ubicacion == 'HABER':
                    saldos[cuenta] -= monto
                else:
                    natura = p.get('naturaleza', '')
                    mov = p.get('movimiento', '')
                    if natura and mov:
                        if (natura == "DEUDORA" and mov == "AUMENTA") or \
                           (natura == "ACREEDORA" and mov == "DISMINUYE"):
                            saldos[cuenta] += monto
                        else:
                            saldos[cuenta] -= monto
    return dict(saldos)

def reexpresar_estado_situacion(saldos, fecha_cierre, db_path):
    """Reexpresa solo cuentas NO MONETARIAS."""
    eeff_reexpresado = {}
    for cuenta, saldo in saldos.items():
        if es_no_monetaria(cuenta):
            try:
                saldo_reex = FactoresInflacion.reexpresar_saldo(saldo, "2026-01-01", fecha_cierre, db_path)
            except ValueError:
                saldo_reex = saldo
        else:
            # Cuenta monetaria: no se reexpresa
            saldo_reex = saldo
        eeff_reexpresado[cuenta] = saldo_reex
    return eeff_reexpresado

def main():
    periodo = sys.argv[1] if len(sys.argv) > 1 else date.today().strftime("%Y-%m")
    fecha_cierre = sys.argv[2] if len(sys.argv) > 2 else date.today().isoformat()
    db_path = sys.argv[3] if len(sys.argv) > 3 else "scfv.db"

    print(f"🔄 Reexpresando EEFF para período {periodo} a fecha {fecha_cierre}")

    saldos = obtener_saldos_mayor(periodo, db_path)
    if not saldos:
        print("⚠️ No hay saldos para el período.")
        return

    eeff_reexpresado = reexpresar_estado_situacion(saldos, fecha_cierre, db_path)

    output = {
        "periodo": periodo,
        "fecha_cierre": fecha_cierre,
        "saldos_originales": saldos,
        "saldos_reexpresados": eeff_reexpresado,
        "nota": "Solo se reexpresaron cuentas no monetarias (NIC 29)."
    }
    with open(f"reexpresion_{periodo}.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"✅ Reexpresión guardada en reexpresion_{periodo}.json")

if __name__ == "__main__":
    main()
