#!/usr/bin/env bash
# PixelBooster · SCUNet (Apache-2.0) — denoise ciego de fotos reales (Swin-Conv-UNet).
# CNN ligera, no difusión: corre en NVIDIA (CUDA) y también por CPU en Mac (más
# lento pero usable). Venv propio. Los pesos se bajan del release v1.0 de KAIR.
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

# En NVIDIA usar las ruedas CUDA de PyTorch; en Mac las normales (CPU/MPS).
TORCH_ARGS=""
command -v nvidia-smi >/dev/null 2>&1 && TORCH_ARGS="--index-url https://download.pytorch.org/whl/cu124"

echo "== SCUNet (denoise ciego real) =="
"$PY" -m venv .venv-scunet
source .venv-scunet/bin/activate
pip install --upgrade pip
pip install torch torchvision $TORCH_ARGS
# Dependencias del repo: la red usa einops + timm; el resto utilidades de imagen.
pip install numpy opencv-python einops "timm>=0.6.12" requests "numpy<2"

mkdir -p vendor
if [ ! -d vendor/SCUNet ]; then
  git clone --depth 1 https://github.com/cszn/SCUNet.git vendor/SCUNet
fi

# Pesos en la carpeta compartida del proyecto models/SCUNet/ (la que lee el engine).
# El script de descarga del repo trae los 8 .pth desde el release v1.0 de KAIR.
PESOS_DIR="$(pwd)/models/SCUNet"
mkdir -p "$PESOS_DIR"
echo "== Descargando pesos SCUNet (release v1.0 de KAIR) a models/SCUNet/ =="
( cd vendor/SCUNet && python main_download_pretrained_models.py --models "SCUNet" --model_dir "$PESOS_DIR" ) || \
  echo "⚠️ Falló la descarga automática. Baja los .pth de https://github.com/cszn/KAIR/releases/tag/v1.0 a models/SCUNet/ a mano."

deactivate

# Solo marcamos .ok si existe al menos el peso "real" principal: sin él el motor
# no funciona (no hay autodescarga en tiempo de inferencia).
if [ -f "$PESOS_DIR/scunet_color_real_psnr.pth" ]; then
  touch .venv-scunet/.ok
  echo "✅ SCUNet listo (pesos en models/SCUNet/)."
else
  echo "❌ Falta models/SCUNet/scunet_color_real_psnr.pth. No marco .ok hasta que el peso exista."
  exit 1
fi
