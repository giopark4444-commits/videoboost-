#!/usr/bin/env bash
# PixelBooster · DreamClear (shallowdream204/DreamClear, Apache-2.0) — restauración
# real-world fotorealista de máxima calidad (NeurIPS 2024). Difusión de alta capacidad
# sobre PixArt-α-1024 + SwinIR + VAE + T5-XXL. SOLO NVIDIA/CUDA y MUCHA VRAM.
# Entorno propio .venv-dreamclear. Python 3.9 según su repo (admitimos 3.9–3.11).
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "❌ DreamClear requiere GPU NVIDIA/CUDA y mucha VRAM. En Mac usa SeedVR2."
  exit 1
fi

# El repo fija python=3.9; aceptamos 3.9–3.11 (xformers/mmcv viejos no van en 3.12+).
PY=""
for c in python3.11 python3.10 python3.9 python3; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if (3,9) <= sys.version_info[:2] <= (3,11) else 1)' 2>/dev/null; then
    PY="$c"; break
  fi
done
[ -z "$PY" ] && { echo "❌ Necesitas Python 3.9–3.11 para DreamClear."; exit 1; }

echo "== DreamClear (restauración real-world, Apache-2.0) =="
"$PY" -m venv .venv-dreamclear
source .venv-dreamclear/bin/activate
pip install --upgrade pip

# Torch CUDA. El repo está validado con torch 2.1.1 (cu121); usamos esa familia.
pip install torch==2.1.1 torchvision==0.16.1 torchaudio==2.1.1 \
  --index-url https://download.pytorch.org/whl/cu121

mkdir -p vendor models/DreamClear
if [ ! -d vendor/DreamClear ]; then
  git clone --depth 1 https://github.com/shallowdream204/DreamClear.git vendor/DreamClear
fi
pip install -r vendor/DreamClear/requirements.txt
# numpy<2: el ecosistema (mmcv 1.7, opencv, timm 0.6) se escribió contra numpy 1.x.
pip install "numpy<2"
pip install "huggingface_hub[cli]"

echo "↓ Descargando pesos de DreamClear (~14 GB; DreamClear-1024.pth solo ya pesa ~8.9 GB)…"
python - <<'PY'
from huggingface_hub import snapshot_download
# Repo de los autores: trae DreamClear, PixArt base, SwinIR, VAE y T5-XXL.
# Excluimos los pesos RMT (detección/segmentación) que son para datos/entrenamiento,
# no para inferencia, y pesan >1 GB.
snapshot_download(
    "shallowdream204/DreamClear",
    local_dir="models/DreamClear",
    ignore_patterns=["rmt_*.pth"],
)
print("✅ Pesos base de DreamClear en models/DreamClear/")
PY

cat <<'NOTE'
ℹ️ LLaVA (caption) es OPCIONAL y pesa ~26 GB; NO se baja por defecto.
   Si tu 4080 tiene VRAM de sobra y quieres usarlo, descárgalo a mano:
     source .venv-dreamclear/bin/activate
     huggingface-cli download liuhaotian/llava-v1.6-vicuna-13b \
       --local-dir models/DreamClear/llava-v1.6-vicuna-13b
   y pasa usar_llava=True desde el engine.
⚠️ Motor MUY pesado y lento; en 16 GB puede requerir bajar --latent_tiled_size
   y dejar LLaVA fuera. Verificar flags reales en la GPU al estrenarlo.
NOTE

touch .venv-dreamclear/.ok
deactivate
echo "✅ DreamClear listo."
