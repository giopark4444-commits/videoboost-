#!/usr/bin/env bash
# VideoBoost · DehazeFormer (IDKiro, MIT) — quita neblina/niebla de imágenes con un
# Transformer eficiente. Incluye gUNet (mismo autor, MIT) como modo rápido. NO es
# difusión: corre en NVIDIA (CUDA) y en Mac con chip M (MPS/CPU) → plataforma ambas.
# Venv propio. Pesos en Google Drive (no autodescargan): se bajan con gdown si pasas
# DEHAZEFORMER_GDRIVE / GUNET_GDRIVE, o se colocan a mano. NO se marca .ok hasta que
# exista al menos un peso.
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

# En NVIDIA, torch con CUDA; en Mac el índice por defecto ya trae soporte MPS.
TORCH_ARGS=""
command -v nvidia-smi >/dev/null 2>&1 && TORCH_ARGS="--index-url https://download.pytorch.org/whl/cu124"

echo "== DehazeFormer + gUNet (quitar neblina, MIT) =="
"$PY" -m venv .venv-dehazeformer
source .venv-dehazeformer/bin/activate
pip install --upgrade pip
pip install torch torchvision $TORCH_ARGS

# Dependencias de la inferencia (read_img/write_img usan opencv; el resto son utils
# del repo). pytorch_msssim solo lo necesita el test.py oficial (métricas), pero lo
# incluimos por si se usa. numpy<2 para evitar choques ABI con opencv en torch viejo.
pip install opencv-python pyyaml timm pytorch_msssim "numpy<2"

mkdir -p vendor
if [ ! -d vendor/DehazeFormer ]; then
  git clone --depth 1 https://github.com/IDKiro/DehazeFormer.git vendor/DehazeFormer
fi
# gUNet (modo rápido). Si falla el clon, no es fatal: DehazeFormer ya sirve.
if [ ! -d vendor/gUNet ]; then
  git clone --depth 1 https://github.com/IDKiro/gUNet.git vendor/gUNet || \
    echo "⚠️  No se pudo clonar gUNet (modo rápido). DehazeFormer funciona igual."
fi

pip install gdown

# Pesos: ambos repos los publican SOLO en Google Drive, organizados por experimento
# (saved_models/<exp>/<modelo>.pth). Estructura objetivo para el engine (exp outdoor):
#   vendor/DehazeFormer/saved_models/outdoor/dehazeformer-b.pth
#   vendor/DehazeFormer/saved_models/outdoor/dehazeformer-l.pth
#   vendor/gUNet/saved_models/outdoor/gunet_b.pth
mkdir -p vendor/DehazeFormer/saved_models vendor/gUNet/saved_models

if [ -n "${DEHAZEFORMER_GDRIVE:-}" ]; then
  echo "↓ Descargando pesos de DehazeFormer desde Google Drive…"
  # Se baja la carpeta completa de Drive dentro de saved_models/ (trae outdoor/ etc.).
  gdown --folder "$DEHAZEFORMER_GDRIVE" -O vendor/DehazeFormer/saved_models || \
    echo "⚠️  Falló gdown para DehazeFormer; descarga manual necesaria."
fi
if [ -n "${GUNET_GDRIVE:-}" ] && [ -d vendor/gUNet ]; then
  echo "↓ Descargando pesos de gUNet desde Google Drive…"
  gdown --folder "$GUNET_GDRIVE" -O vendor/gUNet/saved_models || \
    echo "⚠️  Falló gdown para gUNet; descarga manual necesaria."
fi

# ¿Existe al menos un peso utilizable? Solo entonces marcamos el entorno como listo.
HAY_PESO=0
for p in \
  vendor/DehazeFormer/saved_models/outdoor/dehazeformer-b.pth \
  vendor/DehazeFormer/saved_models/outdoor/dehazeformer-l.pth \
  vendor/gUNet/saved_models/outdoor/gunet_b.pth; do
  [ -f "$p" ] && HAY_PESO=1
done

if [ "$HAY_PESO" -eq 1 ]; then
  touch .venv-dehazeformer/.ok
  echo "✅ DehazeFormer listo (quitar neblina). gUNet disponible como modo rápido."
else
  echo "ℹ️  Falta bajar los pesos (Google Drive). Carpeta oficial de DehazeFormer:"
  echo "    https://drive.google.com/drive/folders/1Yy_GH6_bydYPU6_JJzFQwig4LTh86VI4"
  echo "    Coloca, por ejemplo:"
  echo "      vendor/DehazeFormer/saved_models/outdoor/dehazeformer-b.pth"
  echo "      vendor/gUNet/saved_models/outdoor/gunet_b.pth   (modo rápido)"
  echo "    O reejecuta con los IDs/URLs de las carpetas de Drive:"
  echo "      DEHAZEFORMER_GDRIVE='<id-o-url>' GUNET_GDRIVE='<id-o-url>' bash install/extras_dehazeformer.sh"
  echo "    (NO se marcó .venv-dehazeformer/.ok hasta que exista un peso.)"
fi
deactivate
