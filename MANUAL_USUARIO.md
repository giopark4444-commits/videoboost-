# VideoBoost · Manual de inicio

Mejora videos e imágenes con IA, **100% en tu computadora**: tus archivos nunca
salen de tu máquina, sin suscripciones ni internet (salvo la instalación).

## Lo que necesitas

- **Windows** con tarjeta NVIDIA (8 GB+ de video recomendado), o **Mac** con chip M.
- **Python 3** instalado (solo una vez, 2 minutos): [python.org/downloads](https://www.python.org/downloads/)
  — en Windows, marca la casilla **"Add Python to PATH"** al instalar.
- Espacio en disco: 20–40 GB (los modelos de IA son grandes).

## Instalación (una sola vez)

Hay **dos formas**, elige una:

**A) Rápida — solo lo esencial** (video + SeedVR2 + Vulkan):
1. Descomprime VideoBoost donde quieras.
2. Doble clic en **`VideoBoost.bat`** (Windows) o **`VideoBoost.command`** (Mac).
   La primera vez instala el núcleo y al terminar abre la app sola.

**B) Completa — TODOS los motores** (restauración de imagen, caras, color…):
1. Doble clic en **`INSTALAR_TODO.bat`** (Windows) o **`INSTALAR_TODO.command`** (Mac).
2. Instala la base y todos los motores compatibles con tu máquina, uno tras otro.
   Si alguno falla, avisa y sigue con los demás (terminas con todo lo que sí pudo).
3. Después arranca normal con `VideoBoost.bat` / `VideoBoost.command`.

En ambos casos:
- *Windows:* si aparece el aviso azul de SmartScreen → "Más información" → "Ejecutar de todas formas".
- *Mac:* si dice "no se puede abrir" → clic derecho sobre el archivo → "Abrir".
- **Descarga modelos de IA** (varios GB; la opción completa, decenas de GB) —
  déjalo trabajar tranquilo. Solo pasa una vez.

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
- **Pestaña Lote:** procesa muchos archivos seguidos con la misma configuración.
- **Pestaña Galería:** mira todos tus resultados y descárgalos sin salir de la app.
- Botón **Cancelar** para detener un proceso a medias, y elección de **formato de
  salida** (H.264/H.265/ProRes/WebM en video; PNG/JPEG/TIFF/WebP en imagen).
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
