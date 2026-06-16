#!/usr/bin/env bash
# VideoBoost · Practical-RIFE (MIT) — interpolación de frames moderna (slow-mo).
# PyTorch: corre en NVIDIA (CUDA) y en Mac (MPS). Venv propio.
set -euo pipefail
cd "$(dirname "$0")/.."

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

# En NVIDIA, ruedas CUDA; en Mac, la rueda por defecto ya trae soporte MPS.
TORCH_ARGS=""
command -v nvidia-smi >/dev/null 2>&1 && TORCH_ARGS="--index-url https://download.pytorch.org/whl/cu124"

echo "== Practical-RIFE (interpolación de frames / slow-mo) =="
"$PY" -m venv .venv-prife
source .venv-prife/bin/activate
pip install --upgrade pip
pip install torch torchvision $TORCH_ARGS
mkdir -p vendor
if [ ! -d vendor/Practical-RIFE ]; then
  git clone --depth 1 https://github.com/hzwer/Practical-RIFE.git vendor/Practical-RIFE
fi
pip install -r vendor/Practical-RIFE/requirements.txt 2>/dev/null || \
  pip install numpy opencv-python torch torchvision sk-video tqdm

# --- Modelo (flownet.pkl + *.py en train_log/) ---
# Los modelos de Practical-RIFE viven en Google Drive (sin URL directa). Opciones:
#   PRIFE_GDRIVE=<id_o_carpeta>  → se baja con gdown
# Si no, deja instrucciones para colocarlo a mano y NO marca .ok.
mkdir -p vendor/Practical-RIFE/train_log
if [ ! -f vendor/Practical-RIFE/train_log/flownet.pkl ]; then
  if [ -n "${PRIFE_GDRIVE:-}" ]; then
    pip install -q gdown
    gdown --folder "${PRIFE_GDRIVE}" -O vendor/Practical-RIFE/train_log || \
      gdown "${PRIFE_GDRIVE}" -O vendor/Practical-RIFE/train_log/
  fi
fi
if [ -f vendor/Practical-RIFE/train_log/flownet.pkl ]; then
  touch .venv-prife/.ok
  echo "✅ Practical-RIFE listo."
else
  echo "⚠️  Falta el modelo. Descarga el último (p.ej. 4.25) desde el README de"
  echo "    hzwer/Practical-RIFE y copia *.py + flownet.pkl en"
  echo "    vendor/Practical-RIFE/train_log/ ; luego: touch .venv-prife/.ok"
fi
deactivate
