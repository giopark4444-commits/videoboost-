"""SeedVR2 en MLX (vía mflux, MIT) — restauración/super-resolución por difusión
**nativa de Apple Silicon**. Es el mismo modelo "nivel Topaz" que SeedVR2, pero
corriendo en MLX (no PyTorch/MPS), así que en Mac es mucho más usable de
velocidad. Solo Apple Silicon.

Imagen: una pasada. Video: extrae frames con FFmpeg, los procesa TODOS en una
sola invocación (mflux carga el modelo una vez y recorre la carpeta) y reensambla
con el audio original. Ojo: el port MLX es **por frame** (sin consistencia
temporal nativa) → usamos un --seed fijo para reducir el parpadeo.

Vive en .venv-mlx (paquete `mflux`). Se instala con install/extras_mlx.sh.
"""

import shutil
import tempfile
from pathlib import Path

from engines import RAIZ, SALIDAS, correr
from engines import ffmpeg_utils as ff

CLI = RAIZ / ".venv-mlx" / "bin" / "mflux-upscale-seedvr2"
MODELOS = ["seedvr2-3b", "seedvr2-7b"]


def disponible() -> bool:
    return CLI.exists()


def _cmd_base(resolucion, softness, modelo, quantize):
    cmd = [str(CLI), "--resolution", int(resolucion), "--softness", float(softness),
           "--seed", 42]
    if modelo and modelo != "seedvr2-3b":   # 3B es el default del CLI; solo pasamos 7B
        cmd += ["--model", modelo]
    if quantize:                            # int8 MLX: ~mitad de RAM, calidad casi igual
        cmd += ["--quantize", int(quantize)]
    return cmd


def mejorar(entrada, es_video=False, resolucion=1080, softness=0.5,
            modelo="seedvr2-3b", quantize=8):
    """Generador: cede log y devuelve la ruta de salida (imagen o video)."""
    if not disponible():
        raise RuntimeError(
            "SeedVR2 (MLX) no está instalado. Corre install/extras_mlx.sh."
        )
    entrada = Path(entrada)

    if not es_video:
        salida = SALIDAS / f"{entrada.stem}_seedvr2mlx.png"
        cmd = _cmd_base(resolucion, softness, modelo, quantize) + [
            "--image-path", entrada, "--output", salida]
        yield f"🚀 SeedVR2 (MLX, Apple Silicon) · lado corto {resolucion}px"
        yield "ℹ️ La primera vez descarga los pesos de HuggingFace (varios GB)."
        yield from correr(cmd)
        return str(salida)

    # --- Video: frames → mflux (un solo proceso) → reensamblar con audio ---
    info = ff.info_video(entrada)
    yield f"📹 {info['ancho']}x{info['alto']} · {info['fps']:.2f} fps · {info['frames']} frames"
    tmp = Path(tempfile.mkdtemp(prefix="videoboost_sv2mlx_"))
    dir_in, dir_out = tmp / "in", tmp / "out"
    dir_in.mkdir(), dir_out.mkdir()
    try:
        yield "⏳ Extrayendo frames…"
        yield from correr(ff.cmd_extraer_frames(entrada, dir_in))  # frame_%08d.png

        yield f"🚀 SeedVR2 (MLX) · lado corto {resolucion}px · {modelo} (per-frame)"
        yield "ℹ️ El modelo se carga una vez para toda la carpeta. Primera vez: descarga pesos."
        # --image-path = carpeta (carga el modelo una vez y recorre los frames).
        # --output requiere plantilla {image_name} para no sobreescribir.
        cmd = _cmd_base(resolucion, softness, modelo, quantize) + [
            "--image-path", dir_in, "--output", str(dir_out / "{image_name}.png")]
        yield from correr(cmd)

        salida = SALIDAS / f"{entrada.stem}_seedvr2mlx_{resolucion}p.mp4"
        yield "🎞️ Reensamblando con el audio original…"
        fps_str = f"{info['fps_num']}/{info['fps_den']}"
        yield from correr(ff.cmd_reensamblar(dir_out, "frame_%08d.png", fps_str, entrada, salida))
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
