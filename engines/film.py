"""FILM (Google Research, Apache-2.0) — interpolación de frames para MOVIMIENTO
GRANDE: inventa fotogramas intermedios fotorrealistas, ideal para slow-motion
dramático donde hay desplazamientos amplios entre fotogramas.

TensorFlow 2 → en la práctica solo NVIDIA (4080); en Mac es impráctico.

CLI: `python3 -m eval.interpolator_cli --pattern "<dir_frames>" --model_path
<pesos>/film_net/Style/saved_model --times_to_interpolate K --output_video`.
K es recursivo: inserta 2^K - 1 fotogramas entre cada par (x2→K=1, x4→K=2, x8→K=3).

NO PROBADO desde aquí (sin CUDA): verificar flags, pesos y fps en la 4080.
"""

import math
import shutil
import tempfile
from pathlib import Path

from engines import SALIDAS, VENDOR, MODELS, correr, python_venv
from engines import ffmpeg_utils as ff

FILM_DIR = VENDOR / "frame-interpolation"
FILM_WEIGHTS = MODELS / "FILM" / "film_net" / "Style" / "saved_model"


def disponible() -> bool:
    return ((FILM_DIR / "eval" / "interpolator_cli.py").exists()
            and FILM_WEIGHTS.exists())


def interpolar(video, mult=2):
    """Generador: cede log y devuelve la ruta del video interpolado (slow-mo).

    `mult` ∈ {2,4,8}. Se extraen los frames del video, FILM los interpola y se
    reensambla a los fps ORIGINALES → cámara lenta real (duración ×mult).
    """
    if not disponible():
        raise RuntimeError("FILM no está instalado. Corre install/extras_film.sh.")
    video = Path(video)
    py = python_venv(".venv-film", "install/extras_film.sh")
    mult = max(2, int(mult))
    k = max(1, round(math.log2(mult)))        # x2→1, x4→2, x8→3
    factor = 2 ** k
    fps_orig = ff.info_video(video).get("fps") or 30.0

    tmp = Path(tempfile.mkdtemp(prefix="videoboost_film_"))
    seq = tmp / "seq"                          # carpeta con los frames de entrada
    seq.mkdir(parents=True)
    out_dir = tmp / "out"
    out_dir.mkdir()

    cmd = [
        py, "-m", "eval.interpolator_cli",
        "--pattern", str(seq),
        "--model_path", str(FILM_WEIGHTS),
        "--times_to_interpolate", int(k),
        "--output_video",
    ]
    try:
        yield f"🚀 FILM · x{factor} (movimiento grande / slow-mo fotorrealista)"
        yield "📊 Paso 1/3 · Extrayendo frames…"
        yield from correr(ff.cmd_extraer_frames(video, seq))
        yield "📊 Paso 2/3 · Interpolando con FILM (la primera vez carga TensorFlow)…"
        yield from correr(cmd, cwd=FILM_DIR)
        # FILM deja interpolated.mp4 y/o interpolated_frames/ dentro de `seq`.
        frames_int = sorted((seq / "interpolated_frames").glob("*.png"))
        if frames_int:
            yield "📊 Paso 3/3 · Reensamblando a los fps originales (cámara lenta)…"
            salida = SALIDAS / f"{video.stem}_film_x{factor}.mp4"
            yield from correr(ff.cmd_reensamblar(
                seq / "interpolated_frames", "*.png", f"{fps_orig:.5f}",
                video, salida))
            return str(salida)
        # Fallback: usar el mp4 que genera FILM directamente.
        vids = list(seq.rglob("*.mp4"))
        if not vids:
            raise RuntimeError("FILM terminó pero no generó frames ni video interpolado.")
        salida = SALIDAS / f"{video.stem}_film_x{factor}.mp4"
        shutil.copy(vids[0], salida)
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
