#!/usr/bin/env bash
# PixelBooster · EMA-VFI (MCG-NJU, Apache-2.0) — interpolación de frames SOTA (slow-mo).
# PyTorch; el demo usa .cuda() → pensado para NVIDIA (4080). Venv propio.
set -euo pipefail
cd "$(dirname "$0")/.."

command -v nvidia-smi >/dev/null 2>&1 || \
  echo "⚠️  EMA-VFI usa CUDA en su código: pensado para NVIDIA. En Mac MPS puede no funcionar."

PY=""
for c in python3.10 python3.9 python3.11 python3; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if (3,8) <= sys.version_info[:2] <= (3,11) else 1)' 2>/dev/null; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ] && command -v brew >/dev/null 2>&1; then
  brew install python@3.10 && PY="$(brew --prefix)/opt/python@3.10/bin/python3.10"
fi
[ -z "$PY" ] && { echo "❌ Necesitas Python 3.8–3.11."; exit 1; }

TORCH_ARGS=""
command -v nvidia-smi >/dev/null 2>&1 && TORCH_ARGS="--index-url https://download.pytorch.org/whl/cu124"

echo "== EMA-VFI (frame interpolation SOTA) =="
"$PY" -m venv .venv-emavfi
source .venv-emavfi/bin/activate
pip install --upgrade pip
pip install torch torchvision $TORCH_ARGS
mkdir -p vendor
if [ ! -d vendor/EMA-VFI ]; then
  git clone --depth 1 https://github.com/MCG-NJU/EMA-VFI.git vendor/EMA-VFI
fi
pip install -r vendor/EMA-VFI/requirements.txt 2>/dev/null || \
  pip install opencv-python numpy timm imageio tqdm "numpy<2"

# --- Pesos: carpeta ckpt/ (ours.pkl / ours_t) en Google Drive. ---
#   EMAVFI_GDRIVE=<id_o_carpeta>  → se baja con gdown a vendor/EMA-VFI/ckpt/
if [ ! -d vendor/EMA-VFI/ckpt ] || [ -z "$(ls -A vendor/EMA-VFI/ckpt 2>/dev/null)" ]; then
  mkdir -p vendor/EMA-VFI/ckpt
  if [ -n "${EMAVFI_GDRIVE:-}" ]; then
    pip install -q gdown
    gdown --folder "${EMAVFI_GDRIVE}" -O vendor/EMA-VFI/ckpt || \
      gdown "${EMAVFI_GDRIVE}" -O vendor/EMA-VFI/ckpt/
  fi
fi
if [ -n "$(ls -A vendor/EMA-VFI/ckpt 2>/dev/null)" ]; then
  touch .venv-emavfi/.ok
  echo "✅ EMA-VFI listo."
else
  echo "⚠️  Falta el ckpt. Descarga 'model checkpoints' del README de MCG-NJU/EMA-VFI"
  echo "    y deja la carpeta ckpt/ en vendor/EMA-VFI/ ; luego: touch .venv-emavfi/.ok"
fi
deactivate
