#!/usr/bin/env bash
# VideoBoost · NAFNet (MIT) — denoise (SIDD) + deblur (GoPro) por imagen, red
# simple sin difusión. Funciona en Mac (MPS/CPU) y en NVIDIA/CUDA. Venv propio.
#
# Los pesos están en Google Drive. Patrón NAFNET_GDRIVE: si gdown está disponible
# se descargan solos; si no, se imprimen instrucciones manuales. NO se marca .ok
# hasta que exista al menos un .pth, igual que las demás extras con pesos en Drive.
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

# En Mac (sin nvidia-smi) instalamos torch CPU/MPS desde el índice por defecto;
# en NVIDIA, ruedas CUDA. NAFNet es una CNN normal: no necesita extensión CUDA.
TORCH_ARGS=""
command -v nvidia-smi >/dev/null 2>&1 && TORCH_ARGS="--index-url https://download.pytorch.org/whl/cu124"

echo "== NAFNet (denoise/deblur por imagen) =="
"$PY" -m venv .venv-nafnet
source .venv-nafnet/bin/activate
pip install --upgrade pip
pip install torch torchvision $TORCH_ARGS

mkdir -p vendor
if [ ! -d vendor/NAFNet ]; then
  git clone --depth 1 https://github.com/megvii-research/NAFNet.git vendor/NAFNet
fi

# basicsr embebido de NAFNet exige numpy<2 (usa np.float, APIs viejas).
pip install -r vendor/NAFNet/requirements.txt "numpy<2"
# Compila/instala el basicsr vendorizado en modo develop (sin extensión CUDA:
# NAFNet no la necesita y así corre igual en Mac).
( cd vendor/NAFNet && python setup.py develop --no_cuda_ext )
# gdown para bajar los pesos de Google Drive automáticamente.
pip install gdown

# ---- Pesos (Google Drive) -------------------------------------------------
PESOS_DIR="vendor/NAFNet/experiments/pretrained_models"
mkdir -p "$PESOS_DIR"

# IDs oficiales de los pesos width64 (de docs/SIDD.md y docs/GoPro.md del repo).
SIDD_ID="14Fht1QQJ2gMlk4N1ERCRuElg8JfjrWWR"   # NAFNet-SIDD-width64.pth (denoise)
GOPRO_ID="1S0PVRbyTakYY9a82kujgZLbMihfNBLfC"   # NAFNet-GoPro-width64.pth (deblur)

bajar() {  # bajar <id> <destino>
  local id="$1" dst="$2"
  [ -f "$dst" ] && { echo "   ya existe: $dst"; return 0; }
  echo "-- descargando $(basename "$dst") de Google Drive…"
  gdown --id "$id" -O "$dst" || echo "   ⚠️ no se pudo descargar $(basename "$dst")"
}

# Permite forzar la fuente manualmente con NAFNET_GDRIVE=<carpeta> (pesos ya bajados).
if [ -n "${NAFNET_GDRIVE:-}" ] && [ -d "${NAFNET_GDRIVE}" ]; then
  echo "-- copiando pesos desde NAFNET_GDRIVE=${NAFNET_GDRIVE}"
  cp -n "${NAFNET_GDRIVE}"/NAFNet-SIDD-width64.pth  "$PESOS_DIR"/ 2>/dev/null || true
  cp -n "${NAFNET_GDRIVE}"/NAFNet-GoPro-width64.pth "$PESOS_DIR"/ 2>/dev/null || true
else
  bajar "$SIDD_ID"  "$PESOS_DIR/NAFNet-SIDD-width64.pth"
  bajar "$GOPRO_ID" "$PESOS_DIR/NAFNet-GoPro-width64.pth"
fi

deactivate

# Solo marcamos .ok si existe al menos un peso (si Drive limita la descarga, el
# usuario coloca el .pth a mano y vuelve a correr el instalador).
if [ -f "$PESOS_DIR/NAFNet-SIDD-width64.pth" ] || [ -f "$PESOS_DIR/NAFNet-GoPro-width64.pth" ]; then
  touch .venv-nafnet/.ok
  echo "✅ NAFNet listo."
else
  echo "⚠️ NAFNet instalado, pero FALTAN los pesos (Google Drive pudo limitar la descarga)."
  echo "   Descarga manualmente y colócalos en: $PESOS_DIR/"
  echo "     denoise:  https://drive.google.com/file/d/$SIDD_ID/view  -> NAFNet-SIDD-width64.pth"
  echo "     deblur:   https://drive.google.com/file/d/$GOPRO_ID/view -> NAFNet-GoPro-width64.pth"
  echo "   o pásalos con: NAFNET_GDRIVE=/ruta/a/pesos bash install/extras_nafnet.sh"
  echo "   (no se marcó .ok hasta que exista al menos un peso)."
fi
