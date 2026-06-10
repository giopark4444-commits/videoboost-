#!/usr/bin/env bash
# VideoBoost · Motores de imágenes: HYPIR (siempre) y SUPIR (con --supir).
# Cada uno va en su propio venv porque sus dependencias de diffusers chocan
# entre sí y con las de SeedVR2.
#
# Licencia: HYPIR y SUPIR son de uso NO comercial sin permiso de sus autores.
set -euo pipefail
cd "$(dirname "$0")/.."

# PyTorch según plataforma: CUDA en Linux/NVIDIA, MPS (wheels estándar) en Mac.
TORCH_ARGS=""
if command -v nvidia-smi >/dev/null 2>&1; then
  TORCH_ARGS="--index-url https://download.pytorch.org/whl/cu124"
fi

echo "== HYPIR (restauración de imágenes, SIGGRAPH 2025) =="
python3 -m venv .venv-imagenes
source .venv-imagenes/bin/activate
pip install --upgrade pip
pip install torch torchvision $TORCH_ARGS
mkdir -p vendor models
if [ ! -d vendor/HYPIR ]; then
  git clone --depth 1 https://github.com/XPixelGroup/HYPIR.git vendor/HYPIR
fi
pip install -r vendor/HYPIR/requirements.txt
pip install huggingface_hub
echo "↓ Descargando pesos HYPIR_sd2.pth…"
python - <<'PY'
from huggingface_hub import hf_hub_download
hf_hub_download("lxq007/HYPIR", "HYPIR_sd2.pth", local_dir="models/HYPIR")
print("✅ Pesos de HYPIR en models/HYPIR/")
PY
deactivate
echo "✅ HYPIR listo."

if [ "${1:-}" = "--supir" ]; then
  echo ""
  echo "== SUPIR (máximo detalle; pesado, ideal RTX 4080) =="
  python3 -m venv .venv-supir
  source .venv-supir/bin/activate
  pip install --upgrade pip
  pip install torch torchvision $TORCH_ARGS
  if [ ! -d vendor/SUPIR ]; then
    git clone --depth 1 https://github.com/Fanghua-Yu/SUPIR.git vendor/SUPIR
  fi
  pip install -r vendor/SUPIR/requirements.txt
  deactivate
  echo "⚠️ SUPIR necesita configurar sus pesos a mano (SUPIR-v0Q, SDXL, CLIP)."
  echo "   Sigue el README de vendor/SUPIR — es el motor más quisquilloso del stack."
fi
