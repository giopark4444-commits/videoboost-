#!/usr/bin/env bash
# VideoBoost · doble clic para instalar TODO de una vez (Mac Apple Silicon).
# Hazle doble clic en el Finder. (Si macOS lo bloquea: clic derecho › Abrir.)
# Instala la base y todos los motores compatibles con tu Mac. Tarda un buen
# rato y baja varios GB; déjalo trabajando.
cd "$(dirname "$0")"
clear
bash install/instalar_todo.sh
echo ""
echo "Pulsa una tecla para cerrar esta ventana…"
read -n 1 -s
