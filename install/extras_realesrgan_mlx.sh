#!/usr/bin/env bash
# Instalador de Real-ESRGAN x4plus (MLX) — escalador GAN nativo de Apple Silicon.
# Reusa el venv .venv-mlx (el mismo de SeedVR2/mflux) y descarga los pesos del
# modelo themindstudio/RealESRGAN-x4plus-mlx (BSD-3, uso comercial OK).
# Solo macOS Apple Silicon (arm64).
set -euo pipefail

# Carpeta raíz del proyecto (este script vive en install/).
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$RAIZ/.venv-mlx"
DEST="$RAIZ/vendor/realesrgan-mlx"
PESOS="$DEST/realesrgan_x4plus.npz"
REPO="themindstudio/RealESRGAN-x4plus-mlx"

# --- 1. Comprobar plataforma ---------------------------------------------------
if [[ "$(uname -s)" != "Darwin" || "$(uname -m)" != "arm64" ]]; then
  echo "❌ Real-ESRGAN (MLX) solo corre en macOS Apple Silicon (arm64)." >&2
  exit 1
fi

# --- 2. Asegurar el venv .venv-mlx con las dependencias ------------------------
if [[ ! -x "$VENV/bin/python" ]]; then
  echo "🔧 Creando $VENV (python@3.12)…"
  PY312="$(command -v python3.12 || true)"
  if [[ -z "$PY312" ]]; then
    echo "❌ No se encontró python3.12. Instálalo (brew install python@3.12) y reintenta." >&2
    exit 1
  fi
  "$PY312" -m venv "$VENV"
fi

echo "📦 Asegurando dependencias MLX en .venv-mlx…"
"$VENV/bin/python" -m pip install --upgrade pip >/dev/null
"$VENV/bin/python" -m pip install --upgrade mlx pillow numpy huggingface_hub

# --- 3. Descargar los pesos del modelo ----------------------------------------
mkdir -p "$DEST"
if [[ -f "$PESOS" ]]; then
  echo "✓ Pesos ya presentes: $PESOS"
else
  echo "⬇️  Descargando pesos de $REPO …"
  "$VENV/bin/python" - "$REPO" "$PESOS" <<'PY'
import shutil, sys
from huggingface_hub import hf_hub_download
repo, dest = sys.argv[1], sys.argv[2]
ruta = hf_hub_download(repo, "realesrgan_x4plus.npz")
shutil.copy(ruta, dest)
print("✓ copiado a", dest)
PY
fi

# --- 4. Verificación rápida ----------------------------------------------------
echo "🔎 Verificando que la inferencia carga el modelo…"
"$VENV/bin/python" - "$DEST/infer.py" "$PESOS" <<'PY'
import sys, importlib.util
spec = importlib.util.spec_from_file_location("infer", sys.argv[1])
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.cargar_modelo(sys.argv[2])
print("✓ RRDBNet x4plus cargado correctamente en MLX")
PY

echo ""
echo "✅ Real-ESRGAN x4plus (MLX) listo."
echo "   Motor:     engines/realesrgan_mlx.py"
echo "   Pesos:     $PESOS"
echo "   Escala:    x4 (fija), determinista, nativo Apple Silicon."
