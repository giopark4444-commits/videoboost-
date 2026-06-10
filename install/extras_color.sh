#!/usr/bin/env bash
# VideoBoost · DDColor — colorización de imágenes B/N (el "colorize model" tipo HitPaw).
# CUDA en NVIDIA; en Mac corre en CPU (más lento pero funciona). Entorno propio.
set -euo pipefail
cd "$(dirname "$0")/.."

TORCH_ARGS=""
if command -v nvidia-smi >/dev/null 2>&1; then
  TORCH_ARGS="--index-url https://download.pytorch.org/whl/cu124"
fi

echo "== DDColor (colorización de imágenes) =="
python3 -m venv .venv-color
source .venv-color/bin/activate
pip install --upgrade pip
pip install torch torchvision $TORCH_ARGS
mkdir -p vendor models
if [ ! -d vendor/DDColor ]; then
  git clone --depth 1 https://github.com/piddnad/DDColor.git vendor/DDColor
fi
pip install -r vendor/DDColor/requirements.txt
pip install huggingface_hub timm

echo "↓ Descargando pesos de DDColor…"
python - <<'PY'
from huggingface_hub import hf_hub_download
import shutil, os
os.makedirs("models/DDColor", exist_ok=True)
ruta = hf_hub_download("piddnad/ddcolor_modelscope", "pytorch_model.pt")
shutil.copy(ruta, "models/DDColor/pytorch_model.pt")
print("✅ Pesos de DDColor en models/DDColor/")
PY
deactivate
echo "✅ DDColor listo."
