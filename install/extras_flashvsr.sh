#!/usr/bin/env bash
# VideoBoost · FlashVSR (CVPR 2026) — modo rápido EXPERIMENTAL. Solo NVIDIA:
# usa kernels CUDA de atención dispersa que no existen para Mac.
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "❌ FlashVSR requiere GPU NVIDIA con CUDA. En Mac usa SeedVR2."
  exit 1
fi

echo "== FlashVSR (experimental) =="
python3 -m venv .venv-flashvsr
source .venv-flashvsr/bin/activate
pip install --upgrade pip
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
mkdir -p vendor
if [ ! -d vendor/FlashVSR ]; then
  git clone --depth 1 https://github.com/OpenImagingLab/FlashVSR.git vendor/FlashVSR
fi
if [ -f vendor/FlashVSR/requirements.txt ]; then
  pip install -r vendor/FlashVSR/requirements.txt
fi
pip install huggingface_hub
deactivate

echo ""
echo "⚠️ Los pesos de FlashVSR se descargan según su README (HuggingFace, Git LFS):"
echo "   https://github.com/OpenImagingLab/FlashVSR#readme"
echo "   Es la pieza más nueva del stack; si algo falla, SeedVR2 cubre lo mismo con más calidad."
