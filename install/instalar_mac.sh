#!/usr/bin/env bash
# VideoBoost · Instalador para Mac con chip M (Apple Silicon).
# Instala: ffmpeg, entorno Python, PyTorch (MPS/Metal), SeedVR2 y motores Vulkan.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== VideoBoost · instalador para Mac (Apple Silicon) =="

# 1. FFmpeg: ya no es obligatorio instalarlo a mano — viene por pip
#    (imageio-ffmpeg en requirements.txt). Si Homebrew ya lo tiene, mejor (trae
#    ffprobe), pero NO bloqueamos la instalación si falta.

# 2. Entorno Python principal (app + SeedVR2)
echo "🐍 Creando entorno .venv…"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
# En Mac los wheels estándar de PyTorch ya traen soporte MPS (Metal).
pip install torch torchvision torchaudio

# 3. SeedVR2 (integración de numz, con CLI standalone y soporte Apple Silicon)
mkdir -p vendor models
if [ ! -d vendor/seedvr2 ]; then
  echo "📦 Clonando SeedVR2…"
  git clone --depth 1 https://github.com/numz/ComfyUI-SeedVR2_VideoUpscaler.git vendor/seedvr2
fi
pip install -r vendor/seedvr2/requirements.txt

# 4. Motores Vulkan (funcionan vía MoltenVK en Mac)
python install/descargar_vulkan.py

echo ""
echo "✅ Instalación base completa. Ejecuta ./iniciar.sh"
echo "   Motores de imagen extra: install/extras_caras.sh (caras) · install/extras_color.sh (color)"
