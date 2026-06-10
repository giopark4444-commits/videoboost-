"""Helpers de FFmpeg: información del video, extracción y reensamblado de frames."""

import json
import shutil
import subprocess
from pathlib import Path

from engines import BIN


def _binario(nombre: str) -> str:
    """Busca ffmpeg/ffprobe en bin/ (Windows) o en el PATH del sistema."""
    local = list((BIN / "ffmpeg").rglob(f"{nombre}*")) if (BIN / "ffmpeg").exists() else []
    for p in local:
        if p.is_file() and p.stem == nombre:
            return str(p)
    en_path = shutil.which(nombre)
    if en_path:
        return en_path
    raise RuntimeError(
        f"No se encontró {nombre}. En Mac: `brew install ffmpeg`. "
        f"En Windows corre el instalador (lo descarga a bin/ffmpeg/)."
    )


def ffmpeg() -> str:
    return _binario("ffmpeg")


def ffprobe() -> str:
    return _binario("ffprobe")


def info_video(ruta) -> dict:
    """Ancho, alto, fps (fracción y float), nº de frames y si tiene audio."""
    out = subprocess.run(
        [ffprobe(), "-v", "error", "-select_streams", "v:0",
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
        [ffprobe(), "-v", "error", "-select_streams", "a", "-show_entries",
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
