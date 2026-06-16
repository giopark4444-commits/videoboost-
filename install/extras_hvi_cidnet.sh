#!/usr/bin/env bash
# PixelBooster · HVI-CIDNet (MIT) — realce de poca luz (low-light), ganador NTIRE 2025
# / CVPR 2025. CIDNet es una CNN ligera, así que corre en NVIDIA y en Mac (MPS/CPU).
# Venv propio .venv-hvi_cidnet. Los pesos se bajan de HuggingFace en el primer uso.
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

# En NVIDIA forzamos ruedas CUDA; en Mac, el torch por defecto trae MPS.
TORCH_ARGS=""
command -v nvidia-smi >/dev/null 2>&1 && TORCH_ARGS="--index-url https://download.pytorch.org/whl/cu124"

echo "== HVI-CIDNet (realce de poca luz) =="
"$PY" -m venv .venv-hvi_cidnet
source .venv-hvi_cidnet/bin/activate
pip install --upgrade pip
# El requirements.txt del repo fija torch==1.13.1 (muy viejo, sin MPS y sin CUDA
# moderna): instalamos un torch actual + solo lo que el runner de inferencia usa.
pip install torch torchvision $TORCH_ARGS
pip install "numpy<2" pillow einops huggingface_hub safetensors

mkdir -p vendor
if [ ! -d vendor/HVI-CIDNet ]; then
  git clone --depth 1 https://github.com/Fediory/HVI-CIDNet.git vendor/HVI-CIDNet
fi

# Chequeo de sintaxis/imports del paquete del modelo en el venv (sin GPU no se
# corre inferencia, pero verificamos que net.CIDNet importa).
( cd vendor/HVI-CIDNet && python -c "import net.CIDNet" ) \
  && echo "✅ net.CIDNet importa correctamente." \
  || echo "⚠️ No se pudo importar net.CIDNet; revisar dependencias del repo."

touch .venv-hvi_cidnet/.ok
deactivate
echo "✅ HVI-CIDNet listo. Los pesos (Fediory/HVI-CIDNet-Generalization) se descargan de HuggingFace en el primer uso."
