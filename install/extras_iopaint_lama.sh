#!/usr/bin/env bash
# PixelBooster · IOPaint + LaMa (ambos Apache-2.0) — borrar objetos de imágenes por
# inpainting (imagen + máscara). Corre en CPU, CUDA (RTX 4080) y MPS (Mac M).
# IOPaint es un paquete pip: NO se clona repo, se instala "iopaint" en su venv.
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

# torch: rueda CUDA solo si hay NVIDIA; en Mac la rueda por defecto trae MPS.
TORCH_ARGS=""
command -v nvidia-smi >/dev/null 2>&1 && TORCH_ARGS="--index-url https://download.pytorch.org/whl/cu124"

echo "== IOPaint + LaMa (borrado de objetos) =="
"$PY" -m venv .venv-iopaint_lama
source .venv-iopaint_lama/bin/activate
pip install --upgrade pip
# torch primero (deja que iopaint resuelva el resto de sus dependencias).
pip install torch torchvision $TORCH_ARGS
pip install iopaint

# Los pesos de LaMa los descarga IOPaint solo en el primer borrado, a models/IOPaint.
mkdir -p models/IOPaint

# Verificación mínima de que el paquete importa y el CLI existe.
python -c "import iopaint" >/dev/null
touch .venv-iopaint_lama/.ok
deactivate
echo "✅ IOPaint (LaMa) listo. El modelo LaMa se descarga en el primer borrado."
