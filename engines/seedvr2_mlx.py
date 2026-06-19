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


# Velocidad medida en M1 Max: 3B int8, salida ~1280×720 ≈ 12 s/frame en régimen
# (con el servidor abierto, condiciones reales de Gio). Es el suelo: la difusión
# tiene pasos fijos y mflux no expone --steps. Escala con los píxeles de salida y
# con el modelo (7B ~1.8× más lento). Mejor sobreestimar que subestimar el ETA.
SEG_POR_FRAME_720 = 12.0


def _seg_por_frame(w, h, resolucion, modelo):
    nw, nh = dims_salida(w, h, resolucion)
    factor = max((nw * nh) / (1280 * 720), 0.25)
    s = SEG_POR_FRAME_720 * factor
    if modelo and "7b" in str(modelo).lower():
        s *= 1.8
    return s


def _fmt_dur(seg):
    seg = int(round(seg))
    h, m, s = seg // 3600, (seg % 3600) // 60, seg % 60
    if h:
        return f"~{h} h {m:02d} min"
    if m:
        return f"~{m} min {s:02d} s"
    return f"~{s} s"


def _aviso_tiempo_video(w, h, resolucion, n_frames, modelo):
    """Aviso pre-vuelo (una vez): cuánto tardará y qué hacer si es mucho. SeedVR2
    es difusión por frame: en Mac va a varios segundos por frame, así que un vídeo
    de pocos segundos puede tardar minutos u horas. NO está colgado: es lento por
    diseño. Para escalar rápido están MetalFX y Real-ESRGAN."""
    spf = _seg_por_frame(w, h, resolucion, modelo)
    if n_frames:
        cuerpo = f"{n_frames} frames × ~{spf:.0f} s/frame ≈ {_fmt_dur(spf * n_frames)} en este Mac"
    else:
        cuerpo = f"~{spf:.0f} s por frame en este Mac"
    return (
        "⏳ SeedVR2 IA procesa FRAME a FRAME: " + cuerpo + ". NO está colgado, solo "
        "es lento por diseño (la difusión tiene pasos fijos, no hay forma de "
        "acelerarla salvo bajar la resolución). Para escalar vídeo largo en "
        "segundos usa MetalFX o Real-ESRGAN; deja SeedVR2-MLX para clips cortos "
        "donde quieras la máxima calidad IA. Truco: baja el «lado corto» (p. ej. "
        "720) para ir bastante más rápido."
    )


def _correr_mlx_video(cmd, dir_out, total):
    """Como _correr_silencioso pero, además, da progreso REAL: cuenta los PNG que
    mflux va escribiendo en dir_out y emite `frame=N/total` para que la barra
    global avance de verdad.

    Por qué: la barra tqdm de mflux es POR FRAME (siempre «100%|1/1», reiniciándose
    en cada frame), así que no refleja el avance de la carpeta y la barra global
    parecía congelada toda la corrida. La ocultamos y la sustituimos por el conteo
    de archivos (robusto ante cambios de log de mflux). La barra de DESCARGA de
    pesos (lleva «B/s») SÍ se deja pasar para no perder ese feedback la 1ª vez."""
    hechos = -1
    for linea in correr(cmd):
        oculta = (
            "multiples of 16" in linea or "Rounding down" in linea
            or "s/it]" in linea
            or ("it/s]" in linea and "B/s" not in linea)
        )
        if not oculta:
            yield linea
        try:
            n = sum(1 for _ in dir_out.glob("*.png"))
        except OSError:
            n = hechos
        if n != hechos:
            hechos = n
            yield f"🖼️ frame={n}/{total}" if total else f"🖼️ frame={n}"


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
    n_frames = int(info.get("frames") or 0)
    yield f"📹 {info['ancho']}x{info['alto']} · {info['fps']:.2f} fps · {n_frames} frames"
    yield _aviso_16(info["ancho"], info["alto"], resolucion)
    yield _aviso_tiempo_video(info["ancho"], info["alto"], resolucion, n_frames, modelo)
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
        yield from _correr_mlx_video(cmd, dir_out, n_frames)

        # Reensamblado robusto. mflux escribe {image_name}.png = frame_00000001.png…
        # pero un vídeo real puede dar frames de dimensión impar o que varían entre
        # sí (rotación/VFR) → libx264/yuv420p falla con «código 254». Forzamos que
        # TODOS los frames tengan exactamente las mismas dimensiones pares (las del
        # primer frame ya generado) y arrancamos en el primer número real.
        hechas = sorted(dir_out.glob("frame_*.png"))
        if not hechas:
            raise RuntimeError(
                "SeedVR2 (MLX) terminó pero no generó ningún frame de salida. "
                "Revisa el log de mflux más arriba (memoria insuficiente, modelo no "
                "descargado, o un frame de entrada inválido)."
            )
        if len(hechas) < n_frames:
            yield (f"⚠️ Se generaron {len(hechas)} de {n_frames} frames; reensamblo "
                   f"con los disponibles.")
        from PIL import Image
        w0, h0 = Image.open(hechas[0]).size
        w0, h0 = (w0 // 2) * 2, (h0 // 2) * 2          # par → compatible con yuv420p
        try:                                           # número del primer frame real
            inicio = int("".join(filter(str.isdigit, hechas[0].stem)))
        except ValueError:
            inicio = 1

        salida = SALIDAS / f"{entrada.stem}_seedvr2mlx_{resolucion}p.mp4"
        yield f"🎞️ Reensamblando {len(hechas)} frames ({w0}×{h0}) con el audio original…"
        fps_str = f"{info['fps_num']}/{info['fps_den']}"
        yield from correr(ff.cmd_reensamblar(
            dir_out, "frame_%08d.png", fps_str, entrada, salida,
            vf=f"scale={w0}:{h0}:flags=lanczos", start_number=inicio))
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
