#!/usr/bin/env bash
# VideoBoost · FBCNN (ICCV 2021, Apache-2.0) — quita artefactos de compresión JPEG
# con Factor de Calidad ajustable. CNN ligera: funciona en Mac (MPS) y NVIDIA
# (CUDA). Venv propio. Los pesos vienen de los releases del repo (no Google Drive).
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

# En Mac la rueda por defecto trae MPS; en PC con NVIDIA usar el índice CUDA.
TORCH_ARGS=""
command -v nvidia-smi >/dev/null 2>&1 && TORCH_ARGS="--index-url https://download.pytorch.org/whl/cu124"

echo "== FBCNN (quitar artefactos JPEG) =="
"$PY" -m venv .venv-fbcnn
source .venv-fbcnn/bin/activate
pip install --upgrade pip
pip install torch torchvision $TORCH_ARGS
# El repo no trae requirements.txt; estas son sus dependencias de inferencia.
pip install "numpy<2" opencv-python requests

mkdir -p vendor models
if [ ! -d vendor/FBCNN ]; then
  git clone --depth 1 https://github.com/jiaxi-jiang/FBCNN.git vendor/FBCNN
fi

# Pesos: fbcnn_color.pth vive en los releases del repo y va en vendor/FBCNN/model_zoo/.
# Se descargan aquí para no depender del primer uso (y para poder marcar .ok).
mkdir -p vendor/FBCNN/model_zoo
PESO="vendor/FBCNN/model_zoo/fbcnn_color.pth"
URL="https://github.com/jiaxi-jiang/FBCNN/releases/download/v1.0/fbcnn_color.pth"
if [ ! -f "$PESO" ]; then
  echo "↓ Descargando pesos de FBCNN (fbcnn_color.pth)…"
  if command -v curl >/dev/null 2>&1; then
    curl -L --fail -o "$PESO" "$URL" || rm -f "$PESO"
  else
    "$(pwd)/.venv-fbcnn/bin/python" - "$URL" "$PESO" <<'PYEOF'
import sys, requests
url, dst = sys.argv[1], sys.argv[2]
r = requests.get(url, stream=True); r.raise_for_status()
with open(dst, "wb") as f:
    for chunk in r.iter_content(1 << 20):
        f.write(chunk)
PYEOF
  fi
fi

# Solo marcamos listo si el peso existe de verdad.
if [ -f "$PESO" ]; then
  touch .venv-fbcnn/.ok
  echo "✅ FBCNN listo (pesos en vendor/FBCNN/model_zoo/fbcnn_color.pth)."
else
  echo "⚠️  No se pudo bajar el peso de FBCNN. Descárgalo a mano desde:"
  echo "    $URL"
  echo "    y colócalo en: vendor/FBCNN/model_zoo/fbcnn_color.pth"
fi
deactivate
