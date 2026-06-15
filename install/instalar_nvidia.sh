#!/usr/bin/env bash
# VideoBoost · Instalador para Linux con GPU NVIDIA.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== VideoBoost · instalador para Linux + NVIDIA =="

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "❌ Falta ffmpeg. Instálalo con tu gestor de paquetes (ej.: sudo apt install ffmpeg)."
  exit 1
fi

# La app usa sintaxis de tipos de Python 3.10+ (p.ej. `dict | None`).
echo "🐍 Buscando Python 3.10+…"
PY=""
for c in python3.13 python3.12 python3.11 python3.10 python3; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info[:2] >= (3,10) else 1)' 2>/dev/null; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ]; then
  echo "❌ Necesitas Python 3.10 o superior. Instálalo con tu gestor de paquetes"
  echo "   (ej.: sudo apt install python3.12 python3.12-venv) y reintenta."
  exit 1
fi
echo "   Usando: $("$PY" --version 2>&1)"
echo "🐍 Creando entorno .venv…"
"$PY" -m venv .venv
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
