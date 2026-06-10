"""Motores de filtrado de video: desentrelazado, reducción de ruido y estabilización.

Todos son wrappers de FFmpeg y no requieren GPU ni venv adicional.
"""

import subprocess
import tempfile
from pathlib import Path

from engines import SALIDAS, correr
from engines.ffmpeg_utils import ffmpeg, info_video


def _tiene_filtro(nombre: str) -> bool:
    """Comprueba si FFmpeg tiene el filtro `nombre` compilado."""
    try:
        r = subprocess.run(
            [ffmpeg(), "-filters"],
            capture_output=True, text=True, timeout=10,
        )
        return nombre in r.stdout
    except Exception:
        return False


# Cacheado al cargar el módulo para no repetir la llamada en cada render
VIDSTAB_OK: bool = _tiene_filtro("vidstabdetect")


def desentrelazar(entrada):
    """Desentrelaza el video usando yadif=mode=0.

    Generador: cede líneas de log; retorna la ruta del archivo de salida.
    """
    entrada = Path(entrada)
    salida = SALIDAS / (entrada.stem + "_desentrelazado.mp4")
    cmd = [
        ffmpeg(), "-y", "-i", str(entrada),
        "-vf", "yadif=mode=0",
        "-c:v", "libx264", "-crf", "17", "-preset", "medium",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        str(salida),
    ]
    yield f"▶ desentrelazar: {entrada.name} → {salida.name}"
    yield from correr(cmd)
    return str(salida)


def denoise(entrada, luma: float = 3.0, chroma: float = 2.0):
    """Reduce el ruido de video con hqdn3d.

    luma   — fuerza de reducción en luminancia (0–10)
    chroma — fuerza de reducción en crominancia (0–10)

    Generador: cede líneas de log; retorna la ruta del archivo de salida.
    """
    entrada = Path(entrada)
    salida = SALIDAS / (entrada.stem + "_denoise.mp4")
    filtro = f"hqdn3d={luma:.1f}:{chroma:.1f}:{luma:.1f}:{chroma:.1f}"
    cmd = [
        ffmpeg(), "-y", "-i", str(entrada),
        "-vf", filtro,
        "-c:v", "libx264", "-crf", "17", "-preset", "medium",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        str(salida),
    ]
    yield f"▶ denoise (luma={luma}, chroma={chroma}): {entrada.name} → {salida.name}"
    yield from correr(cmd)
    return str(salida)


def estabilizar(entrada, suavidad: int = 10, zoom: float = 0.3):
    """Estabiliza el video con vidstab (2 pasadas).

    suavidad — suavidad de la transformación (1–30, default 10)
    zoom     — zoom de entrada para ocultar bordes (0.0–1.0, default 0.3)

    Requiere que FFmpeg esté compilado con --enable-libvidstab.
    Generador: cede líneas de log; retorna la ruta del archivo de salida.
    """
    if not VIDSTAB_OK:
        raise RuntimeError(
            "Tu FFmpeg no incluye libvidstab. Instala un FFmpeg completo "
            "(p. ej. `brew install ffmpeg` en Mac o el build de BtbN en Windows) "
            "y vuelve a intentarlo."
        )
    entrada = Path(entrada)
    salida = SALIDAS / (entrada.stem + "_estabilizado.mp4")

    # Archivo temporal para los datos de análisis de movimiento
    with tempfile.NamedTemporaryFile(suffix=".trf", delete=False) as tf:
        trf = tf.name

    try:
        # Pasada 1: análisis de movimiento
        yield f"▶ estabilizar (pasada 1/2, suavidad={suavidad}, zoom={zoom:.2f})"
        cmd1 = [
            ffmpeg(), "-y", "-i", str(entrada),
            "-vf", f"vidstabdetect=stepsize=6:shakiness=10:accuracy=15:result={trf}",
            "-f", "null", "-",
        ]
        yield from correr(cmd1)

        # Pasada 2: aplicar la transformación
        yield "▶ estabilizar (pasada 2/2, aplicando transformación)"
        zoom_pct = int(zoom * 100)
        cmd2 = [
            ffmpeg(), "-y", "-i", str(entrada),
            "-vf", (f"vidstabtransform=input={trf}:"
                    f"smoothing={suavidad}:zoom={zoom_pct}:optzoom=1:interpol=bicubic"),
            "-c:v", "libx264", "-crf", "17", "-preset", "medium",
            "-pix_fmt", "yuv420p",
            "-c:a", "copy",
            str(salida),
        ]
        yield from correr(cmd2)
    finally:
        try:
            Path(trf).unlink(missing_ok=True)
        except Exception:
            pass

    return str(salida)
