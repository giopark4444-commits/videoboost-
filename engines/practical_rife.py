"""Practical-RIFE (hzwer, MIT) — interpolación de frames moderna (RIFE 4.x).

Inventa fotogramas intermedios para SLOW-MOTION (o más fps). Es un salto de calidad
sobre el RIFE 4.6 (ncnn/Vulkan) que ya trae la app. PyTorch: corre en NVIDIA (CUDA)
y en Mac (MPS).

CLI: `python3 inference_video.py --multi=N --video=<in> [--fps=F] [--scale=S]`. El
modelo (flownet.pkl + *.py) vive en `train_log/`. La salida es un mp4
`{stem}_{N}X_{fps}fps.mp4` junto al video de entrada.

NO PROBADO a fondo desde aquí: verificar en la 4080 / Mac (MPS).
"""

import shutil
import tempfile
from pathlib import Path

from engines import SALIDAS, VENDOR, correr, python_venv
from engines import ffmpeg_utils as ff

PRIFE_DIR = VENDOR / "Practical-RIFE"


def disponible() -> bool:
    return ((PRIFE_DIR / "inference_video.py").exists()
            and (PRIFE_DIR / "train_log" / "flownet.pkl").exists())


def interpolar(video, mult=2):
    """Generador: cede log y devuelve la ruta del video interpolado (slow-mo).

    `mult` = cuántos fotogramas por cada uno (2/4/8…). Para conseguir cámara lenta
    real, fijamos los fps de salida a los del original: así los fotogramas extra
    estiran la duración (mult× más larga) en vez de solo suavizar.
    """
    if not disponible():
        raise RuntimeError(
            "Practical-RIFE no está instalado. Corre install/extras_practical_rife.sh."
        )
    video = Path(video)
    py = python_venv(".venv-prife", "install/extras_practical_rife.sh")
    mult = max(2, int(mult))

    # Copiamos el video a una carpeta temporal para que la salida (que el script
    # deja junto al de entrada) quede en un sitio predecible.
    tmp = Path(tempfile.mkdtemp(prefix="videoboost_prife_"))
    entrada = tmp / ("in" + video.suffix.lower())
    shutil.copy(video, entrada)

    fps_orig = ff.info_video(video).get("fps") or 0
    cmd = [py, "inference_video.py", f"--multi={mult}", f"--video={entrada}"]
    if fps_orig:                       # cámara lenta: mantener fps → duración ×mult
        # OJO: inference_video.py declara --fps como type=int, así que un valor
        # flotante ("24.00000") lo rechaza con "invalid int value". Redondeamos al
        # entero más cercano (24/30/60…); para slow-mo basta con fijar los fps de
        # salida ≈ a los del original para que los frames extra estiren la duración.
        cmd.append(f"--fps={round(fps_orig)}")

    try:
        yield f"🚀 Practical-RIFE · x{mult} (slow-mo / fotogramas intermedios)"
        yield "ℹ️ Primera vez: carga el modelo RIFE. En Mac usa MPS (más lento que NVIDIA)."
        yield from correr(cmd, cwd=PRIFE_DIR)
        nuevos = sorted(tmp.glob("*X*fps.mp4")) or [p for p in tmp.glob("*.mp4")
                                                    if p != entrada]
        if not nuevos:
            raise RuntimeError("Practical-RIFE terminó pero no se encontró el video de salida.")
        salida = SALIDAS / f"{video.stem}_rife_x{mult}.mp4"
        shutil.move(str(nuevos[0]), salida)
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
