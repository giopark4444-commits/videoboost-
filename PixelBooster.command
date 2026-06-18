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

# 3. Arrancar en un puerto FIJO propio de PixelBooster (7870+).
#    Sin esto, Gradio auto-escanea desde 7860 y choca con otras apps tuyas (Image
#    Studio en 7860, audio-layers en 7861…), así que PixelBooster caía cada vez en
#    un puerto distinto y la pestaña/marcador guardado apuntaba a otra app → "no
#    abre bien". Fijamos 7870; si estuviera ocupado tomamos el primer libre hacia
#    arriba (así nunca falla al enlazar).
source .venv/bin/activate
export GRADIO_SERVER_PORT="$(python - <<'PORT'
import socket
for p in range(7870, 7890):
    with socket.socket() as s:
        if s.connect_ex(("127.0.0.1", p)) != 0:   # connect falla => puerto libre
            print(p); break
else:
    print(7870)
PORT
)"
echo "Abriendo PixelBooster en tu navegador…  →  http://127.0.0.1:$GRADIO_SERVER_PORT"
echo "Para cerrar la app: cierra esta ventana."
echo ""
python app.py || fallo
