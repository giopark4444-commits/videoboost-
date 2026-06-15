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
#    La app usa sintaxis de tipos de Python 3.10+ (p.ej. `dict | None`), así que
#    necesitamos un intérprete 3.10 o superior. macOS trae 3.9 de fábrica, por eso
#    buscamos uno válido (preferimos python@3.12 de Homebrew) y lo instalamos si falta.
echo "🐍 Buscando Python 3.10+…"
PY=""
for c in python3.13 python3.12 python3.11 python3.10 python3; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info[:2] >= (3,10) else 1)' 2>/dev/null; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ]; then
  if command -v brew >/dev/null 2>&1; then
    echo "   No hay Python 3.10+. Instalando python@3.12 con Homebrew…"
    brew install python@3.12
    PY="$(brew --prefix)/opt/python@3.12/bin/python3.12"
  else
    echo "❌ Necesitas Python 3.10 o superior (tienes solo el 3.9 del sistema) y no encuentro Homebrew."
    echo "   Instala Homebrew (https://brew.sh) o Python 3.12 (https://www.python.org/downloads/macos/) y reintenta."
    exit 1
  fi
fi
echo "   Usando: $("$PY" --version 2>&1)"
echo "🐍 Creando entorno .venv…"
"$PY" -m venv .venv
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
deactivate

# 5. Extras de imagen que SÍ funcionan en Mac (caras + color). No-fatales: si
#    alguno falla, la instalación base sigue siendo válida. (FaithDiff/InstantIR/
#    FlashVSR son solo-NVIDIA y no se instalan en Mac.)
echo ""
echo "🎭 Instalando extras de imagen para Mac (CodeFormer caras · DDColor color)…"
bash install/extras_caras.sh || echo "⚠️  CodeFormer no se instaló (puedes reintentar: bash install/extras_caras.sh)"
bash install/extras_color.sh || echo "⚠️  DDColor no se instaló (puedes reintentar: bash install/extras_color.sh)"

echo ""
echo "✅ Instalación completa. Ejecuta ./iniciar.sh"
