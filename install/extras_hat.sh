#!/usr/bin/env bash
# PixelBooster · HAT (Apache-2.0) — Hybrid Attention Transformer, super-resolución
# clásica (NO difusión) muy nítida. Pensado para NVIDIA; en Mac corre por CPU
# (lentísimo). Venv propio .venv-hat. Basado en BasicSR.
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

# torch desde el índice CUDA solo si hay GPU NVIDIA.
TORCH_ARGS=""
command -v nvidia-smi >/dev/null 2>&1 && TORCH_ARGS="--index-url https://download.pytorch.org/whl/cu124"

echo "== HAT (super-resolución nítida, no-difusión) =="
"$PY" -m venv .venv-hat
source .venv-hat/bin/activate
pip install --upgrade pip
pip install torch torchvision $TORCH_ARGS

mkdir -p vendor
if [ ! -d vendor/HAT ]; then
  git clone --depth 1 https://github.com/XPixelGroup/HAT.git vendor/HAT
fi

# Dependencias del repo (einops, basicsr==1.3.4.9). IMPORTANTE: basicsr arrastra
# APIs antiguas que rompen con numpy>=2 (np.float, etc.); fijamos numpy<2.
pip install -r vendor/HAT/requirements.txt "numpy<2"

# HAT registra sus arquitecturas/modelos en BasicSR vía `setup.py develop`.
# OJO (verificar en GPU real): este paso a veces es quisquilloso —
#   - puede requerir compilar; si falla, probar `pip install -e vendor/HAT`.
#   - basicsr 1.3.4.9 importa `torchvision.transforms.functional_tensor`, que
#     fue eliminado en torchvision>=0.17. Si revienta el import, hay dos salidas:
#       1) instalar torchvision<0.17, o
#       2) parchear basicsr/data/degradations.py para importar desde
#          `torchvision.transforms.functional`.
( cd vendor/HAT && python setup.py develop ) || {
  echo "⚠️  'python setup.py develop' falló; intentando 'pip install -e .' ...";
  pip install -e vendor/HAT;
}

# Pesos Real_HAT_GAN_SRx4 (variante recomendada para fotos reales: mejor fidelidad).
# Fuente oficial: carpeta de Google Drive de los autores. gdown baja la carpeta
# y nos quedamos con el .pth que necesitamos.
mkdir -p vendor/HAT/experiments/pretrained_models
PESOS="vendor/HAT/experiments/pretrained_models/Real_HAT_GAN_SRx4.pth"
if [ ! -f "$PESOS" ]; then
  pip install gdown
  echo "Descargando pesos Real_HAT_GAN_SRx4 desde Google Drive (oficial)..."
  TMPW="$(mktemp -d)"
  # Carpeta oficial de pesos de HAT (XPixelGroup).
  gdown --folder "https://drive.google.com/drive/folders/1HpmReFfoUqUbnAOQ7rvOeNU3uf_m69w0" -O "$TMPW" || true
  FOUND="$(find "$TMPW" -name 'Real_HAT_GAN_SRx4.pth' -print -quit || true)"
  if [ -n "$FOUND" ]; then
    mv "$FOUND" "$PESOS"
  else
    echo "⚠️  No se pudo bajar Real_HAT_GAN_SRx4.pth automáticamente."
    echo "    Descárgalo a mano desde:"
    echo "    https://drive.google.com/drive/folders/1HpmReFfoUqUbnAOQ7rvOeNU3uf_m69w0"
    echo "    (o Baidu, código qyrl) y colócalo en:"
    echo "    $PESOS"
  fi
  rm -rf "$TMPW"
fi

[ -f "$PESOS" ] && touch .venv-hat/.ok
deactivate
echo "✅ HAT listo (si los pesos están en experiments/pretrained_models/)."
