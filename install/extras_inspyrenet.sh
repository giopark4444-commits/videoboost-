#!/usr/bin/env bash
# PixelBooster · InSPyReNet / transparent-background (MIT) — quita el FONDO de una
# imagen (matting) y deja PNG con alpha. Paquete pip puro; corre en NVIDIA (CUDA)
# y en Apple Silicon (MPS). Venv propio .venv-inspyrenet.
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

echo "== InSPyReNet (transparent-background · matting de fondo) =="
"$PY" -m venv .venv-inspyrenet
source .venv-inspyrenet/bin/activate
pip install --upgrade pip
pip install torch torchvision $TORCH_ARGS
# El paquete trae InSPyReNet + descarga de pesos al primer uso.
pip install transparent-background "numpy<2"
touch .venv-inspyrenet/.ok
deactivate
echo "✅ InSPyReNet listo. Los pesos se descargan al primer uso (~/.transparent-background)."
