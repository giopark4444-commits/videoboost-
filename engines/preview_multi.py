"""Comparar varios looks (LUTs) sobre un mismo frame de un video.

Extrae un único frame del video en una posición relativa (0–1) y lo revela con
cada look elegido (hasta 3), para que la UI pueda mostrar "el mismo frame con 3
miradas distintas lado a lado". 100% CPU/FFmpeg, sin venv propio.

Reutiliza el patrón de `hacer_comparar_luts` en app.py: consume el generador de
`luts.etalonar(...)` y captura la ruta de salida vía `StopIteration.value`.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

from engines import ffmpeg_utils as ff
from engines import luts


def comparar_looks(base_video, pos, looks):
    """Extrae el frame en `pos` (0–1) de `base_video` y lo devuelve revelado con
    cada look. `looks` = lista de tuplas (lut_id, mezcla, etiqueta), hasta 3; los
    lut_id == "ninguno" o vacíos se omiten. Generador que cede (galeria, mensaje)
    para streaming, donde galeria = lista de (ruta_png, etiqueta) empezando por
    ("...", "Original" sin LUT). Limpia los temporales que no use."""
    if not base_video:
        yield [], "sin video"
        return

    pos = max(0.0, min(1.0, float(pos if pos is not None else 0.3)))

    # Si lo que llega ya es una imagen (tab Imágenes), la usamos directamente como
    # "frame"; si es un video, extraemos el frame en `pos` UNA sola vez.
    _IMG = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".gif")
    es_imagen = str(base_video).lower().endswith(_IMG)
    if es_imagen:
        frame = str(base_video)          # la imagen del usuario: NO se borra
    else:
        frame = ff.extraer_frame_preview(base_video, pos)  # temporal: sí se borra
    if not frame:
        yield [], "no se pudo extraer el frame"
        return

    tmp = Path(tempfile.mkdtemp(prefix="vb_multi_"))
    # Transcodificamos el frame extraído (un JPEG temporal) a PNG en la carpeta
    # temporal: así la galería es autocontenida y homogénea (todo PNG), y el
    # mismo PNG es el `origen` que pasamos a etalonar para revelar cada look.
    origen = tmp / "original.png"
    try:
        subprocess.run([ff.ffmpeg(), "-y", "-i", str(frame), str(origen)],
                       capture_output=True, timeout=30, check=True)
        origen = str(origen)
    except Exception:
        origen = frame  # si falla la conversión, usamos el JPEG temporal directamente
    finally:
        # Si convertimos bien, el JPEG temporal de la EXTRACCIÓN ya no hace falta.
        # (Nunca borramos `frame` cuando es la imagen original del usuario.)
        if origen != frame and not es_imagen:
            Path(frame).unlink(missing_ok=True)

    galeria = [(origen, "Original")]
    yield galeria, "comparando looks…"

    # Solo hasta 3 looks válidos; descartamos "ninguno"/vacíos.
    validos = [(lid, mez, etq) for lid, mez, etq in (looks or [])
               if lid and lid != "ninguno"][:3]

    for n, (lut_id, mezcla, etiqueta) in enumerate(validos, 1):
        try:
            gen = luts.etalonar(origen, es_video=False,
                                looks=[(lut_id, float(mezcla))])
            salida = None
            try:
                while True:
                    next(gen)
            except StopIteration as fin:
                salida = fin.value
            if salida:
                dest = tmp / f"look_{n}_{lut_id}.png"
                shutil.copy(salida, dest)
                galeria.append((str(dest), etiqueta))
        except Exception:
            # Si un look falla, lo saltamos sin tumbar toda la comparación.
            pass
        yield galeria, f"look {n}/{len(validos)}"

    yield galeria, "listo"
