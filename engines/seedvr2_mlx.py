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
# Mismas opciones de "lado corto" que ofrece el desplegable de la UI.
OPCIONES_RES = [720, 1080, 1440, 2160, 4320]


def disponible() -> bool:
    return CLI.exists()


def dims_salida(w, h, resolucion):
    """Dimensiones de salida tal como las calcula mflux (SeedVR2Util): el lado
    corto va a `resolucion` y el otro a escala, ambos redondeados ABAJO a número
    par. Es exactamente la fórmula que usa el modelo, así anticipamos el tamaño
    real y si activará el aviso de «múltiplos de 16»."""
    w, h = int(w), int(h)
    escala = int(resolucion) / min(w, h)
    nw = (int(w * escala) // 2) * 2
    nh = (int(h * escala) // 2) * 2
    return nw, nh


def cumple_16(w, h, resolucion):
    """True si la salida queda en múltiplos de 16 (sin el aviso de mflux).

    SeedVR2 *siempre* genera el vídeo (rellena a 16 y luego recorta), pero si las
    dimensiones no son múltiplo de 16 mflux imprime un aviso por cada frame que
    parece un error. Que cumplan da el resultado más limpio y la consola callada.
    """
    nw, nh = dims_salida(w, h, resolucion)
    return nw % 16 == 0 and nh % 16 == 0


def resoluciones_limpias(w, h, opciones=OPCIONES_RES):
    """De las opciones del desplegable, las que dan salida múltiplo de 16 para
    este aspect ratio concreto."""
    return [r for r in opciones if cumple_16(w, h, r)]


def _aviso_16(w, h, resolucion):
    """Mensaje pre-vuelo (una vez, antes del trabajo pesado): si la salida no será
    múltiplo de 16, avisa que mflux lo ajusta solo —NO es error— y sugiere las
    resoluciones que sí cumplen para este vídeo/imagen."""
    nw, nh = dims_salida(w, h, resolucion)
    if nw % 16 == 0 and nh % 16 == 0:
        return f"✅ Salida {nw}×{nh}: múltiplos de 16 (resultado limpio)."
    limpias = resoluciones_limpias(w, h)
    sug = ", ".join(f"{r}px" for r in limpias) if limpias else "—"
    return (
        f"ℹ️ Salida {nw}×{nh}: no es múltiplo de 16. SeedVR2 lo ajusta solo "
        f"(rellena y recorta): el resultado SÍ se genera, NO es un error aunque "
        f"veas repetido «Width and height should be multiples of 16». "
        f"Para el resultado más limpio en este caso usa lado corto: {sug}."
    )


def _correr_silencioso(cmd):
    """Igual que correr(), pero silencia el aviso de mflux sobre múltiplos de 16
    (se repite una vez por frame y parece un muro de errores). Ya lo explicamos
    una sola vez en el aviso pre-vuelo, así que aquí lo ocultamos."""
    for linea in correr(cmd):
        if "multiples of 16" in linea or "Rounding down" in linea:
            continue
        yield linea


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
        try:
            from PIL import Image
            iw, ih = Image.open(entrada).size
            yield _aviso_16(iw, ih, resolucion)
        except Exception:
            pass
        yield "ℹ️ La primera vez descarga los pesos de HuggingFace (varios GB)."
        yield from _correr_silencioso(cmd)
        return str(salida)

    # --- Video: frames → mflux (un solo proceso) → reensamblar con audio ---
    info = ff.info_video(entrada)
    yield f"📹 {info['ancho']}x{info['alto']} · {info['fps']:.2f} fps · {info['frames']} frames"
    yield _aviso_16(info["ancho"], info["alto"], resolucion)
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
        yield from _correr_silencioso(cmd)

        salida = SALIDAS / f"{entrada.stem}_seedvr2mlx_{resolucion}p.mp4"
        yield "🎞️ Reensamblando con el audio original…"
        fps_str = f"{info['fps_num']}/{info['fps_den']}"
        yield from correr(ff.cmd_reensamblar(dir_out, "frame_%08d.png", fps_str, entrada, salida))
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
