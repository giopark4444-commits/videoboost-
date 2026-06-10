#!/usr/bin/env bash
# VideoBoost · Instalador para Linux con GPU NVIDIA.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== VideoBoost · instalador para Linux + NVIDIA =="

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "❌ Falta ffmpeg. Instálalo con tu gestor de paquetes (ej.: sudo apt install ffmpeg)."
  exit 1
fi

echo "🐍 Creando entorno .venv…"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

mkdir -p vendor models
if [ ! -d vendor/seedvr2 ]; then
  echo "📦 Clonando SeedVR2…"
  git clone --depth 1 https://github.com/numz/ComfyUI-SeedVR2_VideoUpscaler.git vendor/seedvr2
fi
pip install -r vendor/seedvr2/requirements.txt

python install/descargar_vulkan.py

echo ""
echo "✅ Instalación base completa. Ejecuta ./iniciar.sh"
echo "   Imágenes: install/extras_faithdiff.sh (recomendado) · extras_instantir.sh · FlashVSR: install/extras_flashvsr.sh"
