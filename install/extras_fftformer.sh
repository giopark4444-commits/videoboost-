#!/usr/bin/env bash
# PixelBooster · FFTformer (MIT) — desenfoque de movimiento (motion deblur) SOTA
# por Transformer en el dominio de frecuencia (34.21 dB en GoPro). Pensado para
# NVIDIA (el test.py fija device cuda); en Mac no corre. Venv propio. NO probado
# en GPU real desde el Mac.
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

TORCH_ARGS=""
command -v nvidia-smi >/dev/null 2>&1 && TORCH_ARGS="--index-url https://download.pytorch.org/whl/cu124"

echo "== FFTformer (motion deblur por Transformer en frecuencia) =="
"$PY" -m venv .venv-fftformer
source .venv-fftformer/bin/activate
pip install --upgrade pip
pip install torch torchvision $TORCH_ARGS

mkdir -p vendor
if [ ! -d vendor/FFTformer ]; then
  # El clon trae COMMITEADO el peso GoPro (pretrain_model/fftformer_GoPro.pth, ~66 MB).
  git clone --depth 1 https://github.com/kkkls/FFTformer.git vendor/FFTformer
fi

# Dependencias del repo (estilo BasicSR). numpy<2 para evitar el choque ABI de
# basicsr/opencv en Python moderno. tb-nightly del requirements lo cambiamos por
# tensorboard estable.
pip install -r vendor/FFTformer/requirements.txt "numpy<2" || true
pip install tensorboard lpips

# test.py importa basicsr.models.archs.fftformer_arch desde el PROPIO repo, así
# que instalamos su basicsr en modo develop (sin la extensión CUDA, igual que
# hace su test.sh con `setup.py develop --no_cuda_ext`).
( cd vendor/FFTformer && python setup.py develop --no_cuda_ext ) || \
  pip install basicsr || true

# Peso RealBlur: está en Google Drive (no en el repo). Si tienes el ID/URL de la
# carpeta, pásalo en FFTFORMER_GDRIVE para bajarlo solo; si no, colócalo a mano
# como vendor/FFTformer/pretrain_model/fftformer_RealBlur.pth. El motor funciona
# igual con GoPro (que ya llegó con el clon).
pip install gdown
REALBLUR="vendor/FFTformer/pretrain_model/fftformer_RealBlur.pth"
if [ ! -f "$REALBLUR" ]; then
  if [ -n "${FFTFORMER_GDRIVE:-}" ]; then
    echo "↓ Descargando peso RealBlur de FFTformer desde Google Drive…"
    gdown --fuzzy "$FFTFORMER_GDRIVE" -O "$REALBLUR" || \
      gdown --folder "$FFTFORMER_GDRIVE" -O vendor/FFTformer/pretrain_model/ || true
  else
    echo "ℹ️  (Opcional) Falta el peso RealBlur (Google Drive):"
    echo "    https://drive.google.com/drive/folders/1l_R8_2UKfiQP_BYrgcQrmCBSe_ogwL41"
    echo "    Colócalo en: $REALBLUR  (o reejecuta con FFTFORMER_GDRIVE='<id-o-url>')."
    echo "    No es necesario: el modo GoPro ya está listo."
  fi
fi

# Solo marcamos .ok si el peso GoPro (commiteado en el repo) existe de verdad.
if [ -f vendor/FFTformer/pretrain_model/fftformer_GoPro.pth ]; then
  touch .venv-fftformer/.ok
  echo "✅ FFTformer listo (motion deblur GoPro, MIT). RealBlur es opcional."
else
  echo "❌ No apareció el peso GoPro (pretrain_model/fftformer_GoPro.pth). Revisa el clon."
  deactivate
  exit 1
fi
deactivate
