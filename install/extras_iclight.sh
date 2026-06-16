#!/usr/bin/env bash
# PixelBooster · IC-Light v1 (lllyasviel, Apache-2.0) — re-iluminación (relighting)
# de imágenes por difusión sobre Stable Diffusion 1.5. Pensado para NVIDIA; en Mac
# corre por CPU/MPS (impráctico de lento). Venv propio.
#
# ⚠️ El código de IC-Light es Apache-2.0 (apto comercial), PERO el quita-fondo por
# defecto (BriaRMBG-1.4) es de uso NO comercial. Para vender, sustituir por una
# alternativa comercial (p. ej. BiRefNet) antes de distribuir.
set -euo pipefail
cd "$(dirname "$0")/.."

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

TORCH_ARGS=""
command -v nvidia-smi >/dev/null 2>&1 && TORCH_ARGS="--index-url https://download.pytorch.org/whl/cu121"

echo "== IC-Light (re-iluminación por difusión SD1.5) =="
"$PY" -m venv .venv-iclight
source .venv-iclight/bin/activate
pip install --upgrade pip
pip install torch torchvision $TORCH_ARGS
mkdir -p vendor
if [ ! -d vendor/IC-Light ]; then
  git clone --depth 1 https://github.com/lllyasviel/IC-Light.git vendor/IC-Light
fi
# requirements.txt del repo (diffusers, transformers, safetensors, opencv, etc.).
pip install -r vendor/IC-Light/requirements.txt "numpy<2"
touch .venv-iclight/.ok
deactivate
echo "✅ IC-Light listo. SD1.5 (realistic-vision-v51), BriaRMBG-1.4 y los pesos"
echo "   iclight_sd15_fc se descargan de HuggingFace en el primer uso."
