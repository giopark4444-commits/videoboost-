#!/usr/bin/env bash
# VideoBoost · DarkIR (MIT) — restauración all-in-one de poca luz (corrige luz +
# ruido + desenfoque a la vez) con un modelo ligero (3-13M params). Corre tanto
# en NVIDIA como en Mac (no es difusión). Venv propio.
set -euo pipefail
cd "$(dirname "$0")/.."

# Python 3.10+ (el repo se desarrolló con 3.10.12; preferir python@3.12).
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

echo "== DarkIR (poca luz all-in-one: luz+ruido+desenfoque) =="
"$PY" -m venv .venv-darkir
source .venv-darkir/bin/activate
pip install --upgrade pip
pip install torch torchvision $TORCH_ARGS
mkdir -p vendor
if [ ! -d vendor/DarkIR ]; then
  git clone --depth 1 https://github.com/cidautai/DarkIR.git vendor/DarkIR
fi
pip install -r vendor/DarkIR/requirements.txt "numpy<2"
pip install huggingface_hub

# Pesos: NO se auto-descargan en la inferencia. El config por defecto
# (options/inference/LOLBlur.yml) espera el modelo en models/DarkIR_64width.pt.
# Fuente oficial: HuggingFace Cidaut/DarkIR (o el OneDrive del repo). Intentamos
# bajarlo de HF; si falla, dejamos instrucciones y NO marcamos .ok.
mkdir -p vendor/DarkIR/models
PESO="vendor/DarkIR/models/DarkIR_64width.pt"

if [ ! -f "$PESO" ]; then
  echo "↓ Descargando pesos de DarkIR desde HuggingFace (Cidaut/DarkIR)…"
  "$PY" - <<'PYEOF' || true
import os, shutil, glob
try:
    from huggingface_hub import snapshot_download
    d = snapshot_download(repo_id="Cidaut/DarkIR")
    dest = os.path.join("vendor", "DarkIR", "models")
    os.makedirs(dest, exist_ok=True)
    pts = sorted(glob.glob(os.path.join(d, "**", "*.pt"), recursive=True))
    if not pts:
        print("⚠️  No se encontraron .pt en el repo de HF."); raise SystemExit
    # Copiamos todos los .pt y dejamos una copia con el nombre que pide el config.
    objetivo = os.path.join(dest, "DarkIR_64width.pt")
    elegido = None
    for p in pts:
        shutil.copy(p, os.path.join(dest, os.path.basename(p)))
        if "64width" in os.path.basename(p):
            elegido = p
    if elegido is None:
        elegido = pts[0]  # p.ej. DarkIR_384.pt: el peso LOL-Blur publicado
    if not os.path.exists(objetivo):
        shutil.copy(elegido, objetivo)
    print("✓ Peso colocado en", objetivo, "(origen:", os.path.basename(elegido) + ")")
except Exception as e:
    print("⚠️  No se pudo descargar de HuggingFace:", e)
PYEOF
fi

# Alternativa: OneDrive del repo (manual) si HF no funcionó. Si pasas la ruta de
# un .pt ya descargado en DARKIR_PESO, lo copiamos al nombre que pide el config.
if [ ! -f "$PESO" ] && [ -n "${DARKIR_PESO:-}" ] && [ -f "${DARKIR_PESO}" ]; then
  cp "${DARKIR_PESO}" "$PESO"
  echo "✓ Peso copiado desde DARKIR_PESO a $PESO"
fi

if [ -f "$PESO" ]; then
  touch .venv-darkir/.ok
  echo "✅ DarkIR listo (peso en $PESO)."
else
  echo "ℹ️  Falta el peso de DarkIR. Descárgalo del OneDrive/HF del README y déjalo en:"
  echo "    vendor/DarkIR/models/DarkIR_64width.pt"
  echo "    (o reejecuta con DARKIR_PESO='/ruta/al/DarkIR_*.pt' bash install/extras_darkir.sh)"
  echo "⚠️  No se marca .ok hasta que exista el peso."
fi
deactivate
