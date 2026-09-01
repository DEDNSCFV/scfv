#!/bin/bash
# =============================================================================
# SCFV v6 — Script de Respaldo Automático
# Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)
# Fecha: 2026-08-26
# Propósito: Empaquetar y respaldar los datos de un mandante a MEGA.
# =============================================================================

# Configuración
MANDANTE_DIR="$HOME/scfv_v6/data/mandante_$1"
BACKUP_DIR="$HOME/scfv_v6/backups"
MEGA_DIR="/SCFV_v6_backups"

# Verificar que se especificó un mandante
if [ -z "$1" ]; then
    echo "❌ Uso: ./scripts/backup.sh <nombre_mandante>"
    exit 1
fi

# Verificar que existe el mandante
if [ ! -d "$MANDANTE_DIR" ]; then
    echo "❌ Mandante '$1' no existe en $MANDANTE_DIR"
    exit 1
fi

# Crear directorio de backups si no existe
mkdir -p "$BACKUP_DIR"

# Nombre del archivo de backup
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/mandante_${1}_${TIMESTAMP}.tar.gz"

echo "📦 Creando backup de mandante '$1'..."

# Empaquetar y comprimir
tar -czf "$BACKUP_FILE" -C "$MANDANTE_DIR" .

# Verificar que se creó correctamente
if [ $? -eq 0 ]; then
    echo "✅ Backup creado: $BACKUP_FILE"
else
    echo "❌ Error al crear el backup"
    exit 1
fi

# Cifrar el backup (opcional, requiere gpg)
# gpg --symmetric --cipher-algo AES256 "$BACKUP_FILE"

# Subir a MEGA (requiere megacmd instalado)
if command -v megacmd &> /dev/null; then
    echo "☁️ Subiendo a MEGA..."
    megacmd mkdir "$MEGA_DIR" 2>/dev/null
    megacmd put "$BACKUP_FILE" "$MEGA_DIR/"
    if [ $? -eq 0 ]; then
        echo "✅ Backup subido a MEGA: $MEGA_DIR/mandante_${1}_${TIMESTAMP}.tar.gz"
    else
        echo "⚠️ Error al subir a MEGA. El backup está localmente."
    fi
else
    echo "⚠️ megacmd no instalado. Backup guardado localmente en: $BACKUP_FILE"
    echo "   Instalar megacmd: pip install megacmd (o desde repositorio)"
fi

echo "✅ Proceso completado."
