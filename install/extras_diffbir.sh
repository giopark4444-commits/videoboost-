#!/usr/bin/env bash
# PixelBooster · DiffBIR (Apache-2.0) — restauración ciega por difusión (caras +
# escena). Pensado para NVIDIA; en Mac corre por CPU (lentísimo). Venv propio.
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

echo "== DiffBIR (restauración por difusión) =="
"$PY" -m venv .venv-diffbir
source .venv-diffbir/bin/activate
pip install --upgrade pip
pip install torch torchvision $TORCH_ARGS
mkdir -p vendor
if [ ! -d vendor/DiffBIR ]; then
  git clone --depth 1 https://github.com/XPixelGroup/DiffBIR.git vendor/DiffBIR
fi
pip install -r vendor/DiffBIR/requirements.txt "numpy<2"
touch .venv-diffbir/.ok
deactivate
echo "✅ DiffBIR listo. Los pesos se descargan de HuggingFace en el primer uso."
