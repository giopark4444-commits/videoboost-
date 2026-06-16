#!/usr/bin/env bash
# PixelBooster · SeedVR2 en MLX (vía mflux, MIT) — restauración por difusión NATIVA
# de Apple Silicon. Solo Mac con chip M (MLX no existe en NVIDIA/Linux). Venv propio.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ "$(uname -s)" != "Darwin" ] || [ "$(uname -m)" != "arm64" ]; then
  echo "❌ SeedVR2 (MLX) requiere un Mac con chip Apple (M1/M2/M3/M4). En NVIDIA usa SeedVR2 normal."
  exit 1
fi

# Python 3.10+ (preferir python@3.12; instalarlo con Homebrew si falta).
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

echo "== SeedVR2 (MLX) vía mflux =="
"$PY" -m venv .venv-mlx
source .venv-mlx/bin/activate
pip install --upgrade pip
pip install mflux
touch .venv-mlx/.ok
deactivate
echo "✅ SeedVR2 (MLX) listo. Los pesos se descargan de HuggingFace en el primer uso."
