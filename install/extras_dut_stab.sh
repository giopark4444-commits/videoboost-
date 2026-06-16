#!/usr/bin/env bash
# PixelBooster · DUT (Annbless/DUTCode, MIT) — estabilización de VIDEO por IA.
# Pensado para NVIDIA/CUDA (el script hace .cuda() y PWCNet usa cupy). Venv propio.
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

# En NVIDIA, ruedas CUDA; en Mac, la rueda por defecto (sin CUDA → solo sintaxis).
TORCH_ARGS=""
HAS_NV=""
command -v nvidia-smi >/dev/null 2>&1 && { TORCH_ARGS="--index-url https://download.pytorch.org/whl/cu124"; HAS_NV="1"; }

echo "== DUT (estabilización de video por IA) =="
"$PY" -m venv .venv-dut
source .venv-dut/bin/activate
pip install --upgrade pip
pip install torch torchvision $TORCH_ARGS

mkdir -p vendor
if [ ! -d vendor/DUTCode ]; then
  git clone --depth 1 https://github.com/Annbless/DUTCode.git vendor/DUTCode
fi

# Dependencias del repo SIN las pines antiguas/imposibles (numpy 1.18, opencv 4.2,
# scikit-* viejos) que rompen en Python 3.10+; instalamos versiones modernas.
pip install easydict imageio matplotlib networkx numpy opencv-python \
  Pillow pypng scikit-image scikit-learn scipy six tensorboardX tqdm \
  imageio-ffmpeg
# cupy SOLO en NVIDIA (PWCNet lo necesita; no existe rueda para Mac sin CUDA).
if [ -n "$HAS_NV" ]; then
  pip install cupy-cuda12x || pip install cupy || \
    echo "⚠️  No se pudo instalar cupy; PWCNet podría fallar. Instálalo a mano."
fi

# --- Pesos (4 .pth en ckpt/) ---
# Viven en una carpeta de Google Drive (sin URL directa). Opciones:
#   DUT_GDRIVE=<id_carpeta>  → se baja con gdown
# Si no, deja instrucciones para colocarlos a mano y NO marca .ok.
mkdir -p vendor/DUTCode/ckpt
CKPT=vendor/DUTCode/ckpt
if [ ! -f "$CKPT/smoother.pth" ] && [ -n "${DUT_GDRIVE:-}" ]; then
  pip install -q gdown
  gdown --folder "${DUT_GDRIVE}" -O "$CKPT" || gdown "${DUT_GDRIVE}" -O "$CKPT/"
  # Si la carpeta de Drive se descargó anidada, sube los .pth al nivel de ckpt/.
  find "$CKPT" -mindepth 2 -name '*.pth' -exec mv -f {} "$CKPT/" \; 2>/dev/null || true
  find "$CKPT" -mindepth 2 -name '*.pth.tar' -exec mv -f {} "$CKPT/" \; 2>/dev/null || true
  find "$CKPT" -mindepth 2 -name '*.pytorch' -exec mv -f {} "$CKPT/" \; 2>/dev/null || true
fi

if [ -f "$CKPT/smoother.pth" ] && [ -f "$CKPT/RFDet_640.pth.tar" ]; then
  touch .venv-dut/.ok
  echo "✅ DUT listo."
else
  echo "⚠️  Faltan los pesos. Descarga el ZIP de pesos desde el README de"
  echo "    Annbless/DUTCode (Google Drive) y descomprime en vendor/DUTCode/ckpt/"
  echo "    (smoother.pth, RFDet_640.pth.tar, network-default.pytorch, MotionPro.pth,"
  echo "     DIFNet2.pth, stabNet.pth); luego: touch .venv-dut/.ok"
fi
deactivate
