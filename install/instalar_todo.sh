#!/usr/bin/env bash
# VideoBoost · Instalador ÚNICO todo-en-uno (Mac Apple Silicon o Linux NVIDIA).
# Instala la base (app + SeedVR2 + Vulkan) y TODOS los motores que tu máquina
# puede usar, uno tras otro. Si un motor falla, avisa y sigue con los demás:
# terminas con todo lo que sí se pudo instalar, nunca a medias por un solo error.
#
# Detecta la plataforma solo: NVIDIA en Linux → todos los motores; Mac con chip
# M → los compatibles (SeedVR2, Vulkan, CodeFormer, DDColor). Los motores que
# requieren CUDA se omiten en Mac automáticamente.
set -uo pipefail
cd "$(dirname "$0")/.."

echo "════════════════════════════════════════════════════"
echo "   VideoBoost · instalación completa (todo-en-uno)"
echo "════════════════════════════════════════════════════"
echo ""

# --- Detección de plataforma ---
ES_MAC=0
TIENE_NVIDIA=0
[ "$(uname -s)" = "Darwin" ] && ES_MAC=1
command -v nvidia-smi >/dev/null 2>&1 && TIENE_NVIDIA=1

if [ "$ES_MAC" = "1" ]; then
  echo "🖥️  Detectado: Mac (Apple Silicon). Motores: SeedVR2 (MPS), Vulkan,"
  echo "    CodeFormer (caras) y DDColor (color)."
  BASE="install/instalar_mac.sh"
  EXTRAS=("install/extras_caras.sh" "install/extras_color.sh")
elif [ "$TIENE_NVIDIA" = "1" ]; then
  echo "🖥️  Detectado: Linux con GPU NVIDIA. Se instalarán TODOS los motores."
  BASE="install/instalar_nvidia.sh"
  EXTRAS=("install/extras_faithdiff.sh" "install/extras_instantir.sh"
          "install/extras_flashvsr.sh" "install/extras_caras.sh"
          "install/extras_color.sh")
else
  echo "🖥️  Sin NVIDIA detectada: instalación compatible (Vulkan + caras + color)."
  echo "    Los motores que requieren CUDA se omitirán."
  BASE="install/instalar_nvidia.sh"   # crea la base; SeedVR2 quedará sin GPU
  EXTRAS=("install/extras_caras.sh" "install/extras_color.sh")
fi
echo ""

# --- 1. Base (obligatoria: si falla, no tiene sentido seguir) ---
echo "▶ [1/$(( ${#EXTRAS[@]} + 1 ))] Base (app + SeedVR2 + Vulkan)…"
if ! bash "$BASE"; then
  echo "❌ La instalación base falló. Lee los mensajes de arriba; sin la base no"
  echo "   se puede continuar. Corrige el problema y vuelve a ejecutar este script."
  exit 1
fi
echo "✅ Base lista."
echo ""

# --- 2. Motores opcionales (tolerante a fallos) ---
FALLIDOS=()
i=2
for extra in "${EXTRAS[@]}"; do
  total=$(( ${#EXTRAS[@]} + 1 ))
  nombre="$(basename "$extra")"
  echo "▶ [$i/$total] $nombre …"
  if bash "$extra"; then
    echo "✅ $nombre listo."
  else
    echo "⚠️  $nombre no se completó — sigo con los demás motores."
    FALLIDOS+=("$nombre")
  fi
  echo ""
  i=$(( i + 1 ))
done

# --- Resumen ---
echo "════════════════════════════════════════════════════"
if [ "${#FALLIDOS[@]}" = "0" ]; then
  echo "✅ Todo instalado correctamente."
else
  echo "✅ Instalación terminada, con avisos."
  echo "   No se completaron: ${FALLIDOS[*]}"
  echo "   Puedes reintentar cada uno con su script en install/ cuando quieras."
fi
echo "   Arranca la app con doble clic en VideoBoost (o ./iniciar.sh)."
echo "════════════════════════════════════════════════════"
