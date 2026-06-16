#!/usr/bin/env bash
# Lanza PixelBooster (Mac y Linux).
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  echo "❌ Falta el entorno. Corre primero el instalador de tu plataforma:"
  echo "   Mac:   install/instalar_mac.sh"
  echo "   Linux: install/instalar_nvidia.sh"
  exit 1
fi
source .venv/bin/activate
python app.py
