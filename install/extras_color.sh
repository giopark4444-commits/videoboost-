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
"$PY" -m venv .venv-color
source .venv-color/bin/activate
pip install --upgrade pip
pip install torch torchvision $TORCH_ARGS
mkdir -p vendor models
if [ ! -d vendor/DDColor ]; then
  git clone --depth 1 https://github.com/piddnad/DDColor.git vendor/DDColor
fi
# El requirements de DDColor fija numpy==1.24.3 y opencv==4.7.0.72, que NO
# compilan en Python 3.12. Relajamos esos pins y cap numpy<2 (el código de
# DDColor usa APIs que numpy 2.x rompe). El resto de pins se respeta.
sed -E 's/^(numpy|opencv-python)==.*/\1/' vendor/DDColor/requirements.txt > /tmp/ddcolor_req.txt
pip install -r /tmp/ddcolor_req.txt "numpy<2"
pip install huggingface_hub timm

echo "↓ Descargando pesos de DDColor…"
python - <<'PY'
from huggingface_hub import hf_hub_download, list_repo_files
import shutil, os
os.makedirs("models/DDColor", exist_ok=True)
# El repo publica el peso como pytorch_model.bin (antes .pt). Tomamos el que
# exista y lo guardamos como .pt, que es lo que espera engines/color.py
# (a torch.load la extensión le da igual).
files = list_repo_files("piddnad/ddcolor_modelscope")
nombre = next((f for f in ("pytorch_model.pt", "pytorch_model.bin")
               if f in files), None)
if not nombre:
    raise SystemExit("No encuentro el peso de DDColor en el repo de HuggingFace.")
ruta = hf_hub_download("piddnad/ddcolor_modelscope", nombre)
shutil.copy(ruta, "models/DDColor/pytorch_model.pt")
print("✅ Pesos de DDColor en models/DDColor/")
PY
touch .venv-color/.ok   # marcador de instalación completa
deactivate
echo "✅ DDColor listo."
