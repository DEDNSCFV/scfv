#!/bin/bash
echo "📦 Instalando SCFV v6.3..."
if command -v pkg &> /dev/null; then
    pkg update -y && pkg upgrade -y
    pkg install python -y
elif command -v apt &> /dev/null; then
    sudo apt update && sudo apt install python3 -y
else
    echo "⚠️ Asegúrate de tener Python 3.8+"
fi
pip install -r requirements.txt 2>/dev/null || echo "✅ Sin dependencias externas"
echo "✅ Instalación completa. Ejecuta: python run_lote.py examples/ejemplo_completo.csv"
