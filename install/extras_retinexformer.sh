#!/usr/bin/env bash
# PixelBooster · Retinexformer (MIT) — realce de imágenes con POCA LUZ.
# Transformer Retinex sobre BasicSR. Pensado para NVIDIA; en Mac corre por CPU
# (lentísimo). Venv propio .venv-retinexformer.
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

echo "== Retinexformer (poca luz) =="
"$PY" -m venv .venv-retinexformer
source .venv-retinexformer/bin/activate
pip install --upgrade pip
pip install torch torchvision $TORCH_ARGS

mkdir -p vendor
if [ ! -d vendor/Retinexformer ]; then
  git clone --depth 1 https://github.com/caiyuanhao1998/Retinexformer.git vendor/Retinexformer
fi

# Dependencias del repo (las que lista su README). OJO: NO instalamos el paquete
# `basicsr` de pip a propósito: el genérico (a) NO trae la arquitectura
# RetinexFormer y (b) rompe al importar torchvision.transforms.functional_tensor
# (eliminado en torchvision >= 0.17). Usamos el basicsr REESTRUCTURADO que el
# repo trae embebido. numpy<2 obligatorio (skimage/basicsr no soportan numpy 2.x).
pip install \
  matplotlib scikit-learn scikit-image opencv-python yacs joblib natsort \
  h5py tqdm tensorboard einops gdown addict future lmdb pyyaml requests \
  scipy yapf lpips thop timm "numpy<2"

# Por si una corrida previa dejó el basicsr de pip instalado (haría sombra al del
# repo): quitarlo. Silencioso si no estaba.
pip uninstall -y basicsr >/dev/null 2>&1 || true

# Registrar el basicsr embebido SIN `python setup.py develop` (su build editable
# falla en Python 3.12). Dos pasos:
#   1) el repo NO trae basicsr/__init__.py de nivel superior -> lo creamos mínimo
#      para que `basicsr` sea un paquete regular importable.
#   2) un .pth en site-packages añade la raíz del repo a sys.path, así
#      `import basicsr` resuelve a ESTE basicsr aunque el script corra desde
#      Enhancement/. (Equivale a lo que haría `setup.py develop`.)
INIT="vendor/Retinexformer/basicsr/__init__.py"
if [ ! -f "$INIT" ]; then
  cat > "$INIT" <<'PYINIT'
# flake8: noqa
# BasicSR reestructurado y embebido por Retinexformer (caiyuanhao1998, MIT).
# El repo depende de `python setup.py develop` (build editable que falla en
# Python 3.12) para registrar este paquete; PixelBooster lo suple con este
# __init__ mínimo + un .pth (ver install/extras_retinexformer.sh).
PYINIT
fi
REPO_ABS="$(cd vendor/Retinexformer && pwd)"
SITEPKG="$(python -c 'import site; print(site.getsitepackages()[0])')"
echo "$REPO_ABS" > "$SITEPKG/_retinexformer_repo.pth"
echo "  basicsr embebido registrado vía .pth -> $REPO_ABS"

# --- Pesos preentrenados (modelo por defecto: LOL_v2_real, poca luz real) -----
# El repo publica los pesos en Google Drive / Baidu (carpeta pretrained_weights).
# ⚠️ El ID EXACTO de la carpeta de Drive NO se pudo confirmar con certeza al
# escribir esto (posible cambio del repo). Por eso permitimos:
#   1) RETINEX_GDRIVE = ID/URL de la carpeta de Drive -> se baja con gdown, o
#   2) RETINEX_WEIGHT_URL = URL directa al .pth, o
#   3) colocar el archivo a mano en vendor/Retinexformer/pretrained_weights/.
mkdir -p vendor/Retinexformer/pretrained_weights
DEST="vendor/Retinexformer/pretrained_weights/LOL_v2_real.pth"

if [ ! -f "$DEST" ]; then
  if [ -n "${RETINEX_WEIGHT_URL:-}" ]; then
    echo "Descargando peso desde RETINEX_WEIGHT_URL…"
    curl -L "$RETINEX_WEIGHT_URL" -o "$DEST"
  elif [ -n "${RETINEX_GDRIVE:-}" ]; then
    echo "Descargando carpeta de Google Drive (RETINEX_GDRIVE) con gdown…"
    gdown --folder "$RETINEX_GDRIVE" -O vendor/Retinexformer/pretrained_weights || true
  else
    echo "⚠️ No se descargó el peso automáticamente."
    echo "   Baja 'LOL_v2_real.pth' (o el modelo que prefieras) del repo:"
    echo "     https://github.com/caiyuanhao1998/Retinexformer  (sección Pretrained Weights)"
    echo "   Google Drive / Baidu -> colócalo en:"
    echo "     vendor/Retinexformer/pretrained_weights/LOL_v2_real.pth"
    echo "   O reexporta RETINEX_GDRIVE / RETINEX_WEIGHT_URL y vuelve a correr este script."
  fi
fi

# Marcador de venv listo solo si el peso quedó en su sitio.
if [ -f "$DEST" ]; then
  touch .venv-retinexformer/.ok
  echo "✅ Retinexformer listo (peso LOL_v2_real presente)."
else
  echo "ℹ️ Entorno instalado, pero FALTA el peso. Colócalo y crea el marcador:"
  echo "     touch .venv-retinexformer/.ok"
fi
deactivate
