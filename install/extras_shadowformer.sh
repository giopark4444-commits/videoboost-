#!/usr/bin/env bash
# PixelBooster · ShadowFormer (MIT) — eliminación de sombras en imágenes con un
# transformer de contexto global (AAAI 2023). Es ligero (no es difusión): corre
# en Mac (MPS/CPU) y en NVIDIA → plataforma ambas. Venv propio.
#
# Pesos en Google Drive (ISTD / ISTD+ / SRD). Si tienes el ID/URL del .pth,
# pásalo en SHADOWFORMER_GDRIVE para bajarlo solo; si no, descárgalo a mano a
# models/ShadowFormer/. NO se marca .ok hasta que exista al menos un peso.
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

# En Mac: torch MPS/CPU del índice por defecto. En NVIDIA: ruedas CUDA.
TORCH_ARGS=""
command -v nvidia-smi >/dev/null 2>&1 && TORCH_ARGS="--index-url https://download.pytorch.org/whl/cu124"

echo "== ShadowFormer (eliminación de sombras) =="
"$PY" -m venv .venv-shadowformer
source .venv-shadowformer/bin/activate
pip install --upgrade pip
pip install torch torchvision $TORCH_ARGS
mkdir -p vendor models/ShadowFormer
if [ ! -d vendor/ShadowFormer ]; then
  git clone --depth 1 https://github.com/GuoLanqing/ShadowFormer.git vendor/ShadowFormer
fi
# El repo SÍ trae requirements.txt, pero fija torch==1.7.1/torchvision==0.8.2
# (incompatibles con Python 3.10+) → NO lo usamos: instalamos torch moderno arriba
# y aquí solo el resto de dependencias ligeras del modelo.
pip install scikit-image opencv-python pillow "numpy<2" einops linformer timm yacs natsort scipy tqdm
pip install gdown

# Pesos: Google Drive. ISTD por defecto (ISTD_model_best.pth). Si pasas el ID o
# la URL en SHADOWFORMER_GDRIVE, lo bajamos; si no, instrucciones manuales.
PESO="models/ShadowFormer/ISTD_model_best.pth"
if [ ! -f "$PESO" ] && [ -n "${SHADOWFORMER_GDRIVE:-}" ]; then
  echo "↓ Descargando pesos de ShadowFormer desde Google Drive…"
  gdown "$SHADOWFORMER_GDRIVE" -O "$PESO" || \
    gdown --folder "$SHADOWFORMER_GDRIVE" -O models/ShadowFormer/ || true
fi

deactivate

# Solo marcamos .ok si ya hay algún peso .pth (sin él el motor no funciona).
if ls models/ShadowFormer/*.pth >/dev/null 2>&1; then
  touch .venv-shadowformer/.ok
  echo "✅ ShadowFormer listo."
else
  echo "ℹ️  Falta bajar los pesos de ShadowFormer (Google Drive)."
  echo "    Descárgalos del README del repo y colócalos en: models/ShadowFormer/"
  echo "    (recomendado renombrar el de ISTD a: ISTD_model_best.pth). O reejecuta con:"
  echo "    SHADOWFORMER_GDRIVE='<id-o-url-del-.pth>' bash install/extras_shadowformer.sh"
  echo "⚠️  No se marcó .venv-shadowformer/.ok hasta que exista el peso."
fi
