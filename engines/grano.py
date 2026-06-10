"""Grano de película analógico — emulación orgánica, NO ruido digital.

Técnica clásica de emulación de film: una "placa de grano" gris al 50% con
ruido **gaussiano** (no uniforme) generada a **baja resolución** y reescalada
con bicúbico — eso crea racimos suaves con estructura, como los haluros de
plata reales, en vez de píxeles sueltos. La placa se mezcla en modo
**overlay**, que aporta gratis la respuesta de luminancia del film auténtico:
el grano vive en los medios tonos y desaparece en negros y blancos puros.

100% FFmpeg (CPU): funciona igual en Mac, NVIDIA o cualquier máquina, para
video e imagen, sin venv propio. El grano es temporal en video (cambia cada
frame, nunca un patrón estático).

Presets inspirados en carretes icónicos (su carácter de grano, no su color):
finura tipo Portra/Ektar, clásico 35mm tipo Kodak Gold, alta sensibilidad
tipo Portra 800/Cinestill, Super 8 grueso, y blanco y negro de plata tipo
Tri-X/HP5. Todos los parámetros son ajustables a mano.
"""

from pathlib import Path

from engines import SALIDAS, correr
from engines import ffmpeg_utils as ff

# preset → (intensidad 0-1, tamaño 1-4, grano_color)
# El "tamaño" es el factor de reescalado de la placa: 1 = grano fino y apretado,
# 4 = racimos gruesos tipo Super 8. La intensidad es la opacidad del overlay.
PRESETS = {
    "fino":     (0.10, 1, True),   # película profesional fina (tipo Portra 160/Ektar)
    "clasico":  (0.18, 2, True),   # 35mm de consumo (tipo Kodak Gold/ColorPlus)
    "alta_iso": (0.30, 2, True),   # película rápida (tipo Portra 800/Cinestill 800T)
    "super8":   (0.45, 3, True),   # Super 8 / 8mm casero, grueso y vivo
    "bn_plata": (0.32, 2, False),  # B/N de plata (tipo Tri-X/HP5): grano mono marcado
}

_FUERZA_RUIDO = 28  # amplitud del ruido gaussiano de la placa (fija; la
                    # intensidad visible se controla con la opacidad del blend)


def _filtro(w, h, fps, intensidad, tamano, grano_color, es_video):
    """Arma el filter_complex: placa gris+ruido a baja resolución → overlay."""
    tamano = max(1, int(tamano))
    gw, gh = max(2, w // tamano), max(2, h // tamano)
    gw, gh = gw + gw % 2, gh + gh % 2  # pares, por los formatos yuv

    # Ruido gaussiano (sin flag 'u' = no uniforme). 't' lo regenera cada frame.
    if grano_color:
        ruido = f"noise=alls={_FUERZA_RUIDO}:allf=t"          # también en croma
    else:
        ruido = f"noise=c0s={_FUERZA_RUIDO}:c0f=t"            # solo luma (plata)

    placa_src = f"color=c=gray:s={gw}x{gh}" + (f":r={fps}" if es_video else "")
    placa = (
        f"{placa_src},format=yuv444p,{ruido},"
        f"scale={w}:{h}:flags=bicubic,format=yuv444p[gr]"
    )
    mezcla = (
        f"[0:v]format=yuv444p[base];"
        f"[base][gr]blend=all_mode=overlay:all_opacity={intensidad:.3f}:shortest=1,"
        f"format=yuv420p[v]"
    )
    return f"{placa};{mezcla}"


def aplicar(entrada, es_video, preset="clasico", intensidad=None, tamano=None,
            grano_color=None):
    """Generador: cede log y devuelve la ruta de salida con grano aplicado.

    Los parámetros explícitos (intensidad/tamano/grano_color) pisan al preset."""
    entrada = Path(entrada)
    p_int, p_tam, p_col = PRESETS.get(preset, PRESETS["clasico"])
    intensidad = p_int if intensidad is None else max(0.0, min(1.0, float(intensidad)))
    tamano = p_tam if tamano is None else int(tamano)
    grano_color = p_col if grano_color is None else bool(grano_color)

    if es_video:
        info = ff.info_video(entrada)
        w, h, fps = info["ancho"], info["alto"], f"{info['fps_num']}/{info['fps_den']}"
        salida = SALIDAS / f"{entrada.stem}_grano.mp4"
        extra = ["-map", "[v]", "-map", "0:a?", "-c:a", "copy",
                 "-c:v", "libx264", "-crf", "17", "-preset", "medium"]
    else:
        from PIL import Image

        with Image.open(entrada) as img:
            w, h = img.size
        fps = None
        salida = SALIDAS / f"{entrada.stem}_grano.png"
        extra = ["-map", "[v]", "-frames:v", "1", "-update", "1"]

    filtro = _filtro(w, h, fps, intensidad, tamano, grano_color, es_video)
    cmd = [ff.ffmpeg(), "-y", "-i", entrada, "-filter_complex", filtro, *extra, salida]

    yield (f"🎞️ Grano analógico · preset {preset} · intensidad {intensidad:.2f} · "
           f"tamaño {tamano} · {'color' if grano_color else 'plata (mono)'}")
    yield "Placa gaussiana orgánica en overlay — el grano respira en los medios tonos."
    yield from correr(cmd)
    return str(salida)
