#!/bin/bash
# =============================================================================
# SCFV v6 — Script de Ejecución de Pruebas de Aceptación (CORREGIDO)
# Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
# =============================================================================

cd ~/scfv_v6

echo "=========================================="
echo "SCFV v6 — Ejecución de Pruebas de Aceptación"
echo "=========================================="
echo "Fecha: $(date)"
echo ""

# Función para ejecutar prueba y mostrar resultado
ejecutar_prueba() {
    local nombre=$1
    local comando=$2
    echo -n "▶ $nombre ... "
    if eval $comando > /dev/null 2>&1; then
        echo "✅ OK"
        PASADAS=$((PASADAS + 1))
        return 0
    else
        echo "❌ FALLÓ"
        FALLIDAS=$((FALLIDAS + 1))
        return 1
    fi
}

# Inicializar contadores
PASADAS=0
FALLIDAS=0
TOTAL=0

# =============================================================================
# 1. Pruebas del Motor Contable (Fase 1)
# =============================================================================
echo ""
echo "--- 1. Motor Contable ---"
ejecutar_prueba "test_validar_partida_doble" "python3 -c \"from tests.test_motor import test_validar_partida_doble; test_validar_partida_doble()\""
ejecutar_prueba "test_aplicar_axioma_booleano" "python3 -c \"from tests.test_motor import test_aplicar_axioma_booleano; test_aplicar_axioma_booleano()\""
ejecutar_prueba "test_generar_asiento" "python3 -c \"from tests.test_motor import test_generar_asiento; test_generar_asiento()\""
ejecutar_prueba "test_escribir_diario" "python3 -c \"from tests.test_motor import test_escribir_diario; test_escribir_diario()\""
ejecutar_prueba "test_revertir_asiento" "python3 -c \"from tests.test_motor import test_revertir_asiento; test_revertir_asiento()\""

# =============================================================================
# 2. Pruebas del Orquestador (Fase 2)
# =============================================================================
echo ""
echo "--- 2. Orquestador ---"
ejecutar_prueba "test_event_store" "python3 -c \"from tests.test_orchestrator import test_event_store; test_event_store()\""
ejecutar_prueba "test_saga_repository" "python3 -c \"from tests.test_orchestrator import test_saga_repository; test_saga_repository()\""
ejecutar_prueba "test_orchestrator_basico" "python3 -c \"from tests.test_orchestrator import test_orchestrator_basico; test_orchestrator_basico()\""
ejecutar_prueba "test_saga_completa" "python3 -c \"from tests.test_orchestrator import test_saga_completa; test_saga_completa()\""

# =============================================================================
# 3. Pruebas de Fractales (Fase 3)
# =============================================================================
echo ""
echo "--- 3. Fractales ---"
ejecutar_prueba "test_ventas" "python3 tests/test_ventas.py"
ejecutar_prueba "test_compras" "python3 tests/test_compras.py"
ejecutar_prueba "test_inventario" "python3 tests/test_inventario.py"
ejecutar_prueba "test_fiscal" "python3 tests/test_fiscal.py"

# =============================================================================
# 4. Prueba de Integración (Fase 4)
# =============================================================================
echo ""
echo "--- 4. Integración ---"
ejecutar_prueba "test_integracion_completa" "python3 tests/test_integracion.py"

# =============================================================================
# 5. Pruebas del Núcleo Epistemológico (Fase 5)
# =============================================================================
echo ""
echo "--- 5. Núcleo Epistemológico ---"
ejecutar_prueba "test_perceptum" "python3 -c \"from tests.test_epistemic import test_perceptum; test_perceptum()\""
ejecutar_prueba "test_flujo_completo" "python3 -c \"from tests.test_epistemic import test_flujo_completo; test_flujo_completo()\""

# =============================================================================
# 6. Pruebas de Seguridad (Fase 6)
# =============================================================================
echo ""
echo "--- 6. Seguridad ---"
ejecutar_prueba "test_cifrado" "python3 -c \"from tests.test_seguridad import test_cifrado; test_cifrado()\""
ejecutar_prueba "test_exportador" "python3 -c \"from tests.test_seguridad import test_exportador; test_exportador()\""
ejecutar_prueba "test_backup_script" "python3 -c \"from tests.test_seguridad import test_backup_script; test_backup_script()\""

# =============================================================================
# Resumen
# =============================================================================
TOTAL=$((PASADAS + FALLIDAS))
echo ""
echo "=========================================="
echo "RESUMEN DE EJECUCIÓN"
echo "=========================================="
echo "✅ Pruebas pasadas: $PASADAS"
echo "❌ Pruebas fallidas: $FALLIDAS"
echo "📊 Total: $TOTAL"
echo ""

if [ $FALLIDAS -eq 0 ]; then
    echo "🎉 ¡TODAS LAS PRUEBAS HAN PASADO EXITOSAMENTE!"
else
    echo "⚠️ Hay pruebas fallidas. Revisar los errores."
fi

echo ""
echo "Resultados guardados en: tests/resultados.txt"
