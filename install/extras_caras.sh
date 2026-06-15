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
# numpy<2: el basicsr 1.3.2 incluido en el repo usa APIs que numpy 2.x rompe.
pip install -r vendor/CodeFormer/requirements.txt "numpy<2"
# NO usamos `basicsr/setup.py develop`: está deprecado y falla con setuptools
# moderno. No hace falta: el basicsr incluido se importa desde la carpeta del
# repo al ejecutar la inferencia (engines/faces.py corre con cwd=vendor/
# CodeFormer). Solo bajamos los pesos — con PYTHONPATH=. para que el script de
# descarga (en scripts/) encuentre basicsr.
( cd vendor/CodeFormer \
  && PYTHONPATH=. BASICSR_EXT=False python scripts/download_pretrained_models.py facelib \
  && PYTHONPATH=. BASICSR_EXT=False python scripts/download_pretrained_models.py CodeFormer )
touch .venv-caras/.ok   # marcador: instalación completa (lo lee engines/faces.disponible)
deactivate
echo "✅ CodeFormer listo."
