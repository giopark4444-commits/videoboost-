#!/usr/bin/env bash
# VideoBoost · InstantIR — restauración de imágenes instantánea (Apache 2.0).
# SOLO NVIDIA/CUDA. Construido sobre SDXL + DINOv2. Entorno propio.
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "❌ InstantIR requiere GPU NVIDIA/CUDA. En Mac usa SeedVR2."
  exit 1
fi

echo "== InstantIR (restauración de imágenes, Apache 2.0) =="
python3 -m venv .venv-instantir
source .venv-instantir/bin/activate
pip install --upgrade pip
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
mkdir -p vendor models
if [ ! -d vendor/InstantIR ]; then
  git clone --depth 1 https://github.com/instantX-research/InstantIR.git vendor/InstantIR
fi
pip install -r vendor/InstantIR/requirements.txt
pip install "huggingface_hub[cli]"

echo "↓ Descargando modelos (SDXL ~7 GB, DINOv2, pesos InstantIR)…"
python - <<'PY'
from huggingface_hub import snapshot_download, hf_hub_download
snapshot_download("stabilityai/stable-diffusion-xl-base-1.0", local_dir="models/sdxl-base-1.0")
snapshot_download("facebook/dinov2-large", local_dir="models/dinov2-large")
# Pesos de InstantIR (adapter + aggregator + previewer LoRA).
snapshot_download("InstantX/InstantIR", local_dir="models/InstantIR")
print("✅ Modelos de InstantIR en models/")
PY
deactivate
echo "✅ InstantIR listo."
