#!/usr/bin/env bash
# VideoBoost · CodeFormer — restauración de caras (el "face model" tipo HitPaw).
# Entorno propio porque basicsr/facexlib chocan con diffusers de HYPIR/SeedVR2.
# Funciona en CUDA (NVIDIA) y MPS (Mac con chip M).
set -euo pipefail
cd "$(dirname "$0")/.."

TORCH_ARGS=""
if command -v nvidia-smi >/dev/null 2>&1; then
  TORCH_ARGS="--index-url https://download.pytorch.org/whl/cu124"
fi

echo "== CodeFormer (restauración de caras) =="
python3 -m venv .venv-caras
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
deactivate
echo "✅ CodeFormer listo."
