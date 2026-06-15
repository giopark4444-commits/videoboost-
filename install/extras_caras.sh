#!/usr/bin/env bash
# VideoBoost · CodeFormer — restauración de caras (el "face model" tipo HitPaw).
# Entorno propio porque basicsr/facexlib chocan con diffusers de FaithDiff/SeedVR2.
# Funciona en CUDA (NVIDIA) y MPS (Mac con chip M).
set -euo pipefail
cd "$(dirname "$0")/.."

TORCH_ARGS=""
if command -v nvidia-smi >/dev/null 2>&1; then
  TORCH_ARGS="--index-url https://download.pytorch.org/whl/cu124"
fi

echo "== CodeFormer (restauración de caras) =="
# Python 3.10+ (preferir python@3.12; en Mac instalarlo con Homebrew si falta).
PY=""
for c in python3.13 python3.12 python3.11 python3.10 python3; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info[:2] >= (3,10) else 1)' 2>/dev/null; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ] && command -v brew >/dev/null 2>&1; then
  brew install python@3.12 && PY="$(brew --prefix)/opt/python@3.12/bin/python3.12"
fi
[ -z "$PY" ] && { echo "❌ Necesitas Python 3.10+."; exit 1; }
"$PY" -m venv .venv-caras
source .venv-caras/bin/activate
pip install --upgrade pip
pip install torch torchvision $TORCH_ARGS
mkdir -p vendor
if [ ! -d vendor/CodeFormer ]; then
  git clone --depth 1 https://github.com/sczhou/CodeFormer.git vendor/CodeFormer
fi
pip install -r vendor/CodeFormer/requirements.txt
# basicsr se instala en modo desarrollo, como pide el README de CodeFormer.
( cd vendor/CodeFormer && python basicsr/setup.py develop )
# Pre-descarga de los pesos (CodeFormer + detección/parsing de caras).
( cd vendor/CodeFormer && python scripts/download_pretrained_models.py facelib \
  && python scripts/download_pretrained_models.py CodeFormer )
touch .venv-caras/.ok   # marcador: instalación completa (lo lee engines/faces.disponible)
deactivate
echo "✅ CodeFormer listo."
