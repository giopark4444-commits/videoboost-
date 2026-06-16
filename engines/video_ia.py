"""Aplica un modelo de IA de restauración **fotograma a fotograma** a un video,
como ajuste de imagen pesado (NVIDIA en la práctica). Extrae los frames, los
procesa TODOS en una sola carga del modelo (no recarga por frame) y reensambla a
los fps originales.

Modelos disponibles:
- "ruido"      → Restormer (Real_Denoising)
- "desenfoque" → Restormer (Motion_Deblurring)
- "poca_luz"   → Retinexformer

Restormer y Retinexformer procesan una CARPETA entera por pasada (ver sus
`procesar_carpeta`), por eso son viables para video. Es lento y pensado para la
RTX 4080; en Mac (CPU) sería muy lento.
"""

import shutil
import tempfile
from pathlib import Path

from engines import SALIDAS, correr
from engines import ffmpeg_utils as ff
from engines import restormer, retinexformer

MODELOS = ("ruido", "desenfoque", "poca_luz")


def disponible(modelo: str) -> bool:
    if modelo in ("ruido", "desenfoque"):
        return restormer.disponible()
    if modelo == "poca_luz":
        return retinexformer.disponible()
    return False


def mejorar(video, modelo="ruido"):
    """Generador: cede log y DEVUELVE la ruta del video procesado por IA."""
    video = Path(video)
    if modelo not in MODELOS:
        raise RuntimeError(f"Modelo de IA desconocido: {modelo!r}. Usa {MODELOS}.")
    if not disponible(modelo):
        falta = "Restormer" if modelo in ("ruido", "desenfoque") else "Retinexformer"
        raise RuntimeError(
            f"Para «Mejora IA · {modelo}» falta {falta}. Instálalo en la pestaña "
            f"Sistema (requiere NVIDIA en la práctica)."
        )

    fps = ff.info_video(video).get("fps") or 30.0
    tmp = Path(tempfile.mkdtemp(prefix="vb_videoia_"))
    in_dir, out_dir = tmp / "in", tmp / "out"
    in_dir.mkdir(), out_dir.mkdir()
    try:
        yield f"✨ Mejora IA por fotograma · {modelo}"
        yield "📊 Paso 1/3 · Extrayendo frames…"
        yield from correr(ff.cmd_extraer_frames(video, in_dir))
        n = len(list(in_dir.glob("*.png")))
        yield f"📊 Paso 2/3 · Procesando {n} frames con IA (una carga del modelo)…"

        if modelo == "ruido":
            yield from restormer.procesar_carpeta(in_dir, out_dir, "Real_Denoising")
            res_dir = out_dir / "Real_Denoising"
        elif modelo == "desenfoque":
            yield from restormer.procesar_carpeta(in_dir, out_dir, "Motion_Deblurring")
            res_dir = out_dir / "Motion_Deblurring"
        else:  # poca_luz
            yield from retinexformer.procesar_carpeta(in_dir, out_dir)
            res_dir = out_dir

        frames = sorted(p for p in res_dir.rglob("*")
                        if p.suffix.lower() in (".png", ".jpg", ".jpeg"))
        if not frames:
            raise RuntimeError("La IA no generó frames de salida.")
        # Renumeramos a una secuencia limpia para reensamblar sin sorpresas.
        seq = tmp / "seq"
        seq.mkdir()
        for i, p in enumerate(frames):
            shutil.copy(p, seq / f"f_{i:08d}.png")

        salida = SALIDAS / f"{video.stem}_ia_{modelo}.mp4"
        yield "📊 Paso 3/3 · Reensamblando video…"
        yield from correr(ff.cmd_reensamblar(seq, "f_%08d.png", f"{fps:.5f}",
                                             video, salida))
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
