"""Helpers de FFmpeg: información del video, extracción y reensamblado de frames.

ffmpeg se busca en bin/ (Windows), en el PATH y, como último recurso, en el
binario que trae el paquete pip `imageio-ffmpeg` — así el instalador no necesita
Homebrew ni descargas manuales: `pip install` ya deja ffmpeg listo en cualquier
sistema. ffprobe es opcional: si no está, info_video deduce los datos del propio
ffmpeg.
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

from engines import BIN


def _en_bin(nombre: str):
    local = list((BIN / "ffmpeg").rglob(f"{nombre}*")) if (BIN / "ffmpeg").exists() else []
    for p in local:
        if p.is_file() and p.stem == nombre:
            return str(p)
    return None


def _ffmpeg_imageio():
    """Binario ffmpeg que trae el paquete pip imageio-ffmpeg, o None."""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def ffmpeg() -> str:
    return _en_bin("ffmpeg") or shutil.which("ffmpeg") or _ffmpeg_imageio() or _falta("ffmpeg")


def ffprobe():
    """Ruta a ffprobe si existe (bin/ o PATH), o None — es opcional."""
    return _en_bin("ffprobe") or shutil.which("ffprobe")


def _falta(nombre):
    raise RuntimeError(
        f"No se encontró {nombre}. Debería venir con `pip install imageio-ffmpeg` "
        f"(está en requirements.txt). En Windows el instalador también lo deja en bin/ffmpeg/."
    )


def _info_via_ffmpeg(ruta) -> dict:
    """Deduce ancho/alto/fps/duración/audio leyendo la salida de `ffmpeg -i`.

    Fallback para cuando no hay ffprobe (p. ej. ffmpeg de imageio-ffmpeg)."""
    out = subprocess.run([ffmpeg(), "-hide_banner", "-i", str(ruta)],
                         capture_output=True, text=True).stderr
    m = re.search(r"Stream #\d+:\d+.*?: Video:.*?(\d{2,5})x(\d{2,5})", out, re.S)
    if not m:
        raise RuntimeError("No se pudo leer la resolución del video.")
    w, h = int(m.group(1)), int(m.group(2))
    mfps = re.search(r"([\d.]+)\s*fps", out)
    fps = float(mfps.group(1)) if mfps else 25.0
    md = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", out)
    dur = (int(md.group(1)) * 3600 + int(md.group(2)) * 60 + float(md.group(3))) if md else 0.0
    audio = bool(re.search(r"Stream #\d+:\d+.*?: Audio:", out))
    # fps como fracción aproximada (suficiente para -framerate)
    num, den = (round(fps * 1000), 1000) if abs(fps - round(fps)) > 1e-3 else (int(round(fps)), 1)
    return {"ancho": w, "alto": h, "fps": fps, "fps_num": num, "fps_den": den,
            "frames": int(dur * fps), "duracion": dur, "audio": audio}


def info_video(ruta) -> dict:
    """Ancho, alto, fps (fracción y float), nº de frames y si tiene audio.

    Usa ffprobe si está disponible; si no, deduce los datos del propio ffmpeg."""
    fp = ffprobe()
    if fp is None:
        return _info_via_ffmpeg(ruta)
    out = subprocess.run(
        [fp, "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,r_frame_rate,nb_frames",
         "-show_entries", "format=duration", "-of", "json", str(ruta)],
        capture_output=True, text=True, check=True,
    )
    datos = json.loads(out.stdout)
    stream = datos["streams"][0]
    num, den = (stream["r_frame_rate"].split("/") + ["1"])[:2]
    num, den = int(num), int(den or 1)
    fps = num / den
    duracion = float(datos.get("format", {}).get("duration", 0) or 0)
    nb = stream.get("nb_frames")
    frames = int(nb) if nb and nb.isdigit() else int(duracion * fps)

    audio = subprocess.run(
        [fp, "-v", "error", "-select_streams", "a", "-show_entries",
         "stream=index", "-of", "csv=p=0", str(ruta)],
        capture_output=True, text=True,
    ).stdout.strip() != ""

    return {
        "ancho": stream["width"], "alto": stream["height"],
        "fps": fps, "fps_num": num, "fps_den": den,
        "frames": frames, "duracion": duracion, "audio": audio,
    }


def cmd_extraer_frames(video, dir_destino: Path):
    return [ffmpeg(), "-y", "-i", str(video), str(dir_destino / "frame_%08d.png")]


def cmd_reensamblar(dir_frames: Path, patron: str, fps_str: str, video_origen, salida):
    """Reconstruye el video desde frames y copia el audio del original (si existe)."""
    return [
        ffmpeg(), "-y",
        "-framerate", fps_str,
        "-i", str(dir_frames / patron),
        "-i", str(video_origen),
        "-map", "0:v:0", "-map", "1:a?",
        "-c:v", "libx264", "-crf", "17", "-preset", "medium",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", str(salida),
    ]
