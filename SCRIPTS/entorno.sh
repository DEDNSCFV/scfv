#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${SCRIPT_DIR}/PODERES:${SCRIPT_DIR}/DOMINIOS:${SCRIPT_DIR}/INFRAESTRUCTURA:${PYTHONPATH}"
exec python3 "$@"
