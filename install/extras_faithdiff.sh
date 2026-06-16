#!/usr/bin/env bash
# PixelBooster · FaithDiff — restauración fiel de imágenes (MIT, uso comercial libre).
# SOLO NVIDIA/CUDA. Construido sobre SDXL. No descarga LLaVA (no hace falta).
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "❌ FaithDiff requiere GPU NVIDIA/CUDA. En Mac usa SeedVR2."
  exit 1
fi

echo "== FaithDiff (restauración de imágenes, MIT) =="
python3 -m venv .venv-faithdiff
source .venv-faithdiff/bin/activate
pip install --upgrade pip
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
mkdir -p vendor models/FaithDiff
if [ ! -d vendor/FaithDiff ]; then
  git clone --depth 1 https://github.com/JyChen9811/FaithDiff.git vendor/FaithDiff
fi
pip install -r vendor/FaithDiff/requirements.txt
pip install "huggingface_hub[cli]"

echo "↓ Descargando pesos (SDXL RealVisXL ~7 GB, VAE, FaithDiff). Sin LLaVA."
python - <<'PY'
from huggingface_hub import snapshot_download
# Pesos de FaithDiff (incluye FaithDiff.bin y, si aplica, BSRNet.pth).
snapshot_download("jychen9811/FaithDiff", local_dir="models/FaithDiff")
# Base SDXL y VAE fp16 que FaithDiff necesita.
snapshot_download("SG161222/RealVisXL_V4.0", local_dir="models/FaithDiff/Real_4_SDXL")
snapshot_download("madebyollin/sdxl-vae-fp16-fix", local_dir="models/FaithDiff/VAE_FP16")
print("✅ Pesos de FaithDiff en models/FaithDiff/")
PY
deactivate
echo "✅ FaithDiff listo."
