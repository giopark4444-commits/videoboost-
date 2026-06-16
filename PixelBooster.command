#!/usr/bin/env bash
# PixelBooster · lanzador de doble clic para Mac (Apple Silicon).
# Primera vez: instala todo y descarga los modelos. Después: solo abre la app.
# Hazle doble clic en el Finder. (Si macOS lo bloquea la 1ª vez: clic derecho › Abrir.)

cd "$(dirname "$0")"
clear
echo "════════════════════════════════════════════"
echo "   PixelBooster"
echo "════════════════════════════════════════════"
echo ""

fallo() {
  echo ""
  echo "⚠️  Algo se detuvo. Lee el mensaje de arriba."
  echo "Pulsa una tecla para cerrar esta ventana…"
  read -n 1 -s
  exit 1
}

# 1. ¿Está Python 3?
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ No encuentro Python 3 (solo hace falta instalarlo una vez)."
  echo "   Se abrirá la página de descarga. Instálalo y vuelve a abrir PixelBooster."
  open "https://www.python.org/downloads/macos/" 2>/dev/null || true
  fallo
fi

# 2. Primera vez: instalación automática
if [ ! -d .venv ]; then
  echo "Es la primera vez. Voy a instalar PixelBooster y descargar los modelos."
  echo "Puede tardar un buen rato (varios GB). Déjalo trabajando con calma."
  echo ""
  bash install/instalar_mac.sh || fallo
  echo ""
  echo "✅ Instalación lista."
  echo ""
fi

# 3. Arrancar (app.py abre el navegador solo)
echo "Abriendo PixelBooster en tu navegador…"
echo "Para cerrar la app: cierra esta ventana."
echo ""
source .venv/bin/activate
python app.py || fallo
