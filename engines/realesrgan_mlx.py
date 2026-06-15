"""Real-ESRGAN x4plus en MLX — escalador GAN **nativo de Apple Silicon**, rápido
y determinista. Es el clásico RRDBNet x4plus de Real-ESRGAN (BSD-3) portado a
MLX (no PyTorch/MPS), así que en Mac vuela: ~0.5s por imagen pequeña, sin
difusión ni pasos iterativos. Escala fija x4.

Complementa a SeedVR2 (difusión, "nivel Topaz", más lento): este es el tier
ligero/rápido cuando solo quieres más resolución y nitidez de forma reproducible.

Pesos: themindstudio/RealESRGAN-x4plus-mlx (un único realesrgan_x4plus.npz). El
repo NO trae script de inferencia, así que la arquitectura RRDBNet se reimplementa
en vendor/realesrgan-mlx/infer.py (verificada numéricamente contra el RRDBNet de
referencia: diferencia máxima ~0.002).

Imagen: una pasada. Video: extrae frames con FFmpeg, los procesa TODOS en una
sola invocación (el modelo se carga una vez y recorre la carpeta) y reensambla
con el audio original. Es por frame, pero al ser determinista (sin ruido) no
parpadea.

Vive en .venv-mlx (paquetes `mlx` + `pillow` + `huggingface_hub`). Se instala con
install/extras_realesrgan_mlx.sh.
"""

import shutil
import tempfile
from pathlib import Path

from engines import RAIZ, SALIDAS, VENDOR, correr
from engines import ffmpeg_utils as ff

PY = RAIZ / ".venv-mlx" / "bin" / "python"
INFER = VENDOR / "realesrgan-mlx" / "infer.py"
PESOS = VENDOR / "realesrgan-mlx" / "realesrgan_x4plus.npz"
ESCALA = 4  # el modelo es x4 fijo


def disponible() -> bool:
    return PY.exists() and INFER.exists() and PESOS.exists()


def mejorar(entrada, es_video=False, escala=4):
    """Generador: cede log y devuelve la ruta de salida (imagen o video).

    `escala` se acepta por uniformidad con los demás motores, pero el modelo es
    x4 fijo (se ignora cualquier otro valor).
    """
    if not disponible():
        raise RuntimeError(
            "Real-ESRGAN (MLX) no está instalado. Corre install/extras_realesrgan_mlx.sh."
        )
    entrada = Path(entrada)

    if not es_video:
        salida = SALIDAS / f"{entrada.stem}_realesrganmlx_x4.png"
        cmd = [str(PY), str(INFER), "--pesos", str(PESOS),
               "--salida", str(salida), str(entrada)]
        yield "🚀 Real-ESRGAN x4plus (MLX, Apple Silicon) · x4 · determinista"
        yield from correr(cmd)
        return str(salida)

    # --- Video: frames → infer.py (un solo proceso) → reensamblar con audio ---
    info = ff.info_video(entrada)
    yield f"📹 {info['ancho']}x{info['alto']} · {info['fps']:.2f} fps · {info['frames']} frames"
    tmp = Path(tempfile.mkdtemp(prefix="videoboost_resrmlx_"))
    dir_in, dir_out = tmp / "in", tmp / "out"
    dir_in.mkdir(), dir_out.mkdir()
    try:
        yield "⏳ Extrayendo frames…"
        yield from correr(ff.cmd_extraer_frames(entrada, dir_in))  # frame_%08d.png

        yield "🚀 Real-ESRGAN x4plus (MLX) · x4 · per-frame (modelo cargado una vez)"
        # salida = carpeta → infer.py escribe <stem>.png por cada frame.
        frames = sorted(dir_in.glob("frame_*.png"))
        cmd = [str(PY), str(INFER), "--pesos", str(PESOS),
               "--salida", str(dir_out)] + [str(f) for f in frames]
        yield from correr(cmd)

        salida = SALIDAS / f"{entrada.stem}_realesrganmlx_x4.mp4"
        yield "🎞️ Reensamblando con el audio original…"
        fps_str = f"{info['fps_num']}/{info['fps_den']}"
        yield from correr(ff.cmd_reensamblar(dir_out, "frame_%08d.png", fps_str, entrada, salida))
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
