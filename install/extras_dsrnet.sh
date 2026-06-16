#!/usr/bin/env bash
# VideoBoost · DSRNet (Apache-2.0) — eliminación de reflejos en una sola imagen
# (single image reflection removal). Red convolucional: corre en NVIDIA y también
# en CPU (Mac Apple Silicon), suficiente para una imagen. Venv propio.
# Los pesos están en Google Drive → patrón DSRNET_GDRIVE (gdown) o manual; NO se
# marca .ok hasta que el peso exista en disco.
set -euo pipefail
cd "$(dirname "$0")/.."

PESO="dsrnet_l_epoch18.pt"   # debe coincidir con engines/dsrnet.py (PESO_ARCHIVO)

# Python 3.10+ (el repo pide 3.9; 3.10+ funciona). Preferir python@3.12.
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
command -v nvidia-smi >/dev/null 2>&1 && TORCH_ARGS="--index-url https://download.pytorch.org/whl/cu124"

echo "== DSRNet (quitar reflejos de una imagen) =="
"$PY" -m venv .venv-dsrnet
source .venv-dsrnet/bin/activate
pip install --upgrade pip
pip install torch torchvision $TORCH_ARGS
mkdir -p vendor models/DSRNet
if [ ! -d vendor/DSRNet ]; then
  git clone --depth 1 https://github.com/mingcv/DSRNet.git vendor/DSRNet
fi
# numpy<2 por compatibilidad con scikit-image/opencv pineados del repo.
pip install -r vendor/DSRNet/requirements.txt "numpy<2"
pip install gdown

# Pesos: el repo los publica en Google Drive (carpeta), no en HuggingFace. Si
# tienes el ID/URL de la carpeta de Drive, pásalo en DSRNET_GDRIVE para bajarlos
# solos; si no, descárgalos a mano y deja models/DSRNet/dsrnet_l_epoch18.pt.
if [ ! -f "models/DSRNet/$PESO" ] && [ -n "${DSRNET_GDRIVE:-}" ]; then
  echo "↓ Descargando pesos de DSRNet desde Google Drive…"
  gdown --folder "$DSRNET_GDRIVE" -O models/DSRNet || \
    gdown "$DSRNET_GDRIVE" -O "models/DSRNet/$PESO" || true
  # Si gdown bajó la carpeta con subdirectorios, sube los .pt a la raíz esperada.
  find models/DSRNet -name '*.pt' -exec sh -c 'mv -n "$1" models/DSRNet/' _ {} \; 2>/dev/null || true
fi

deactivate

if [ -f "models/DSRNet/$PESO" ]; then
  touch .venv-dsrnet/.ok
  echo "✅ DSRNet listo (peso $PESO presente)."
else
  echo "ℹ️  Falta bajar el peso de DSRNet (Google Drive): carpeta"
  echo "    https://drive.google.com/drive/folders/1AIS9-EgBN3_q-TCq7W0j5OeWMgLO_de0"
  echo "    Coloca el archivo en: models/DSRNet/$PESO"
  echo "    O reejecuta con:  DSRNET_GDRIVE='<id-o-url-de-la-carpeta>' bash install/extras_dsrnet.sh"
  echo "⚠️  No se marcó .ok: el motor no estará disponible hasta que exista el peso."
fi
