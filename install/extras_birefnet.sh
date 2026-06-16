#!/usr/bin/env bash
# PixelBooster · BiRefNet (ZhengPeng7, MIT) — matting de ALTA RESOLUCIÓN (recorta el
# sujeto y deja PNG con alpha suave). PyTorch + transformers; corre en NVIDIA
# (CUDA) y en Apple Silicon (MPS). Venv propio .venv-birefnet.
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

# torch: en NVIDIA por el índice CUDA; en Mac la rueda normal ya trae MPS.
TORCH_ARGS=""
command -v nvidia-smi >/dev/null 2>&1 && TORCH_ARGS="--index-url https://download.pytorch.org/whl/cu124"

echo "== BiRefNet (matting de alta resolución) =="
"$PY" -m venv .venv-birefnet
source .venv-birefnet/bin/activate
pip install --upgrade pip
pip install torch torchvision $TORCH_ARGS
# transformers carga los pesos de HuggingFace con trust_remote_code; el resto son
# dependencias del código remoto de BiRefNet (timm/einops/kornia) + imagen.
pip install transformers safetensors huggingface_hub timm einops kornia pillow "numpy<2"
touch .venv-birefnet/.ok
deactivate
echo "✅ BiRefNet listo. Los pesos se descargan de HuggingFace en el primer uso."
