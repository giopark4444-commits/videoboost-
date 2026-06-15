"""Motores ncnn-Vulkan: Real-ESRGAN, Real-CUGAN, waifu2x y RIFE.

Funcionan en cualquier GPU (NVIDIA desde la serie 10, AMD, Intel y Mac con
chips M vía MoltenVK). Pipeline: FFmpeg extrae frames → el motor escala/interpola
en GPU → FFmpeg reensambla con el audio original.
"""

import shutil
import tempfile
from pathlib import Path

from engines import BIN, SALIDAS, correr
from engines import ffmpeg_utils as ff


def _ejecutable(motor: str) -> Path:
    carpeta = BIN / motor
    candidatos = list(carpeta.rglob(f"{motor}-ncnn-vulkan.exe")) + \
                 list(carpeta.rglob(f"{motor}-ncnn-vulkan"))
    for c in candidatos:
        if c.is_file():
            return c
    raise RuntimeError(
        f"No se encontró el binario de {motor} en bin/{motor}/. "
        f"Corre el instalador: python install/descargar_vulkan.py"
    )


def _cmd_escalado(motor, exe, dir_in, dir_out, escala, ruido, tile):
    if motor == "realesrgan":
        # realesr-animevideov3 soporta 2x/3x/4x y es el modelo de video del proyecto.
        cmd = [exe, "-i", dir_in, "-o", dir_out, "-n", "realesr-animevideov3",
               "-s", escala, "-f", "png"]
    elif motor == "realcugan":
        cmd = [exe, "-i", dir_in, "-o", dir_out, "-s", escala, "-n", ruido]
    elif motor == "waifu2x":
        cmd = [exe, "-i", dir_in, "-o", dir_out, "-s", escala, "-n", max(ruido, 0)]
    else:
        raise ValueError(f"Motor desconocido: {motor}")
    if tile:
        cmd += ["-t", tile]
    return cmd


def mejorar_video(entrada, motor="realesrgan", escala=2, ruido=0, tile=0):
    """Generador: cede líneas de log y devuelve la ruta del video de salida."""
    entrada = Path(entrada)
    exe = _ejecutable(motor)
    info = ff.info_video(entrada)
    yield f"📹 {info['ancho']}x{info['alto']} · {info['fps']:.2f} fps · {info['frames']} frames"

    tmp = Path(tempfile.mkdtemp(prefix="videoboost_"))
    dir_in, dir_out = tmp / "in", tmp / "out"
    dir_in.mkdir(), dir_out.mkdir()
    try:
        yield "⏳ Extrayendo frames…"
        yield from correr(ff.cmd_extraer_frames(entrada, dir_in))

        yield f"🚀 Escalando x{escala} con {motor} (GPU/Vulkan)…"
        # cwd = carpeta del binario: los ncnn-vulkan buscan models/ relativo al
        # directorio de trabajo; si no lo encuentran, segfaultan (no dan error).
        yield from correr(_cmd_escalado(motor, exe, dir_in, dir_out, escala, ruido, tile),
                          cwd=exe.parent)

        salida = SALIDAS / f"{entrada.stem}_x{escala}_{motor}.mp4"
        yield "🎞️ Reensamblando con el audio original…"
        fps_str = f"{info['fps_num']}/{info['fps_den']}"
        yield from correr(ff.cmd_reensamblar(dir_out, "frame_%08d.png", fps_str, entrada, salida))
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def interpolar_video(entrada, mult=2):
    """RIFE: multiplica los fps (30→60/120). No cambia la resolución."""
    entrada = Path(entrada)
    exe = _ejecutable("rife")
    modelos = sorted((exe.parent).glob("rife-v4*"), reverse=True)
    if not modelos:
        raise RuntimeError("No se encontró el modelo rife-v4.x junto al binario de RIFE.")
    modelo = modelos[0]

    info = ff.info_video(entrada)
    total_salida = info["frames"] * mult
    yield f"📹 {info['fps']:.2f} fps → {info['fps'] * mult:.2f} fps ({total_salida} frames)"

    tmp = Path(tempfile.mkdtemp(prefix="videoboost_"))
    dir_in, dir_out = tmp / "in", tmp / "out"
    dir_in.mkdir(), dir_out.mkdir()
    try:
        yield "⏳ Extrayendo frames…"
        yield from correr(ff.cmd_extraer_frames(entrada, dir_in))

        yield f"🚀 Interpolando x{mult} con RIFE ({modelo.name})…"
        yield from correr([exe, "-i", dir_in, "-o", dir_out, "-m", modelo, "-n", total_salida],
                          cwd=exe.parent)

        salida = SALIDAS / f"{entrada.stem}_{int(round(info['fps'] * mult))}fps_rife.mp4"
        yield "🎞️ Reensamblando con el audio original…"
        fps_str = f"{info['fps_num'] * mult}/{info['fps_den']}"
        # RIFE nombra su salida como %08d.png (no conserva el prefijo "frame_").
        yield from correr(ff.cmd_reensamblar(dir_out, "%08d.png", fps_str, entrada, salida))
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def mejorar_imagen(entrada, escala=4):
    """Imagen suelta con Real-ESRGAN. x4 usa el modelo de fotos (x4plus)."""
    entrada = Path(entrada)
    exe = _ejecutable("realesrgan")
    salida = SALIDAS / f"{entrada.stem}_x{escala}_realesrgan.png"
    if escala == 4:
        cmd = [exe, "-i", entrada, "-o", salida, "-n", "realesrgan-x4plus", "-s", 4]
    else:
        cmd = [exe, "-i", entrada, "-o", salida, "-n", "realesr-animevideov3", "-s", escala]
    yield f"🚀 Escalando imagen x{escala} con Real-ESRGAN…"
    yield from correr(cmd, cwd=exe.parent)
    return str(salida)
