#!/usr/bin/env bash
# PixelBooster · Restormer (MIT) — restaurador por Transformer eficiente (deblur de
# movimiento/defocus, quitar lluvia, denoise real). Pensado para NVIDIA; en Mac
# corre por CPU (lento). Venv propio. NO probado en GPU real desde el Mac.
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

echo "== Restormer (Transformer de restauración de imagen) =="
"$PY" -m venv .venv-restormer
source .venv-restormer/bin/activate
pip install --upgrade pip
pip install torch torchvision $TORCH_ARGS

mkdir -p vendor
if [ ! -d vendor/Restormer ]; then
  git clone --depth 1 https://github.com/swz30/Restormer.git vendor/Restormer
fi

# Dependencias de demo.py (estilo BasicSR). El repo es de Python 3.7/torch 1.8 y NO
# trae requirements.txt; listamos sus imports a mano. numpy<2 para evitar el choque
# ABI de basicsr/opencv en Python moderno.
pip install \
  scikit-image opencv-python yacs natsort h5py tqdm \
  einops gdown addict future lmdb pyyaml requests scipy yapf lpips \
  "numpy<2"

# basicsr en modo develop dentro del repo: demo.py carga la arquitectura con
# runpy.run_path('basicsr/models/archs/restormer_arch.py'), así que basta con que el
# paquete basicsr esté disponible. Lo instalamos desde PyPI (más estable que el
# setup.py viejo del repo).
pip install basicsr || true

# Pesos preentrenados (release v1.0 de GitHub). demo.py NO autodescarga: cada tarea
# busca un .pth en una ruta relativa fija; los colocamos ahí. Solo las 4 tareas que
# exponemos en engines/restormer.py.
REL="https://github.com/swz30/Restormer/releases/download/v1.0"
declare -a PESOS=(
  "Motion_Deblurring/pretrained_models|motion_deblurring.pth"
  "Defocus_Deblurring/pretrained_models|single_image_defocus_deblurring.pth"
  "Deraining/pretrained_models|deraining.pth"
  "Denoising/pretrained_models|real_denoising.pth"
)
for item in "${PESOS[@]}"; do
  dir="vendor/Restormer/${item%%|*}"
  file="${item##*|}"
  mkdir -p "$dir"
  if [ ! -f "$dir/$file" ]; then
    echo "⬇️  $file"
    curl -L --fail -o "$dir/$file" "$REL/$file"
  fi
done

touch .venv-restormer/.ok
deactivate
echo "✅ Restormer listo (deblur / deraining / denoise, MIT)."
