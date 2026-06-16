#!/usr/bin/env bash
# PixelBooster · FILM (Google, Apache-2.0) — interpolación de frames para movimiento
# grande (slow-mo fotorrealista). TensorFlow 2 → pensado para NVIDIA (4080).
set -euo pipefail
cd "$(dirname "$0")/.."

command -v nvidia-smi >/dev/null 2>&1 || \
  echo "⚠️  FILM usa TensorFlow-GPU: pensado para NVIDIA. En Mac es impráctico."

# FILM es un proyecto TF2 algo antiguo → preferimos Python 3.9/3.10.
PY=""
for c in python3.10 python3.9 python3.11 python3; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if (3,9) <= sys.version_info[:2] <= (3,11) else 1)' 2>/dev/null; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ] && command -v brew >/dev/null 2>&1; then
  brew install python@3.10 && PY="$(brew --prefix)/opt/python@3.10/bin/python3.10"
fi
[ -z "$PY" ] && { echo "❌ Necesitas Python 3.9–3.11."; exit 1; }

echo "== FILM (frame interpolation, movimiento grande) =="
"$PY" -m venv .venv-film
source .venv-film/bin/activate
pip install --upgrade pip
mkdir -p vendor
if [ ! -d vendor/frame-interpolation ]; then
  git clone --depth 1 https://github.com/google-research/frame-interpolation.git vendor/frame-interpolation
fi
# Dependencias del repo (tensorflow, mediapy, scikit-image, etc.).
pip install -r vendor/frame-interpolation/requirements.txt 2>/dev/null || \
  pip install tensorflow tensorflow-addons mediapy scikit-image numpy Pillow apache-beam gin-config tqdm natsort

# --- Pesos: SavedModel film_net/Style (Google Drive). ---
#   FILM_GDRIVE=<id_o_carpeta>  → se baja con gdown a models/FILM/
DEST="models/FILM"
mkdir -p "$DEST"
if [ ! -d "$DEST/film_net/Style/saved_model" ]; then
  if [ -n "${FILM_GDRIVE:-}" ]; then
    pip install -q gdown
    gdown --folder "${FILM_GDRIVE}" -O "$DEST" || gdown "${FILM_GDRIVE}" -O "$DEST/"
  fi
fi
if [ -d "$DEST/film_net/Style/saved_model" ]; then
  touch .venv-film/.ok
  echo "✅ FILM listo."
else
  echo "⚠️  Faltan los pesos. Descarga 'pretrained_models' del README de"
  echo "    google-research/frame-interpolation y deja film_net/Style/saved_model en"
  echo "    $DEST/ ; luego: touch .venv-film/.ok"
fi
deactivate
