#!/bin/bash
# SCFV v8.0 - Script de verificación post-instalación
echo "🔍 Verificando instalación del SCFV..."

# 1. Verificar Python
if command -v python3 &>/dev/null; then
    echo "✅ Python: $(python3 --version)"
else
    echo "❌ Python no encontrado."
    exit 1
fi

# 2. Verificar dependencias Python
echo "🔍 Verificando dependencias..."
missing=()
for pkg in textual fpdf; do
    if ! python3 -c "import $pkg" 2>/dev/null; then
        missing+=("$pkg")
    fi
done
if [ ${#missing[@]} -eq 0 ]; then
    echo "✅ Dependencias Python: OK"
else
    echo "⚠️ Faltan dependencias: ${missing[*]}"
    echo "   Ejecuta: pip install ${missing[*]}"
fi

# 3. Ejecutar salud
echo "🔍 Ejecutando ./scfv salud..."
cd "$(dirname "$0")/.." || exit
./scfv salud
