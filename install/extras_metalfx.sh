#!/usr/bin/env bash
# PixelBooster · MetalFX Spatial — escalado de video NATIVO de Apple Silicon vía el
# CLI de dominio público (CC0) finnvoor/fx-upscale. Lo clonamos en vendor/ y lo
# compilamos con Swift. Solo Mac con chip Apple (MetalFX no existe en NVIDIA/Linux).
set -euo pipefail
cd "$(dirname "$0")/.."

if [ "$(uname -s)" != "Darwin" ] || [ "$(uname -m)" != "arm64" ]; then
  echo "❌ MetalFX requiere un Mac con chip Apple (M1/M2/M3/M4). No existe en NVIDIA/Linux."
  exit 1
fi

command -v swift >/dev/null 2>&1 || {
  echo "❌ Necesitas las herramientas de línea de comandos de Xcode (swift). Instala con: xcode-select --install"
  exit 1
}

DIR="vendor/fx-upscale"
echo "== MetalFX Spatial (fx-upscale) =="

if [ -d "$DIR/.git" ]; then
  echo "ℹ️ fx-upscale ya está clonado en $DIR (omito la clonación)."
else
  echo "⬇️ Clonando finnvoor/fx-upscale…"
  git clone --depth 1 https://github.com/finnvoor/fx-upscale.git "$DIR"
fi

echo "🔨 Compilando (swift build -c release)…"
( cd "$DIR" && swift build -c release )

BIN="$DIR/.build/release/fx-upscale"
[ -x "$BIN" ] || { echo "❌ La compilación no produjo el binario en $BIN"; exit 1; }

echo "✅ MetalFX listo. Binario: $BIN"
