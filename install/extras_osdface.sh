#!/usr/bin/env bash
# VideoBoost · OSDFace (CVPR 2025) — restauración de caras 1-paso, textura muy
# orgánica. ⚠️ SIN LICENCIA en el repo → SOLO uso personal / pruebas, NO para
# la build de venta. Pensado para NVIDIA. Venv propio.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "⚠️  OSDFace no tiene licencia: úsalo solo para pruebas, no en una versión que vendas."

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

echo "== OSDFace (restauración de caras 1-paso) =="
"$PY" -m venv .venv-osdface
source .venv-osdface/bin/activate
pip install --upgrade pip
pip install torch torchvision $TORCH_ARGS
mkdir -p vendor models/OSDFace
if [ ! -d vendor/OSDFace ]; then
  git clone --depth 1 https://github.com/jkwang28/OSDFace.git vendor/OSDFace
fi
pip install -r vendor/OSDFace/requirements.txt "numpy<2"
pip install gdown huggingface_hub

# Pesos: el repo los publica en Google Drive (no en HuggingFace). Si tienes el
# ID/URL de la carpeta de Drive, pásalo en OSDFACE_GDRIVE para bajarlos solos;
# si no, descárgalos a mano a models/OSDFace/ (debe quedar associate_2.ckpt).
if [ -n "${OSDFACE_GDRIVE:-}" ]; then
  echo "↓ Descargando pesos de OSDFace desde Google Drive…"
  gdown --folder "$OSDFACE_GDRIVE" -O models/OSDFace || \
    gdown "$OSDFACE_GDRIVE" -O models/OSDFace/
else
  echo "ℹ️  Falta bajar los pesos de OSDFace (Google Drive)."
  echo "    Ábrelos desde el README del repo y colócalos en: models/OSDFace/"
  echo "    (debe quedar models/OSDFace/associate_2.ckpt). O reejecuta con:"
  echo "    OSDFACE_GDRIVE='<id-o-url-de-la-carpeta>' bash install/extras_osdface.sh"
fi
touch .venv-osdface/.ok
deactivate
echo "✅ Entorno de OSDFace listo (recuerda: solo para pruebas)."
