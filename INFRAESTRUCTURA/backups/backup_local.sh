#!/bin/bash
# Respaldo local del SCFV v6 a la memoria interna

BACKUP_DIR=~/storage/downloads
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="scfv_v6_backup_${TIMESTAMP}.tar.gz"

echo "📦 Creando respaldo: $BACKUP_FILE"
cd ~
tar -czf "$BACKUP_FILE" scfv_v6/

echo "📂 Copiando a $BACKUP_DIR"
cp "$BACKUP_FILE" "$BACKUP_DIR/"

echo "✅ Respaldo completado: $BACKUP_DIR/$BACKUP_FILE"
ls -lh "$BACKUP_DIR/$BACKUP_FILE"
