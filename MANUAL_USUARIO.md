# VideoBoost · Manual de inicio

Mejora videos e imágenes con IA, **100% en tu computadora**: tus archivos nunca
salen de tu máquina, sin suscripciones ni internet (salvo la instalación).

## Lo que necesitas

- **Windows** con tarjeta NVIDIA (8 GB+ de video recomendado), o **Mac** con chip M.
- **Python 3** instalado (solo una vez, 2 minutos): [python.org/downloads](https://www.python.org/downloads/)
  — en Windows, marca la casilla **"Add Python to PATH"** al instalar.
- Espacio en disco: 20–40 GB (los modelos de IA son grandes).

## Instalación (una sola vez)

1. Descomprime VideoBoost donde quieras.
2. Doble clic en **`VideoBoost.bat`** (Windows) o **`VideoBoost.command`** (Mac).
   - *Windows:* si aparece el aviso azul de SmartScreen → "Más información" → "Ejecutar de todas formas".
   - *Mac:* si dice "no se puede abrir" → clic derecho sobre el archivo → "Abrir".
3. La primera vez instala todo y **descarga los modelos de IA** (tarda un buen
   rato, son varios GB — déjalo trabajar tranquilo).
4. Al terminar, la app se abre sola en tu navegador.

## Activación

La primera vez que abras la app te pedirá tu **clave de licencia** (te llegó con
tu compra, empieza por `VB1-`). Pégala completa y pulsa **Activar**. Es una sola
vez y no necesita internet.

## Uso diario

Doble clic en `VideoBoost.bat` / `VideoBoost.command` → se abre en el navegador.

- **Pestaña Video:** sube tu video, elige motor (SeedVR2 es el recomendado para
  restaurar), pulsa *Mejorar video*. El progreso se ve en vivo.
- **Pestaña Imágenes:** igual, con comparador antes/después deslizable y botón
  de descarga.
- **Revelado de color:** hasta 3 looks de película (Portra, Velvia, Tri-X…) +
  ajustes profesionales (exposición, contraste, blancos, negros, viñeta…).
- **Grano de película:** el toque analógico final, con presets ajustables.
- Los resultados quedan también en la carpeta **`salidas/`**.

Flujo recomendado: **Restaurar → Revelado → Grano.**

## Si algo no va

- **"Falta Python"** → instálalo desde python.org y vuelve a abrir VideoBoost.
- **La primera mejora tarda mucho en empezar** → está descargando un modelo;
  solo pasa la primera vez con cada motor.
- **Memoria insuficiente en video** → baja la resolución objetivo o los
  "frames por lote".
- **Diagnóstico completo:** abre una terminal en la carpeta y corre
  `python check.py` — te dice qué está listo y qué falta, con el comando exacto.

*Para cerrar la app: cierra la ventana negra (terminal) que se abre con ella.*
