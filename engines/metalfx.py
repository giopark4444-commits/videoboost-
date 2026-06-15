"""MetalFX Spatial — escalado de video **nativo de Apple Silicon**, rápido y en
tiempo casi real. Usa la API MetalFX Spatial de Apple (la misma tecnología de
escalado espacial de los juegos) vía el CLI de dominio público (CC0)
finnvoor/fx-upscale, que vendorizamos y compilamos con Swift.

No es IA generativa: es un escalador espacial consciente de bordes (edge-aware),
no inventa detalle como SeedVR2/Real-ESRGAN; a cambio es muchísimo más rápido y
trabaja sobre el archivo de video directamente (sin extraer frames). Solo Mac con
chip Apple (M1/M2/M3/M4) y macOS 13+.

El binario fx-upscale escribe un «<nombre> Upscaled.<ext>» junto al de entrada y
no conserva el audio; por eso lo dirigimos a un temporal y reensamblamos con
FFmpeg a h264 yuv420p (reproducible en el navegador) trayendo el audio original.

Se instala con install/extras_metalfx.sh (clona y compila fx-upscale en vendor/).
"""

import shutil
import tempfile
from pathlib import Path

from engines import RAIZ, SALIDAS, correr
from engines import ffmpeg_utils as ff

BINARIO = RAIZ / "vendor" / "fx-upscale" / ".build" / "release" / "fx-upscale"


def disponible() -> bool:
    return BINARIO.exists()


def mejorar(entrada, escala=2):
    """Generador: cede líneas de log y devuelve la ruta del video de salida.

    Escala el video `escala`× (objetivo = ancho×escala, alto×escala) con MetalFX
    Spatial y reensambla a h264 mp4 con el audio original.
    """
    if not disponible():
        raise RuntimeError(
            "MetalFX no está instalado. Corre install/extras_metalfx.sh."
        )
    entrada = Path(entrada)
    escala = int(escala)

    info = ff.info_video(entrada)
    ancho, alto = int(info["ancho"]), int(info["alto"])
    # MetalFX exige dimensiones pares para el códec; redondeamos por seguridad.
    ancho_obj = (ancho * escala) // 2 * 2
    alto_obj = (alto * escala) // 2 * 2
    yield f"📹 {ancho}x{alto} · {info['fps']:.2f} fps · {info['frames']} frames"

    tmp = Path(tempfile.mkdtemp(prefix="videoboost_metalfx_"))
    try:
        # fx-upscale escribe «<stem> Upscaled.<ext>» junto al archivo de entrada;
        # copiamos la entrada al temporal con extensión .mp4 para controlar dónde
        # cae la salida y forzamos códec h264 (reproducible en el navegador).
        src = tmp / "in.mp4"
        shutil.copy(entrada, src)
        crudo = tmp / "in Upscaled.mp4"

        yield f"🚀 MetalFX Spatial (Apple Silicon) · escalando x{escala} → {ancho_obj}x{alto_obj}…"
        yield "ℹ️ Escalador espacial nativo (edge-aware, no IA generativa): rápido, sin inventar detalle."
        yield from correr([BINARIO, str(src),
                           "--width", ancho_obj, "--height", alto_obj,
                           "--codec", "h264"])

        salida = SALIDAS / f"{entrada.stem}_metalfx_x{escala}.mp4"
        yield "🎞️ Reensamblando a h264 con el audio original…"
        # Re-encode a h264 yuv420p + audio del original (fx-upscale no trae audio).
        yield from correr([
            ff.ffmpeg(), "-y",
            "-i", str(crudo),
            "-i", str(entrada),
            "-map", "0:v:0", "-map", "1:a?",
            "-c:v", "libx264", "-crf", "17", "-preset", "medium",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", str(salida),
        ])
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
