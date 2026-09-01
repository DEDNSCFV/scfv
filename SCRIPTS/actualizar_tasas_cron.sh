#!/bin/bash
cd ~/scfv_v6
export PYTHONPATH="${PWD}/PODERES:${PWD}/DOMINIOS:${PWD}/INFRAESTRUCTURA"

# Verificar si existe archivo manual para hoy
MANUAL_FILE="PODERES/CONTABLE/monedas/tasas_oficiales.json"
TODAY=$(date +%Y-%m-%d)

if [ -f "$MANUAL_FILE" ]; then
    DATE_IN_FILE=$(grep -o '"fecha": "[^"]*"' $MANUAL_FILE | cut -d'"' -f4)
    if [ "$DATE_IN_FILE" != "$TODAY" ]; then
        echo "⚠️ ALERTA: No hay tasas manuales para hoy ($TODAY). Última: $DATE_IN_FILE" >> logs/tasas.log
    fi
fi

# Intentar guardar tasas (usará manual si existe, si no, fallback)
python3 SCRIPTS/actualizar_tasas.py >> logs/tasas.log 2>&1
