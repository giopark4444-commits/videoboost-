#!/usr/bin/env bash
# VideoBoost · PMRF (MIT) — restauración de caras (caras alineadas). Pensado
# para NVIDIA. Venv propio.
set -euo pipefail
cd "$(dirname "$0")/.."

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

echo "== PMRF (restauración de caras) =="
"$PY" -m venv .venv-pmrf
source .venv-pmrf/bin/activate
pip install --upgrade pip
pip install torch torchvision $TORCH_ARGS
mkdir -p vendor
if [ ! -d vendor/PMRF ]; then
  git clone --depth 1 https://github.com/ohayonguy/PMRF.git vendor/PMRF
fi
pip install -r vendor/PMRF/requirements.txt "numpy<2"
pip install huggingface_hub
touch .venv-pmrf/.ok
deactivate
echo "✅ PMRF listo. El modelo se descarga de HuggingFace en el primer uso."
