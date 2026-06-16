#!/usr/bin/env bash
# VideoBoost · RestoreFormer++ (Apache-2.0) — restauración de CARAS, reemplazo
# comercial-limpio de CodeFormer. Funciona en NVIDIA (CUDA) y en Mac Apple
# Silicon (cae a CPU). Venv propio. Los pesos se auto-descargan de los releases
# de GitHub en el primer uso (no requiere Google Drive).
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

echo "== RestoreFormer++ (restauración de caras, Apache-2.0) =="
"$PY" -m venv .venv-restoreformerpp
source .venv-restoreformerpp/bin/activate
pip install --upgrade pip
pip install torch torchvision $TORCH_ARGS

mkdir -p vendor
if [ ! -d vendor/RestoreFormerPlusPlus ]; then
  git clone --depth 1 https://github.com/wzhouxiff/RestoreFormerPlusPlus.git vendor/RestoreFormerPlusPlus
fi

# Dependencias del repo (RF_requirements.txt: facexlib, basicsr, realesrgan,
# pytorch-lightning 1.0.8, omegaconf 2.0.6, etc.). numpy<2 por compatibilidad
# con basicsr/realesrgan antiguos.
pip install -r vendor/RestoreFormerPlusPlus/RF_requirements.txt "numpy<2"

# basicsr importa torchvision.transforms.functional_tensor (removido en
# torchvision nuevo). Parche idempotente: redirige el import roto si aplica.
BASICSR_DEG="$(python -c 'import basicsr, os; print(os.path.join(os.path.dirname(basicsr.__file__), "data", "degradations.py"))' 2>/dev/null || true)"
if [ -n "$BASICSR_DEG" ] && [ -f "$BASICSR_DEG" ]; then
  python - "$BASICSR_DEG" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
old = "from torchvision.transforms.functional_tensor import rgb_to_grayscale"
new = "from torchvision.transforms.functional import rgb_to_grayscale"
if old in s:
    open(p, "w", encoding="utf-8").write(s.replace(old, new))
    print("· parche basicsr functional_tensor aplicado")
PYEOF
fi

# Los pesos (RestoreFormer++.ckpt y, si hay CUDA, RealESRGAN_x2plus.pth) se
# descargan solos de los releases de GitHub al primer inferir; no hay que bajarlos
# a mano. Por eso marcamos .ok aquí (el código del repo ya está clonado).
touch .venv-restoreformerpp/.ok
deactivate
echo "✅ RestoreFormer++ listo. Los pesos se descargan de GitHub en el primer uso."
