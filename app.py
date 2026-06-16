"""PixelBooster — mejora de videos e imágenes con IA, 100% local.

Interfaz Gradio multilingüe (español / English / français). Detecta el hardware
al arrancar y solo ofrece los motores que pueden funcionar en esta máquina
(Mac con chip M o PC con NVIDIA; cualquier otra GPU se queda con los motores
Vulkan). La UI se regenera completa al cambiar de idioma (gr.render).
"""

import base64
import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import time
import traceback
from pathlib import Path

import gradio as gr

import hardware
import licencias
import ajustes
import ui_theme
from engines import ffmpeg_utils as ff
from engines import (birefnet, color, darkir, dehazeformer, diffbir, dreamclear,
                     dsrnet, dut_stab, ema_vfi, faces, faithdiff, fbcnn, fftformer,
                     film, filtros, flashvsr, grano, hat, hvi_cidnet, iclight,
                     inspyrenet, instantir, iopaint_lama, luts, mantenimiento,
                     metalfx, nafnet, osdface, pmrf, practical_rife, realesrgan_mlx,
                     restoreformerpp, restormer, retinexformer, scunet, seedvr2,
                     seedvr2_mlx, shadowformer, video_ia, vulkan)
from i18n import IDIOMAS, idioma_por_defecto, t

VERSION = "1.0"
HW = hardware.info_sistema()

# Saneamiento legal del build que se VENDE: por defecto se EXCLUYEN los motores con
# licencia no comercial / sin licencia (CodeFormer = S-Lab no comercial; OSDFace = sin
# LICENSE). Para uso personal se reactivan con VB_NO_COMERCIAL=1. Reemplazos limpios de
# caras: RestoreFormer++ (Apache) y PMRF (MIT), ya integrados.
INCLUIR_NO_COMERCIAL = os.environ.get("VB_NO_COMERCIAL") == "1"
MOTORES_NO_COMERCIALES = {"codeformer", "osdface"}

# Catálogo COMPLETO de motores de IA por plataforma, para MOSTRARLOS TODOS aunque la
# máquina no pueda usarlos: "mac" = solo Apple Silicon, "nvidia" = solo CUDA, "ambas".
# Los que no aplican a esta máquina se listan atenuados (🔒) bajo el selector.
_CAT_IMG = [
    ("faithdiff", "nvidia"), ("diffbir", "nvidia"), ("pmrf", "nvidia"),
    ("instantir", "nvidia"), ("restormer", "nvidia"), ("retinexformer", "nvidia"),
    ("fftformer", "nvidia"), ("hat", "nvidia"), ("dreamclear", "nvidia"),
    ("iclight", "nvidia"),
    ("seedvr2_mlx_img", "mac"), ("realesrgan_mlx_img", "mac"),
    ("seedvr2_img", "ambas"), ("nafnet", "ambas"), ("scunet", "ambas"),
    ("fbcnn", "ambas"), ("dehazeformer", "ambas"), ("hvi_cidnet", "ambas"),
    ("darkir", "ambas"), ("dsrnet", "ambas"), ("shadowformer", "ambas"),
    ("restoreformerpp", "ambas"), ("inspyrenet", "ambas"), ("birefnet", "ambas"),
]
_CAT_VIDEO = [
    ("flashvsr", "nvidia"), ("film", "nvidia"), ("ema_vfi", "nvidia"),
    ("dut_stab", "nvidia"),
    ("seedvr2_mlx", "mac"), ("metalfx", "mac"),
    ("seedvr2", "ambas"), ("practical_rife", "ambas"),
]


def _apto_plataforma(plat: str) -> bool:
    """¿Esta máquina puede correr un motor de la plataforma dada?"""
    if plat == "nvidia":
        return HW["cuda"]
    if plat == "mac":
        return HW["mps"]
    return True  # "ambas"


def _otros_motores_md(catalogo, activos, etiqueta_fn, lang):
    """Markdown atenuado con los motores del catálogo que NO están en el selector:
    marca 🔒 los que requieren una GPU que no tienes (CUDA o Apple) y ⬇ los que sí
    podrías usar pero están sin instalar. Devuelve "" si no hay ninguno."""
    activos = set(activos)
    lineas = []
    for mid, plat in catalogo:
        if mid in activos:
            continue
        nombre = etiqueta_fn(mid).split(" (")[0]
        if not _apto_plataforma(plat):
            tag = t("req_nvidia", lang) if plat == "nvidia" else t("req_apple", lang)
            lineas.append(f"🔒 {nombre} · <b>{tag}</b>")
        else:
            lineas.append(f"⬇ {nombre} · <i>{t('req_instalar', lang)}</i>")
    if not lineas:
        return ""
    return f"**{t('otros_motores', lang)}**<br>" + "<br>".join(lineas)

# ---------------------------------------------------------------- constantes

# ids internos estables; las etiquetas visibles salen de i18n
MOTORES_VIDEO_NOTAS = {
    "seedvr2": "n_seedvr2", "seedvr2_mlx": "n_seedvr2_mlx", "metalfx": "n_metalfx",
    "realesrgan": "n_realesrgan", "realcugan": "n_realcugan",
    "waifu2x": "n_waifu2x", "rife": "n_rife", "flashvsr": "n_flashvsr",
    "practical_rife": "n_practical_rife", "film": "n_film", "ema_vfi": "n_ema_vfi",
    "dut_stab": "n_dut_stab",
    "grano": "n_grano", "lut": "n_lut",
    "desentrelazar": "n_desentrelazar", "denoise": "n_denoise", "limpiar": "n_limpiar",
    "cine": "n_cine", "lente": "n_lente", "ia": "n_ia",
    "estabilizar": "n_estabilizar",
}
MOTORES_IMG_NOTAS = {
    "faithdiff": "n_faithdiff", "seedvr2_img": "n_seedvr2_img",
    "realesrgan_img": "n_realesrgan_img", "codeformer": "n_codeformer",
    "instantir": "n_instantir", "ddcolor": "n_ddcolor", "grano": "n_grano",
    "lut": "n_lut", "diffbir": "n_diffbir", "pmrf": "n_pmrf",
    "osdface": "n_osdface", "seedvr2_mlx_img": "n_seedvr2_mlx",
    "realesrgan_mlx_img": "n_realesrgan_mlx",
    "restormer": "n_restormer", "retinexformer": "n_retinexformer",
    "dreamclear": "n_dreamclear", "hat": "n_hat",
    "nafnet": "n_nafnet", "scunet": "n_scunet", "fbcnn": "n_fbcnn",
    "fftformer": "n_fftformer", "dehazeformer": "n_dehazeformer",
    "hvi_cidnet": "n_hvi_cidnet", "darkir": "n_darkir",
    "inspyrenet": "n_inspyrenet", "birefnet": "n_birefnet",
    "restoreformerpp": "n_restoreformerpp", "dsrnet": "n_dsrnet",
    "shadowformer": "n_shadowformer", "iclight": "n_iclight",
}
# Presets de grano analógico (etiqueta i18n ↔ id de engines/grano.py)
GRANO_PRESETS = ["fino", "clasico", "alta_iso", "super8", "bn_plata"]
# Motores de imagen que aceptan un prompt opcional.
IMG_CON_PROMPT = ("faithdiff", "instantir", "iclight")

# Formatos de salida
_FORMATOS_VIDEO = [
    ("H.264 MP4", "h264"),
    ("H.265 HEVC", "h265"),
    ("ProRes 422 HQ", "prores"),
    ("ProRes 4444 (10-bit + alfa)", "prores4444"),
    ("ProRes 4444 XQ (máxima calidad)", "prores4444xq"),
    ("WebM VP9", "webm"),
]
_FORMATOS_IMG = [
    ("PNG", "png"),
    ("JPEG 95%", "jpeg"),
    ("TIFF", "tiff"),
    ("WebP", "webp"),
]

# Directorio de presets de revelado
_PRESET_DIR = Path(__file__).parent / "presets"
_PRESET_DIR.mkdir(exist_ok=True)

# Orden plano del panel de revelado (debe coincidir con grupo_revelado).
_CLAVES_REVELADO = (
    "exposicion", "contraste", "altas", "sombras", "blancos", "negros",
    "temperatura", "tinte", "saturacion",
    "vibranza", "matiz", "desvaido", "tinte_sombras", "tinte_altas",
    "nitidez", "claridad", "ruido", "vineta",
)

# Preset keys: lut1,mix1,lut2,mix2,lut3,mix3 + 18 Lumetri params
_PRESET_KEYS = (
    "lut1", "mix1", "lut2", "mix2", "lut3", "mix3",
) + _CLAVES_REVELADO

_PRESET_DEFAULTS = (
    "portra400", 1.0, "ninguno", 1.0, "ninguno", 1.0,
    0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 6500, 0.0, 1.0,
    0.0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
)

# Disponibilidad de vidstab (cacheado al arrancar)
_VIDSTAB_OK: bool = filtros.VIDSTAB_OK

from engines import SALIDAS, MODELS


# ---------------------------------------------------------------- helpers

def _transcodificar_video(entrada: str, formato: str, log: list) -> str:
    """Post-procesa el video de salida del motor al formato elegido con FFmpeg.

    Devuelve la ruta final (puede ser distinta de `entrada` si hay conversión).
    """
    entrada = Path(entrada)
    codecs = {
        "h264":   (["-c:v", "libx264", "-crf", "17", "-preset", "medium",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k"], ".mp4"),
        "h265":   (["-c:v", "libx265", "-crf", "20", "-preset", "medium",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k"], ".mp4"),
        "prores": (["-c:v", "prores_ks", "-profile:v", "3",
                    "-c:a", "pcm_s16le"], ".mov"),
        # ProRes 4444 (perfil 4) y 4444 XQ (perfil 5): 4:4:4 a 10/12-bit con canal
        # alfa. prores_ks lo soporta de sobra; ProRes RAW NO se puede codificar con
        # FFmpeg (Apple no licencia el encoder), así que no se ofrece.
        "prores4444": (["-c:v", "prores_ks", "-profile:v", "4",
                        "-pix_fmt", "yuva444p10le", "-c:a", "pcm_s16le"], ".mov"),
        "prores4444xq": (["-c:v", "prores_ks", "-profile:v", "5",
                          "-pix_fmt", "yuva444p10le", "-c:a", "pcm_s16le"], ".mov"),
        "webm":   (["-c:v", "libvpx-vp9", "-crf", "32", "-b:v", "0",
                    "-c:a", "libopus", "-b:a", "128k"], ".webm"),
    }
    if formato not in codecs or formato == "h264":
        return str(entrada)  # h264 ya es el formato nativo de los motores
    flags, ext = codecs[formato]
    salida = entrada.with_suffix(ext)
    if salida == entrada:
        salida = entrada.with_name(entrada.stem + "_fmt" + ext)
    cmd = [ff.ffmpeg(), "-y", "-i", str(entrada)] + flags + [str(salida)]
    log.append(f"▶ transcodificar → {ext}")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        log.append(f"⚠️ transcodificación falló: {r.stderr[-200:]}")
        return str(entrada)
    return str(salida)


def _convertir_imagen(entrada: str, formato: str) -> str:
    """Convierte la imagen de salida al formato elegido con PIL.

    Devuelve la ruta final.
    """
    from PIL import Image

    entrada = Path(entrada)
    ext_map = {"png": ".png", "jpeg": ".jpg", "tiff": ".tif", "webp": ".webp"}
    save_kwargs = {
        "png": {},
        "jpeg": {"quality": 95},
        "tiff": {},
        "webp": {"quality": 92, "method": 4},
    }
    if formato not in ext_map or entrada.suffix.lower() in (".png",) and formato == "png":
        return str(entrada)
    ext = ext_map[formato]
    salida = entrada.with_suffix(ext)
    if salida == entrada:
        salida = entrada.with_name(entrada.stem + "_fmt" + ext)
    img = Image.open(entrada)
    if img.mode not in ("RGB", "RGBA", "L"):
        img = img.convert("RGB")
    if formato == "jpeg" and img.mode in ("RGBA",):
        img = img.convert("RGB")
    img.save(salida, **save_kwargs.get(formato, {}))
    return str(salida)


def _listar_presets_revelado() -> list[str]:
    return sorted(p.stem for p in _PRESET_DIR.glob("*.json"))


def _estado_modelos() -> dict:
    """Devuelve un dict {nombre: bool} indicando si los pesos están presentes."""
    sv2_dir = MODELS / "SEEDVR2"
    sv2_ok = sv2_dir.is_dir() and (
        any(sv2_dir.glob("*.safetensors")) or any(sv2_dir.glob("*.gguf")))
    fd_ok = (MODELS / "FaithDiff" / "Real_4_SDXL").is_dir()
    ir_ok = (MODELS / "InstantIR").is_dir() and any((MODELS / "InstantIR").iterdir())
    dd_ok = (MODELS / "DDColor" / "pytorch_model.pt").exists()
    return {
        "SeedVR2": sv2_ok,
        "FaithDiff": fd_ok,
        "InstantIR": ir_ok,
        "DDColor": dd_ok,
    }


# ---------------------------------------------------------------- comparador

def _data_uri(ruta, max_lado=1500):
    """Carga una imagen, la reduce si es enorme y la devuelve como data URI JPEG."""
    from PIL import Image

    img = Image.open(ruta)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    w, h = img.size
    if max(w, h) > max_lado:
        f = max_lado / max(w, h)
        img = img.resize((round(w * f), round(h * f)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=88)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def comparador_html(antes, despues, lang):
    """Slider antes/después en CSS puro (clip-path); sin dependencias ni JS externo."""
    try:
        a, d = _data_uri(antes), _data_uri(despues)
    except Exception:
        return (f'<p style="color:var(--vb-muted,#7c776d)">{t("listo", lang)} — '
                f'{despues}</p>')
    fs_js = ("var c=this.closest('.ba-cmp');"
             "if(document.fullscreenElement){document.exitFullscreen()}"
             "else{(c.requestFullscreen||c.webkitRequestFullscreen).call(c)}")
    return (
        '<div class="ba-cmp" style="--pos:50%">'
        f'<img class="ba-after" src="{d}">'
        f'<img class="ba-before" src="{a}" '
        'style="clip-path:inset(0 calc(100% - var(--pos)) 0 0)">'
        '<div class="ba-line"></div>'
        f'<span class="ba-tag ba-l">{t("antes", lang)}</span>'
        f'<span class="ba-tag ba-r">{t("despues", lang)}</span>'
        f'<button class="ba-fs" type="button" title="{t("comparador_fs", lang)}" '
        f'onclick="{fs_js}">⤢</button>'
        '<input type="range" min="0" max="100" value="50" '
        "oninput=\"this.parentNode.style.setProperty('--pos', this.value+'%')\">"
        '</div>'
    )


# ---------------------------------------------------------------- lógica

def _revelar(entrada, es_video, rev):
    """Convierte los valores planos del panel (3 LUTs + ajustes) en etalonar()."""
    l1, m1, l2, m2, l3, m3, *ajustes = rev
    return luts.etalonar(
        entrada, es_video=es_video, looks=[(l1, m1), (l2, m2), (l3, m3)],
        **{k: float(v) for k, v in zip(_CLAVES_REVELADO, ajustes)},
    )


def _consumir(gen, log):
    """Consume el generador del motor cediendo el log acumulado; captura su retorno.

    Añade prefijo de tiempo transcurrido (⏱ MM:SS) después de 3 segundos.
    """
    inicio = time.time()
    try:
        while True:
            try:
                linea = next(gen)
            except StopIteration as fin:
                return fin.value
            log.append(linea)
            t_elapsed = time.time() - inicio
            prefix = f"⏱ {int(t_elapsed // 60):02d}:{int(t_elapsed % 60):02d}  " if t_elapsed > 3 else ""
            yield prefix + "\n".join(log[-400:])
    finally:
        gen.close()


# ---- barra de % de avance: leer el progreso del propio log del motor ----
# correr() une stderr→stdout, así que el avance de FFmpeg (frame=/time=), de los
# binarios Vulkan ncnn y de las barras tqdm (45%|…) llega como líneas de log.
_RE_FRAME = re.compile(r"frame=\s*(\d+)")
_RE_TIME = re.compile(r"time=\s*(\d+):(\d+):(\d+(?:\.\d+)?)")
# % SOLO cuando la línea ES un porcentaje (Vulkan ncnn: "12.50%" / "[12%]") o es una
# barra tqdm ("45%|████"). Así NO confundimos con las estadísticas de x264, que
# llevan muchos "%" sueltos en su resumen final.
_RE_PCT_SOLO = re.compile(r"^\s*\[?\s*(\d{1,3}(?:\.\d+)?)\s*%\s*\]?\s*$")
_RE_PCT_TQDM = re.compile(r"(\d{1,3}(?:\.\d+)?)\s*%\s*\|")


def _totales_video(video):
    """(frames, segundos) del video; (0, 0.0) si no se puede saber."""
    try:
        info = ff.info_video(video)
        return int(info.get("frames") or 0), float(info.get("duracion") or 0)
    except Exception:
        return 0, 0.0


def _pct_de_linea(linea, total_frames, total_seg):
    """Avance 0–1 deducido de una línea de log; None si no hay ninguna señal.

    Prioriza las señales fiables y monótonas de FFmpeg (time=, luego frame=) y deja
    el porcentaje suelto (Vulkan/tqdm) como último recurso cuando no hay totales.
    """
    if total_seg > 0:
        m = _RE_TIME.search(linea)
        if m:
            seg = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
            return max(0.0, min(1.0, seg / total_seg))
    if total_frames > 0:
        m = _RE_FRAME.search(linea)
        if m:
            return max(0.0, min(1.0, int(m.group(1)) / total_frames))
    m = _RE_PCT_SOLO.match(linea) or _RE_PCT_TQDM.search(linea)
    if m:
        v = float(m.group(1))
        if 0.0 <= v <= 100.0:
            return v / 100.0
    return None


def _barra(frac=None, global_frac=None, fase=""):
    """Actualiza la barra de avance (HTML) DEBAJO de la consola.

    `frac`        None → oculta (no hay proceso). 0–1 → barra del SUB-PROCESO actual.
    `global_frac` 0–1  → añade ARRIBA una segunda barra de progreso GLOBAL del render
                         (estilo cola de After Effects/Premiere); None → no se muestra.
    `fase`        texto opcional para la barra global (p.ej. "Paso 2/3").
    """
    if frac is None:
        return gr.update(visible=False, value="")
    pct = max(0, min(100, round(frac * 100)))
    html = ""
    if global_frac is not None:
        g = max(0, min(100, round(global_frac * 100)))
        etq = f"Render global · {fase}" if fase else "Render global"
        html += (f"<div class='vb-bar-lbl'>{etq}</div>"
                 f"<div class='vb-bar vb-bar-g'><div class='vb-bar-fill' "
                 f"style='width:{g}%'></div></div><div class='vb-bar-pct'>{g}%</div>")
    html += (f"<div class='vb-bar-lbl vb-bar-lbl2'>Proceso actual</div>"
             if global_frac is not None else "")
    html += (f"<div class='vb-bar'><div class='vb-bar-fill' style='width:{pct}%'>"
             f"</div></div><div class='vb-bar-pct'>{pct}%</div>")
    return gr.update(visible=True, value=html)


# Marca de fase que los motores multi-etapa emiten en el log ("📊 Paso 2/3 · …")
# para alimentar la barra de progreso GLOBAL.
_RE_FASE = re.compile(r"[Pp]aso\s+(\d+)\s*/\s*(\d+)")


def hacer_procesar_video(lang):
    def procesar(video, motor, escala, ruido, mult, resolucion, modelo, batch, formato):
        oculto = gr.update(visible=False)
        if not video:
            yield t("sube_video", lang), None, "", oculto, _barra(None)
            return
        total_f, total_s = _totales_video(video)
        log = [f"▶ {t('m_' + motor, lang).split(' — ')[0]}"]
        try:
            if motor == "seedvr2":
                gen = seedvr2.mejorar(video, resolucion=int(resolucion), modelo=modelo,
                                      batch_size=int(batch), es_video=True)
            elif motor == "seedvr2_mlx":
                gen = seedvr2_mlx.mejorar(video, es_video=True, resolucion=int(resolucion))
            elif motor == "metalfx":
                gen = metalfx.mejorar(video, escala=int(escala))
            elif motor == "rife":
                gen = vulkan.interpolar_video(video, mult=int(mult))
            elif motor == "practical_rife":
                gen = practical_rife.interpolar(video, mult=int(mult))
            elif motor == "film":
                gen = film.interpolar(video, mult=int(mult))
            elif motor == "ema_vfi":
                gen = ema_vfi.interpolar(video, mult=int(mult))
            elif motor == "dut_stab":
                gen = dut_stab.estabilizar(video)
            elif motor == "flashvsr":
                gen = flashvsr.mejorar(video)
            else:
                gen = vulkan.mejorar_video(video, motor=motor, escala=int(escala),
                                           ruido=int(ruido))
            consumo = _consumir(gen, log)
            salida = None
            pct, fase_cur, fase_tot = 0.0, 1, 1
            while True:
                try:
                    texto = next(consumo)
                    linea = log[-1] if log else ""
                    mf = _RE_FASE.search(linea)
                    if mf:
                        fase_cur, fase_tot = int(mf.group(1)), int(mf.group(2))
                        pct = 0.0  # nueva fase: el % del sub-proceso reinicia
                    frac = _pct_de_linea(linea, total_f, total_s)
                    if frac is not None:
                        pct = frac
                    glob = (((fase_cur - 1) + pct) / fase_tot) if fase_tot > 1 else None
                    fase_txt = f"Paso {fase_cur}/{fase_tot}" if fase_tot > 1 else ""
                    yield texto, None, "", oculto, _barra(pct, glob, fase_txt)
                except StopIteration as fin:
                    salida = fin.value
                    break

            # `salida` es H.264 (siempre reproducible en el navegador): es lo que
            # alimenta el reproductor y el comparador. El formato elegido (ProRes,
            # H.265, WebM) se entrega APARTE como descarga — meter ProRes en el
            # reproductor del navegador da un recuadro en blanco.
            descarga = salida
            if salida and formato and formato != "h264":
                descarga = _transcodificar_video(salida, formato, log)

            log.append(f"{t('listo', lang)}: {Path(salida).name if salida else '?'}")

            # Comparador antes/después (frames). Los JPEG temporales se borran
            # en cuanto comparador_html los incrusta como data URI (no se reusan).
            cmp_html = ""
            if salida:
                frame_antes = frame_despues = None
                try:
                    frame_antes = ff.extraer_frame_preview(video, 0.3)
                    frame_despues = ff.extraer_frame_preview(salida, 0.3)
                    if frame_antes and frame_despues:
                        cmp_html = comparador_html(frame_antes, frame_despues, lang)
                except Exception:
                    pass
                finally:
                    for f in (frame_antes, frame_despues):
                        if f:
                            Path(f).unlink(missing_ok=True)

            dl = (gr.update(value=descarga, visible=True) if descarga else oculto)
            yield "\n".join(log[-400:]), salida, cmp_html, dl, _barra(None)
        except Exception as e:
            log += ["", f"{t('error', lang)}: {e}", traceback.format_exc(limit=3)]
            yield "\n".join(log[-400:]), None, "", oculto, _barra(None)

    return procesar


def hacer_aplicar_filtros(lang):
    """Aplica un filtro de post-proceso (revelado/grano/limpieza) AL RESULTADO ya
    mejorado (o al video original si aún no se mejoró), y actualiza el reproductor,
    el comparador y la descarga. Permite encadenar (aplicar uno tras otro)."""
    def aplicar(salida_actual, video_orig, filtro, g_preset, g_int, g_tam, g_color,
                den_luma, den_croma, est_suav, est_zoom, lente_k1, lente_k2,
                ia_modelo, formato, *rev):
        oculto = gr.update(visible=False)
        base = salida_actual or video_orig
        if not base:
            yield t("filtros_sin_base", lang), None, "", oculto, _barra(None)
            return
        total_f, total_s = _totales_video(base)
        log = [f"▶ {t('m_' + filtro, lang).split(' — ')[0]}"]
        try:
            if filtro == "lut":
                gen = _revelar(base, es_video=True, rev=rev)
            elif filtro == "grano":
                gen = grano.aplicar(base, es_video=True, preset=g_preset,
                                    intensidad=float(g_int), tamano=int(g_tam),
                                    grano_color=bool(g_color))
            elif filtro == "desentrelazar":
                gen = filtros.desentrelazar(base)
            elif filtro == "denoise":
                gen = filtros.denoise(base, luma=float(den_luma), chroma=float(den_croma))
            elif filtro == "estabilizar":
                gen = filtros.estabilizar(base, suavidad=int(est_suav), zoom=float(est_zoom))
            elif filtro == "limpiar":
                gen = filtros.limpiar(base)
            elif filtro == "cine":
                gen = filtros.cine(base)
            elif filtro == "lente":
                gen = filtros.corregir_lente(base, k1=float(lente_k1), k2=float(lente_k2))
            elif filtro == "ia":
                gen = video_ia.mejorar(base, modelo=ia_modelo)
            else:
                yield t("filtros_sin_base", lang), salida_actual, "", oculto, _barra(None)
                return
            consumo = _consumir(gen, log)
            salida = None
            pct, fase_cur, fase_tot = 0.0, 1, 1
            while True:
                try:
                    texto = next(consumo)
                    linea = log[-1] if log else ""
                    mf = _RE_FASE.search(linea)
                    if mf:
                        fase_cur, fase_tot = int(mf.group(1)), int(mf.group(2))
                        pct = 0.0
                    frac = _pct_de_linea(linea, total_f, total_s)
                    if frac is not None:
                        pct = frac
                    glob = (((fase_cur - 1) + pct) / fase_tot) if fase_tot > 1 else None
                    fase_txt = f"Paso {fase_cur}/{fase_tot}" if fase_tot > 1 else ""
                    yield texto, None, "", oculto, _barra(pct, glob, fase_txt)
                except StopIteration as fin:
                    salida = fin.value
                    break

            descarga = salida
            if salida and formato and formato != "h264":
                descarga = _transcodificar_video(salida, formato, log)
            log.append(f"{t('listo', lang)}: {Path(salida).name if salida else '?'}")

            cmp_html = ""
            if salida:
                fa = fd = None
                try:
                    fa = ff.extraer_frame_preview(base, 0.3)
                    fd = ff.extraer_frame_preview(salida, 0.3)
                    if fa and fd:
                        cmp_html = comparador_html(fa, fd, lang)
                except Exception:
                    pass
                finally:
                    for f in (fa, fd):
                        if f:
                            Path(f).unlink(missing_ok=True)
            dl = (gr.update(value=descarga, visible=True) if descarga else oculto)
            yield "\n".join(log[-400:]), salida, cmp_html, dl, _barra(None)
        except Exception as e:
            log += ["", f"{t('error', lang)}: {e}", traceback.format_exc(limit=3)]
            yield "\n".join(log[-400:]), None, "", oculto, _barra(None)

    return aplicar


def hacer_preview_filtro(lang):
    """Vista previa rápida (un frame) de cómo quedará el filtro, sin aplicarlo."""
    from engines import preview as _prev

    def previsualizar(pos, salida_actual, video_orig, filtro, g_preset, g_int, g_tam,
                      g_color, den_luma, den_croma, *rev):
        base = salida_actual or video_orig
        if not base:
            return f"<p class='size-preview'>{t('filtros_sin_base', lang)}</p>"
        try:
            pos = max(0.0, min(1.0, float(pos or 0.3)))
            antes, despues, soporta = _prev.previsualizar(
                base, filtro, pos=pos, g_preset=g_preset, g_int=g_int, g_tam=g_tam,
                g_color=g_color, den_luma=float(den_luma), den_croma=float(den_croma),
                rev=rev)
            if not soporta:
                html = f"<p class='size-preview'>{t('preview_temporal', lang)}</p>"
            else:
                html = comparador_html(antes, despues, lang)
        except Exception as e:
            return f"<p class='size-preview'>⚠️ {e}</p>"
        finally:
            pass
        # limpiar frames temporales tras incrustarlos
        for f in (antes, despues):
            try:
                if f and "salidas" not in str(f):
                    Path(f).unlink(missing_ok=True)
            except Exception:
                pass
        return html

    return previsualizar


def hacer_comparar_frame(lang):
    """Compara entrada vs resultado en el frame exacto donde el usuario pausó el
    video (la posición la rellena el JS con el tiempo del reproductor)."""
    def comparar(pos, video_in, video_out):
        if not video_out:
            return f"<p class='size-preview'>{t('cmp_sin_resultado', lang)}</p>"
        pos = max(0.0, min(1.0, float(pos or 0.3)))
        fa = ff.extraer_frame_preview(video_in, pos) if video_in else None
        fd = ff.extraer_frame_preview(video_out, pos)
        try:
            if fa and fd:
                return comparador_html(fa, fd, lang)
            return f"<p class='size-preview'>{t('cmp_sin_resultado', lang)}</p>"
        finally:
            for f in (fa, fd):
                if f:
                    Path(f).unlink(missing_ok=True)

    return comparar


def hacer_borrar(lang):
    """Borrar objetos: el usuario pinta de blanco lo que sobra en el lienzo
    (gr.ImageEditor) y LaMa (IOPaint) rellena el hueco. Construye la máscara desde
    las capas pintadas y llama a engines.iopaint_lama.borrar."""
    import numpy as np
    from PIL import Image

    def borrar_obj(editor):
        oculto = gr.update(visible=False)
        if not editor or editor.get("background") is None:
            yield t("borrar_sube", lang), "", oculto
            return
        fondo = np.asarray(editor["background"])[:, :, :3]
        capas = editor.get("layers") or []
        # Máscara = blanco donde el usuario pintó (alpha>0 en cualquier capa).
        mascara = np.zeros(fondo.shape[:2], dtype=np.uint8)
        for capa in capas:
            capa = np.asarray(capa)
            if capa.ndim == 3 and capa.shape[2] == 4:
                mascara[capa[:, :, 3] > 10] = 255
            elif capa.ndim == 3:
                mascara[capa.sum(axis=2) > 20] = 255
        if not mascara.any():
            yield t("borrar_sin_mascara", lang), "", oculto
            return
        tmp = Path(tempfile.mkdtemp(prefix="vb_borrar_"))
        img_p, msk_p = tmp / "img.png", tmp / "mask.png"
        Image.fromarray(fondo).save(img_p)
        Image.fromarray(mascara).save(msk_p)
        log = ["▶ borrar objeto (IOPaint · LaMa)"]
        try:
            gen = iopaint_lama.borrar(str(img_p), str(msk_p))
            consumo = _consumir(gen, log)
            salida = None
            while True:
                try:
                    yield next(consumo), "", oculto
                except StopIteration as fin:
                    salida = fin.value
                    break
            html = (f"<img src='{_data_uri(salida)}' style='max-width:100%;border-radius:8px'>"
                    if salida else "")
            dl = (gr.update(value=salida, visible=True) if salida else oculto)
            yield "\n".join(log[-400:]), html, dl
        except Exception as e:
            log += ["", f"{t('error', lang)}: {e}", traceback.format_exc(limit=3)]
            yield "\n".join(log[-400:]), "", oculto
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    return borrar_obj


def hacer_procesar_imagen(lang):
    def procesar(imagen, motor, prompt, escala, resolucion, fidelidad,
                 tarea_rest, g_preset, g_int, g_tam, g_color, formato_img, *rev):
        oculto = gr.update(visible=False)
        if not imagen:
            yield t("sube_imagen", lang), "", oculto
            return
        log = [f"▶ {motor}"]
        try:
            if motor == "faithdiff":
                gen = faithdiff.mejorar(imagen, prompt=prompt or "", escala=int(escala))
            elif motor == "diffbir":
                gen = diffbir.mejorar(imagen, escala=int(escala))
            elif motor == "pmrf":
                gen = pmrf.mejorar(imagen)
            elif motor == "osdface":
                gen = osdface.mejorar(imagen)
            elif motor == "restormer":
                gen = restormer.mejorar(imagen, tarea=tarea_rest or "Motion_Deblurring")
            elif motor == "retinexformer":
                gen = retinexformer.mejorar(imagen)
            elif motor == "dreamclear":
                gen = dreamclear.mejorar(imagen, escala=int(escala))
            elif motor == "hat":
                gen = hat.mejorar(imagen, escala=int(escala))
            elif motor == "nafnet":
                gen = nafnet.mejorar(imagen, tarea="denoise")
            elif motor == "scunet":
                gen = scunet.mejorar(imagen)
            elif motor == "fbcnn":
                gen = fbcnn.mejorar(imagen)
            elif motor == "fftformer":
                gen = fftformer.mejorar(imagen)
            elif motor == "dehazeformer":
                gen = dehazeformer.mejorar(imagen)
            elif motor == "hvi_cidnet":
                gen = hvi_cidnet.mejorar(imagen)
            elif motor == "darkir":
                gen = darkir.mejorar(imagen)
            elif motor == "inspyrenet":
                gen = inspyrenet.mejorar(imagen)
            elif motor == "birefnet":
                gen = birefnet.mejorar(imagen)
            elif motor == "restoreformerpp":
                gen = restoreformerpp.mejorar(imagen, escala=2)
            elif motor == "dsrnet":
                gen = dsrnet.mejorar(imagen)
            elif motor == "shadowformer":
                gen = shadowformer.mejorar(imagen)
            elif motor == "iclight":
                gen = iclight.relight(imagen, prompt=prompt or "", direccion="izquierda")
            elif motor == "seedvr2_img":
                gen = seedvr2.mejorar(imagen, resolucion=int(resolucion), es_video=False)
            elif motor == "seedvr2_mlx_img":
                gen = seedvr2_mlx.mejorar(imagen, es_video=False, resolucion=int(resolucion))
            elif motor == "realesrgan_mlx_img":
                gen = realesrgan_mlx.mejorar(imagen, es_video=False)
            elif motor == "codeformer":
                gen = faces.restaurar_caras(imagen, fidelidad=float(fidelidad), escala=int(escala))
            elif motor == "instantir":
                gen = instantir.mejorar(imagen, prompt=prompt or "")
            elif motor == "ddcolor":
                gen = color.colorizar(imagen)
            elif motor == "grano":
                gen = grano.aplicar(imagen, es_video=False, preset=g_preset,
                                    intensidad=float(g_int), tamano=int(g_tam),
                                    grano_color=bool(g_color))
            elif motor == "lut":
                gen = _revelar(imagen, es_video=False, rev=rev)
            else:
                gen = vulkan.mejorar_imagen(imagen, escala=int(escala))
            consumo = _consumir(gen, log)
            salida = None
            while True:
                try:
                    yield next(consumo), "", oculto
                except StopIteration as fin:
                    salida = fin.value
                    break

            # Post-proceso: conversión de formato de imagen
            if salida and formato_img:
                salida = _convertir_imagen(salida, formato_img)

            log.append(f"{t('listo', lang)}: {salida}")
            yield ("\n".join(log[-400:]), comparador_html(imagen, salida, lang),
                   gr.update(value=salida, visible=True))
        except Exception as e:
            log += ["", f"{t('error', lang)}: {e}", traceback.format_exc(limit=3)]
            yield "\n".join(log[-400:]), "", oculto

    return procesar


def hacer_procesar_lote(lang):
    def procesar(archivos, motor, escala, resolucion, formato):
        if not archivos:
            yield "⚠️ No hay archivos seleccionados."
            return
        total = len(archivos)
        log = [f"▶ Lote: {total} archivos · motor {motor}"]
        for n, f_obj in enumerate(archivos, 1):
            ruta = f_obj if isinstance(f_obj, str) else f_obj.name
            nombre = Path(ruta).name
            log.append(t("lote_archivo_n", lang).format(n=n, total=total, nombre=nombre))
            yield "\n".join(log[-400:])
            try:
                if motor == "seedvr2":
                    gen = seedvr2.mejorar(ruta, resolucion=int(resolucion), es_video=True)
                elif motor == "rife":
                    gen = vulkan.interpolar_video(ruta, mult=2)
                elif motor == "flashvsr":
                    gen = flashvsr.mejorar(ruta)
                elif motor == "desentrelazar":
                    gen = filtros.desentrelazar(ruta)
                elif motor == "denoise":
                    gen = filtros.denoise(ruta)
                elif motor in ("realesrgan", "realcugan", "waifu2x"):
                    gen = vulkan.mejorar_video(ruta, motor=motor, escala=int(escala), ruido=0)
                else:
                    raise ValueError(f"Motor no soportado en lote: {motor}")

                consumo = _consumir(gen, log)
                salida = None
                while True:
                    try:
                        yield next(consumo)
                    except StopIteration as fin:
                        salida = fin.value
                        break

                if salida and formato:
                    salida = _transcodificar_video(salida, formato, log)

                log.append(f"  ✅ {n}/{total}: {Path(salida).name if salida else '?'}")
            except Exception as e:
                log.append(f"  ❌ {n}/{total}: {e}")
            yield "\n".join(log[-400:])
        log.append(f"✅ Lote completado: {total} archivos.")
        yield "\n".join(log[-400:])

    return procesar


def hacer_vista_previa(lang):
    def vista_previa(video, motor, escala, mult, resolucion):
        # Nombre corto del motor (antes del " — " de la etiqueta i18n).
        etiqueta = t("m_" + motor, lang).split(" — ")[0]
        cab = f"**{t('vp_motor', lang)}:** {etiqueta}"
        if not video:
            return cab
        try:
            info = ff.info_video(video)
        except Exception:
            return cab
        w, h = info["ancho"], info["alto"]
        if motor == "rife":
            return (f"{cab} · {w}×{h} ({t('se_mantiene', lang)}) · "
                    f"{info['fps']:.0f} → **{info['fps'] * int(mult or 2):.0f} fps**")
        if motor not in _ESCALADORES:
            # Filtros FFmpeg: no cambian la resolución (lo decimos sin ambigüedad).
            return f"{cab} · {w}×{h} — {t('vp_no_resol', lang)}"
        # Escaladores: calculamos la resolución final.
        if motor in ("seedvr2", "flashvsr"):
            factor = int(resolucion or 1080) / min(w, h)
            nw, nh = round(w * factor / 2) * 2, round(h * factor / 2) * 2
        else:
            nw, nh = w * int(escala or 2), h * int(escala or 2)
        _8k = max(nw, nh) >= 7680
        _puede_8k = (HW["cuda"] and HW["vram_gb"] >= 16) or (HW["mps"] and HW["ram_gb"] >= 48)
        if _8k and not _puede_8k:
            mem = (f"{HW['vram_gb']:.0f} GB VRAM" if HW["cuda"]
                   else f"{HW['ram_gb']:.0f} GB RAM")
            aviso = f"{t('aviso_8k_insuf', lang)} ({mem})"
        elif max(nw, nh) > 4096:
            aviso = t("supera_4k", lang)
        else:
            aviso = ""
        return f"{cab} · {w}×{h} {t('vp_sube_a', lang)} **{nw}×{nh}**{aviso}"

    return vista_previa


def picker_temas_html(lang):
    """Galería de temas: 3 claros + 3 oscuros, cada uno con un swatch (fondo +
    superficie + acento). Al pulsar aplica el tema en cliente (window.vbTema)."""
    def card(tid):
        v = ui_theme.TEMAS[tid]["vars"]
        return (
            f'<button type="button" class="vb-tema" data-tema="{tid}" '
            f"onclick=\"window.vbTema('{tid}');return false;\">"
            f'<span class="vb-tema-sw" style="--c1:{v["--vb-bg"]};'
            f'--c2:{v["--vb-surface"]};--c3:{v["--vb-accent"]}"></span>'
            f'<span class="vb-tema-nom">{t("tema_" + tid, lang)}</span></button>')

    def grupo(titulo, ids):
        cards = "".join(card(tid) for tid in ids)
        return (f'<div class="vb-temas-grupo"><span class="vb-temas-tit">{titulo}</span>'
                f'<div class="vb-temas-row">{cards}</div></div>')

    return (
        '<div class="vb-temas">'
        + grupo(t("ap_grupo_claros", lang), ui_theme.TEMAS_CLAROS)
        + grupo(t("ap_grupo_oscuros", lang), ui_theme.TEMAS_OSCUROS)
        + '</div>')


def picker_fuentes_html(lang):
    """Selector de tipografía: cada botón se previsualiza en su propia fuente y
    al pulsar la aplica en cliente (window.vbFuente)."""
    botones = "".join(
        f'<button type="button" class="vb-fuente" data-fuente="{fid}" '
        f"onclick=\"window.vbFuente('{fid}');return false;\" "
        # comillas simples: las dobles romperían el atributo style (preview)
        f"style=\"font-family:{', '.join(ui_theme.FUENTES[fid]).replace(chr(34), chr(39))}\">"
        f'{t("fuente_" + fid, lang)}</button>'
        for fid in ui_theme.FUENTES_ORDEN)
    return (f'<span class="vb-tipo-tit">{t("aj_tipografia", lang)}</span>'
            f'<div class="vb-fuentes">{botones}</div>')


def gpu_resumen(lang):
    """Línea legible del equipo detectado (GPU/chip + memoria)."""
    if HW["cuda"]:
        return f"NVIDIA {HW['gpu']} · {HW['vram_gb']} GB VRAM"
    if HW["mps"]:
        return f"Apple Silicon · {HW['ram_gb']:.0f} GB {t('mem_unificada', lang)}"
    return t("gpu_generica", lang)


def texto_niveles(lang):
    """Explica los 3 niveles, de qué dependen y cuál te tocó (y por qué)."""
    n = HW["nivel"]
    if HW["mps"]:
        porque = t("aj_nivel_why_mac", lang)
    elif HW["cuda"]:
        porque = t("aj_nivel_why_cuda", lang)
    else:
        porque = t("aj_nivel_why_gen", lang)
    niv = lambda k: t("nivel", lang) + f" {k} · " + t(f"nivel_{k}", lang)
    return "\n".join([
        f"### {t('aj_niveles_tit', lang)}",
        t("aj_niveles_intro", lang),
        "",
        f"- **{niv(1)}** _({t('aj_nivel_min', lang)})_ — {t('aj_nivel1', lang)}",
        f"- **{niv(2)}** — {t('aj_nivel2', lang)}",
        f"- **{niv(3)}** _({t('aj_nivel_max', lang)})_ — {t('aj_nivel3', lang)}",
        "",
        f"**{t('aj_nivel_tuyo', lang)}: {niv(n)}** — {porque}",
    ])


def texto_requisitos(lang):
    """Tarjeta gráfica mínima e ideal para PC y Mac."""
    return t("req_txt", lang)


# --- Tema + tipografía: JS de cliente (aplicación y persistencia) -------------
# vbTema()/vbFuente() viven en ui_theme; aquí los cargamos al inicio aplicando lo
# guardado (o los valores por defecto).
_JS_CARGA = """() => {
  %s
  %s
  try { window.vbTema(localStorage.getItem('vb_tema') || '%s'); } catch (e) {}
  try { window.vbFuente(localStorage.getItem('vb_fuente') || '%s'); } catch (e) {}
  // Clic en el logo PixelBooster (zona a la izquierda de las pestañas) → inicio
  // (primera pestaña). Gradio solo conmuta con la secuencia completa de eventos,
  // no con .click(); por eso la replicamos. Delegado en document para sobrevivir
  // a los re-render de @gr.render.
  if (!window.__vbLogoNav) {
    window.__vbLogoNav = true;
    const irAPestana = (btn) => {
      const r = btn.getBoundingClientRect();
      const o = {bubbles:true, cancelable:true, composed:true, view:window,
                 clientX: Math.round(r.left + r.width/2),
                 clientY: Math.round(r.top + r.height/2)};
      ['pointerdown','mousedown','pointerup','mouseup','click'].forEach(ty => {
        const E = (ty[0] === 'p' && window.PointerEvent) ? PointerEvent : MouseEvent;
        btn.dispatchEvent(new E(ty, o));
      });
    };
    document.addEventListener('click', (e) => {
      const wrap = e.target && e.target.closest && e.target.closest('.tab-wrapper');
      if (!wrap) return;
      const first = wrap.querySelector('.tab-container[role="tablist"] button');
      if (first && e.clientX < first.getBoundingClientRect().left) irAPestana(first);
    });
  }
}""" % (ui_theme.temas_js(), ui_theme.fuentes_js(),
        ui_theme.TEMA_DEFECTO, ui_theme.FUENTE_DEFECTO)

# Lee el tiempo ACTUAL del reproductor de resultado/preview (#vb-result) y lo
# convierte en fracción 0–1, para que "este frame" sea justo donde el usuario paró
# la barra. Constante de módulo: la usan los botones de comparación y el comparador
# de LUTs que vive dentro del panel de looks.
_JS_POS = ("(pos, ...rest) => { const v = document.querySelector('#vb-result video') "
           "|| document.querySelector('#vb-input video'); "
           "if (v && v.duration) pos = v.currentTime / v.duration; "
           "return [pos, ...rest]; }")


def texto_sistema(lang):
    # --- Resumen de hardware ---
    filas = [
        f"- **{t('s_sistema', lang)}:** {HW['so']}" + (" (Apple Silicon)" if HW["apple_silicon"] else ""),
        f"- **GPU:** {HW['gpu'] or ('Apple Silicon / Metal' if HW['mps'] else t('s_sin_gpu', lang))}",
        f"- **VRAM:** {HW['vram_gb']} GB" if HW["cuda"] else f"- **RAM:** {HW['ram_gb']} GB",
        f"- **{t('nivel', lang)}:** {HW['nivel']} · {t('nivel_' + str(HW['nivel']), lang)}",
        "",
    ]

    # --- Motores, clasificados según TU equipo ---
    # (nombre, ¿listo?, comando de instalación, ¿solo NVIDIA?)
    sv2_extra = (f" · `{HW['seedvr2_modelo']}`" if HW["seedvr2"] else "")
    inst_base = "bash install/instalar_nvidia.sh" if HW["cuda"] else "bash install/instalar_mac.sh"
    motores = [
        (f"SeedVR2 — restauración IA{sv2_extra}", HW["seedvr2"], inst_base, False),
        ("Real-ESRGAN · Real-CUGAN · waifu2x · RIFE (Vulkan)", HW["vulkan"], inst_base, False),
    ]
    if HW["mps"]:  # nativos de Apple Silicon (MLX / MetalFX)
        motores.insert(1, ("SeedVR2 (MLX) — nativo Apple Silicon, rápido",
                           seedvr2_mlx.disponible(), "bash install/extras_mlx.sh", False))
        motores.insert(2, ("Real-ESRGAN x4 (MLX) — rápido (BSD)",
                           realesrgan_mlx.disponible(), "bash install/extras_realesrgan_mlx.sh", False))
        motores.insert(3, ("MetalFX — escalado rápido de video (Apple)",
                           metalfx.disponible(), "bash install/extras_metalfx.sh", False))
    motores += [
        ("DDColor — colorizar B/N", color.disponible(), "bash install/extras_color.sh", False),
        ("FaithDiff — restauración fiel (MIT)", faithdiff.disponible(),
         "bash install/extras_faithdiff.sh", True),
        ("DiffBIR — caras + escena (Apache-2.0)", diffbir.disponible(),
         "bash install/extras_diffbir.sh", True),
        ("PMRF — caras (MIT)", pmrf.disponible(),
         "bash install/extras_pmrf.sh", True),
        ("InstantIR — restauración instantánea", instantir.disponible(),
         "bash install/extras_instantir.sh", True),
        ("FlashVSR — modo rápido", HW["flashvsr"] and flashvsr.disponible(),
         "bash install/extras_flashvsr.sh", True),
        ("Restormer — deblur / lluvia / ruido (MIT)", restormer.disponible(),
         "bash install/extras_restormer.sh", True),
        ("Retinexformer — poca luz (MIT)", retinexformer.disponible(),
         "bash install/extras_retinexformer.sh", True),
        ("DreamClear — restauración real máx. (Apache-2.0)", dreamclear.disponible(),
         "bash install/extras_dreamclear.sh", True),
        ("HAT — super-resolución nítida (Apache-2.0)", hat.disponible(),
         "bash install/extras_hat.sh", True),
        ("Practical-RIFE — slow-mo / interpolación (MIT)", practical_rife.disponible(),
         "bash install/extras_practical_rife.sh", False),
        ("FILM — slow-mo movimiento grande (Apache-2.0)", film.disponible(),
         "bash install/extras_film.sh", True),
        ("EMA-VFI — interpolación SOTA (Apache-2.0)", ema_vfi.disponible(),
         "bash install/extras_ema_vfi.sh", True),
        ("NAFNet — denoise/deblur (MIT)", nafnet.disponible(),
         "bash install/extras_nafnet.sh", False),
        ("SCUNet — denoise ciego (Apache-2.0)", scunet.disponible(),
         "bash install/extras_scunet.sh", False),
        ("FBCNN — quitar artefactos JPEG (Apache-2.0)", fbcnn.disponible(),
         "bash install/extras_fbcnn.sh", False),
        ("FFTformer — deblur de movimiento (MIT)", fftformer.disponible(),
         "bash install/extras_fftformer.sh", True),
        ("DehazeFormer — quitar neblina (MIT)", dehazeformer.disponible(),
         "bash install/extras_dehazeformer.sh", False),
        ("HVI-CIDNet — poca luz premium (MIT)", hvi_cidnet.disponible(),
         "bash install/extras_hvi_cidnet.sh", False),
        ("DarkIR — noche extrema, luz+ruido+desenfoque (MIT)", darkir.disponible(),
         "bash install/extras_darkir.sh", False),
        ("InSPyReNet — quitar fondo / matting (MIT)", inspyrenet.disponible(),
         "bash install/extras_inspyrenet.sh", False),
        ("BiRefNet — quitar fondo alta resolución (MIT)", birefnet.disponible(),
         "bash install/extras_birefnet.sh", False),
        ("RestoreFormer++ — caras (Apache-2.0)", restoreformerpp.disponible(),
         "bash install/extras_restoreformerpp.sh", False),
        ("DSRNet — quitar reflejos (Apache-2.0)", dsrnet.disponible(),
         "bash install/extras_dsrnet.sh", False),
        ("ShadowFormer — quitar sombras (MIT)", shadowformer.disponible(),
         "bash install/extras_shadowformer.sh", False),
        ("DUT — estabilización por IA (MIT)", dut_stab.disponible(),
         "bash install/extras_dut_stab.sh", True),
        ("IC-Light — reiluminación / relighting (Apache-2.0)", iclight.disponible(),
         "bash install/extras_iclight.sh", True),
        ("IOPaint+LaMa — borrar objetos con máscara (Apache-2.0)", iopaint_lama.disponible(),
         "bash install/extras_iopaint_lama.sh", False),
    ]
    # Motores de caras NO comerciales: ocultos en el build que se vende; solo con
    # VB_NO_COMERCIAL=1 (uso personal). Reemplazo comercial = RestoreFormer++/PMRF.
    if INCLUIR_NO_COMERCIAL:
        motores += [
            ("CodeFormer — caras ⚠️ S-Lab NO comercial (uso personal)",
             faces.disponible(), "bash install/extras_caras.sh", False),
            ("OSDFace — caras ⚠️ sin licencia (uso personal)", osdface.disponible(),
             "bash install/extras_osdface.sh", True),
        ]
    listos, instalables, no_aplican = [], [], []
    for nombre, ok, inst, solo_nvidia in motores:
        if ok:
            listos.append(f"- ✅ **{nombre}**")
        elif solo_nvidia and not HW["cuda"]:
            no_aplican.append(f"- **{nombre}** — {t('s_requiere_nvidia', lang)}")
        else:
            instalables.append((nombre, inst))

    filas.append(f"### {t('s_listos', lang)}")
    filas += listos or [t("s_nada_listo", lang)]

    if instalables:
        filas += ["", f"### {t('s_instalables', lang)}", t("s_instalar_intro", lang)]
        for nombre, inst in instalables:
            filas.append(f"- **{nombre}**\n  `{inst}`")

    if no_aplican:
        filas += ["", f"### {t('s_no_aplican', lang)}"] + no_aplican

    filas += ["", t("combo", lang)]
    lic = licencias.activa()
    if licencias.requiere_licencia() and lic:
        filas.append(f"\n🔑 {t('lic_activada', lang)} **{lic.get('cliente', '?')}**")
    return "\n".join(filas)


def texto_acerca(lang):
    """Rubro 'Acerca de': versión y licencias de los motores incluidos."""
    return "\n".join([
        f"**PixelBooster** · v{VERSION}",
        "",
        t("aj_acerca_intro", lang),
        "",
        f"### {t('aj_acerca_lic', lang)}",
        "- FaithDiff — **MIT**",
        "- SeedVR2 · FlashVSR · InstantIR · DDColor · DiffBIR — **Apache-2.0**",
        "- PMRF — **MIT**",
        "- Real-ESRGAN · Real-CUGAN · waifu2x · RIFE (Vulkan) — **BSD/MIT**",
        "- CodeFormer — NTU S-Lab (" + t("aj_acerca_revisar", lang) + ")",
    ])


def motores_video():
    sv2 = ["seedvr2"] if HW["seedvr2"] else []
    mlx = ["seedvr2_mlx"] if (seedvr2_mlx.disponible() and HW["mps"]) else []
    mfx = ["metalfx"] if (metalfx.disponible() and HW["mps"]) else []
    vk = ["realesrgan", "realcugan", "waifu2x", "rife"] if HW["vulkan"] else []
    # En NVIDIA SeedVR2 (PyTorch) es rápido → va primero (mejor calidad por defecto).
    # En Mac (MPS) SeedVR2-PyTorch es lentísimo → Real-ESRGAN va primero (default
    # usable); luego SeedVR2-MLX (calidad alta), MetalFX (escalado rápido no-IA) y
    # el SeedVR2-PyTorch lento queda al final.
    m = (sv2 + vk) if HW["cuda"] else (vk + mlx + mfx + sv2)
    if HW["flashvsr"] and flashvsr.disponible():
        m.append("flashvsr")
    # Motores de interpolación de frames (slow-mo); aparecen si están instalados.
    for vfi, mod in (("practical_rife", practical_rife), ("film", film),
                     ("ema_vfi", ema_vfi), ("dut_stab", dut_stab)):
        if mod.disponible():
            m.append(vfi)
    return m or ["realesrgan"]  # que la UI nunca quede vacía


def filtros_video():
    """Filtros de post-proceso (FFmpeg) que se aplican AL RESULTADO ya mejorado,
    antes de descargar: revelado/LUT, grano, desentrelazar, ruido, estabilizar."""
    if not HW["ffmpeg"]:
        return []
    f = ["lut", "grano", "desentrelazar", "denoise", "limpiar", "cine", "lente", "ia"]
    if filtros.ESTABILIZA_OK:   # vidstab (2 pasadas) o deshake (integrado)
        f.append("estabilizar")
    return f


def motores_imagen():
    m = []
    if faithdiff.disponible():
        m.append("faithdiff")  # recomendado por defecto (MIT, supera a SUPIR)
    if seedvr2_mlx.disponible() and HW["mps"]:
        m.append("seedvr2_mlx_img")  # SeedVR2 nativo Apple Silicon (MLX)
    if realesrgan_mlx.disponible() and HW["mps"]:
        m.append("realesrgan_mlx_img")  # Real-ESRGAN x4 nativo MLX (BSD)
    if diffbir.disponible():
        m.append("diffbir")    # caras + escena, Apache-2.0
    if pmrf.disponible():
        m.append("pmrf")       # caras alineadas, MIT
    if HW["seedvr2"]:
        m.append("seedvr2_img")
    if instantir.disponible():
        m.append("instantir")
    if faces.disponible() and INCLUIR_NO_COMERCIAL:
        m.append("codeformer")  # S-Lab NO comercial → oculto salvo VB_NO_COMERCIAL=1
    if osdface.disponible() and INCLUIR_NO_COMERCIAL:
        m.append("osdface")    # ⚠️ sin licencia → oculto salvo VB_NO_COMERCIAL=1
    if restormer.disponible():
        m.append("restormer")  # deblur / lluvia / ruido real, MIT
    if retinexformer.disponible():
        m.append("retinexformer")  # poca luz / noche, MIT
    if hat.disponible():
        m.append("hat")        # super-resolución nítida no-difusión, Apache-2.0
    if dreamclear.disponible():
        m.append("dreamclear")  # restauración real máxima calidad, Apache-2.0
    # Restauración / limpieza por imagen (roadmap; ambas salvo fftformer)
    for mid, mod in (("nafnet", nafnet), ("scunet", scunet), ("fbcnn", fbcnn),
                     ("fftformer", fftformer), ("dehazeformer", dehazeformer),
                     ("hvi_cidnet", hvi_cidnet), ("darkir", darkir),
                     ("inspyrenet", inspyrenet), ("birefnet", birefnet),
                     ("restoreformerpp", restoreformerpp), ("dsrnet", dsrnet),
                     ("shadowformer", shadowformer), ("iclight", iclight)):
        if mod.disponible():
            m.append(mid)
    if color.disponible():
        m.append("ddcolor")
    if HW["vulkan"]:
        m.append("realesrgan_img")
    if HW["ffmpeg"]:
        m += ["lut", "grano"]
    return m or ["realesrgan_img"]


# Motores que de verdad mejoran (suben resolución / reconstruyen detalle). Los
# filtros FFmpeg (color, grano, limpieza) NO entran aquí: ayudan a comunicar al
# usuario cuándo la máquina solo tiene filtros y aún le falta instalar la IA.
_MEJORADORES_VIDEO = {"seedvr2", "seedvr2_mlx", "realesrgan", "realcugan",
                      "waifu2x", "flashvsr"}
_MEJORADORES_IMG = {"faithdiff", "seedvr2_img", "instantir", "codeformer",
                    "realesrgan_img", "diffbir", "pmrf", "osdface", "seedvr2_mlx_img",
                    "realesrgan_mlx_img", "restormer", "retinexformer", "dreamclear",
                    "hat", "nafnet", "scunet", "fbcnn", "fftformer", "dehazeformer",
                    "hvi_cidnet", "darkir", "inspyrenet", "birefnet",
                    "restoreformerpp", "dsrnet", "shadowformer", "iclight"}
# Motores que escalan a una resolución/escala (para la vista previa de tamaño).
_ESCALADORES = {"seedvr2", "seedvr2_mlx", "flashvsr", "realesrgan", "realcugan",
                "waifu2x", "metalfx"}


def _hay_mejorador_video() -> bool:
    return any(m in _MEJORADORES_VIDEO for m in motores_video())


def _hay_mejorador_imagen() -> bool:
    return any(m in _MEJORADORES_IMG for m in motores_imagen())


def _como_instalar(lang) -> str:
    return t("como_instalar_nvidia" if HW["cuda"] else "como_instalar_mac", lang)


def _nota_video(motor, lang):
    """Nota del motor; antepone un aviso si SeedVR2 va a correr en Mac (MPS)."""
    nota = t(MOTORES_VIDEO_NOTAS[motor], lang)
    if motor == "seedvr2" and HW["mps"] and not HW["cuda"]:
        nota = t("n_seedvr2_mac_lento", lang) + "\n\n" + nota
    return nota


# ---------------------------------------------------------------- interfaz

# Gradio 6 movió theme/css/js del constructor de Blocks() al método launch();
# en 4.x/5.x van en el constructor. Detectamos la versión para que la UI cálida,
# el modo oscuro y el comparador se apliquen en cualquier instalación.
_GR6 = int(gr.__version__.split(".")[0]) >= 6
_APARIENCIA = dict(theme=ui_theme.TEMA, css=ui_theme.CSS, js=_JS_CARGA)

with gr.Blocks(title="PixelBooster", **({} if _GR6 else _APARIENCIA)) as demo:
    idioma = gr.Radio(IDIOMAS, value=idioma_por_defecto(), show_label=False,
                      container=False, elem_id="vb-lang", scale=0)
    # Cambia al activar la licencia para que la UI completa se re-renderice.
    lic_tick = gr.State(0)

    @gr.render(inputs=[idioma, lic_tick])
    def ui(lang, _tick):
        # El título "PixelBooster" ahora es un logo integrado en la barra de
        # pestañas (CSS .tab-nav::before en ui_theme), así que no hay cabecera.

        # --- Activación (solo si la build exige licencia y no está activada) ---
        if licencias.requiere_licencia() and not licencias.activa():
            with gr.Column():
                gr.Markdown(f"## {t('lic_titulo', lang)}\n{t('lic_texto', lang)}")
                clave_in = gr.Textbox(label=t("lic_clave", lang), lines=2)
                lic_msg = gr.Markdown()
                boton_lic = gr.Button(t("lic_boton", lang), variant="primary",
                                      elem_classes="cta")

            def intentar_activar(clave, tick):
                try:
                    licencias.activar(clave or "")
                    return "", tick + 1
                except ValueError:
                    return t("lic_error", lang), tick

            boton_lic.click(intentar_activar, [clave_in, lic_tick],
                            [lic_msg, lic_tick])
            return  # no se construye el resto de la app sin licencia

        def grupo_grano(visible):
            """Controles del grano analógico (compartidos por video e imagen)."""
            with gr.Group(visible=visible) as g:
                preset = gr.Dropdown([(t("g_" + p, lang), p) for p in GRANO_PRESETS],
                                     value="clasico", label=t("g_preset", lang))
                i0, t0, c0 = grano.PRESETS["clasico"]
                inten = gr.Slider(0.02, 1.0, value=i0, step=0.01,
                                  label=t("g_intensidad", lang))
                tam = gr.Slider(1, 4, value=t0, step=1, label=t("g_tamano", lang))
                col = gr.Checkbox(value=c0, label=t("g_color", lang))

            def sincronizar(p):
                i, tm, c = grano.PRESETS[p]
                return gr.update(value=i), gr.update(value=tm), gr.update(value=c)

            preset.change(sincronizar, preset, [inten, tam, col])
            return g, preset, inten, tam, col

        def grupo_revelado(visible, fuente=None, pos=None, es_video=False):
            """Panel de revelado estilo Lumetri con presets save/load.

            Devuelve el grupo y la lista plana de 24 componentes
            (orden: lut1,mix1,lut2,mix2,lut3,mix3 + 18 ajustes Lumetri).

            Si `fuente` (el medio ya cargado: video_out o img_in) se pasa, dentro de
            los looks se añade el comparador de LUTs sobre ese medio (sin subir nada):
            en video usa el frame donde el usuario paró la barra (`pos` + JS).
            """
            opciones = [(t("l_ninguno", lang), "ninguno")] + \
                       [(n, k) for k, n in luts.NOMBRES.items()]
            comps = []  # 24 componentes en orden plano (_PRESET_KEYS)
            with gr.Group(visible=visible) as g:
                # ---- presets: en un acordeón colapsado para no estorbar ----
                with gr.Accordion(t("preset_seccion", lang), open=False):
                    preset_selector = gr.Dropdown(
                        _listar_presets_revelado(), label=t("preset_cargar", lang),
                        value=None, interactive=True, container=True)
                    with gr.Row(equal_height=True):
                        preset_nombre = gr.Textbox(label=t("preset_nombre", lang),
                                                   scale=3, container=True)
                        preset_guardar_btn = gr.Button(t("preset_guardar", lang),
                                                       scale=1, size="sm")
                    preset_msg = gr.Markdown("", elem_classes="size-preview")

                # ---- looks ----
                with gr.Accordion(t("l_sec_looks", lang), open=True):
                    for n in range(3):
                        with gr.Row():
                            lk = gr.Dropdown(opciones, scale=2, label=f"LUT {n + 1}",
                                             value="portra400" if n == 0 else "ninguno")
                            mz = gr.Slider(0.0, 1.0, value=1.0, step=0.05, scale=1,
                                           label=t("l_mezcla", lang))
                        comps += [lk, mz]

                def sl(lo, hi, v, paso, clave):
                    comps.append(gr.Slider(lo, hi, value=v, step=paso,
                                           label=t(clave, lang)))

                with gr.Accordion(t("l_sec_basica", lang), open=True):
                    sl(-3.0, 3.0, 0.0, 0.1, "l_exposicion")
                    sl(0.5, 1.6, 1.0, 0.02, "l_contraste")
                    sl(-0.15, 0.15, 0.0, 0.01, "l_altas")
                    sl(-0.15, 0.15, 0.0, 0.01, "l_sombras")
                    sl(-0.15, 0.15, 0.0, 0.01, "l_blancos")
                    sl(-0.15, 0.15, 0.0, 0.01, "l_negros")
                    sl(3000, 10000, 6500, 100, "l_temperatura")
                    sl(-0.3, 0.3, 0.0, 0.01, "l_tinte")
                    sl(0.0, 2.0, 1.0, 0.05, "l_saturacion")
                with gr.Accordion(t("l_sec_creativo", lang), open=False):
                    sl(-2.0, 2.0, 0.0, 0.1, "l_vibranza")
                    sl(-45, 45, 0, 1, "l_matiz")
                    sl(0.0, 1.0, 0.0, 0.05, "l_desvaido")
                    sl(-0.3, 0.3, 0.0, 0.01, "l_tinte_sombras")
                    sl(-0.3, 0.3, 0.0, 0.01, "l_tinte_altas")
                with gr.Accordion(t("l_sec_detalle", lang), open=False):
                    sl(0.0, 3.0, 0.0, 0.1, "l_nitidez")
                    sl(0.0, 1.5, 0.0, 0.05, "l_claridad")
                    sl(0.0, 10.0, 0.0, 0.5, "l_ruido_red")
                    sl(0.0, 1.0, 0.0, 0.05, "l_vineta")

            # ---- lógica presets ----
            def _guardar(nombre, *vals):
                if not nombre or not nombre.strip():
                    return gr.update(), t("preset_sin_nombre", lang)
                d = dict(zip(_PRESET_KEYS, vals))
                (_PRESET_DIR / f"{nombre.strip()}.json").write_text(
                    json.dumps(d, indent=2, ensure_ascii=False))
                return gr.update(choices=_listar_presets_revelado(),
                                 value=nombre.strip()), t("preset_guardado", lang)

            def _cargar(nombre):
                if not nombre:
                    return [gr.update()] * 24
                p = _PRESET_DIR / f"{nombre}.json"
                if not p.exists():
                    return [gr.update()] * 24
                d = json.loads(p.read_text())
                return [gr.update(value=d.get(k, _PRESET_DEFAULTS[i]))
                        for i, k in enumerate(_PRESET_KEYS)]

            preset_guardar_btn.click(
                _guardar, [preset_nombre] + comps,
                [preset_selector, preset_msg])
            preset_selector.change(
                _cargar, preset_selector, comps)

            return g, comps

        with gr.Tab(t("tab_video", lang)):
            ids_v = motores_video()
            if not _hay_mejorador_video():
                gr.Markdown(f"{t('sin_mejorador_v', lang)}\n\n{_como_instalar(lang)}",
                            elem_classes="aviso-sin-motor")
            with gr.Row():
                with gr.Column(elem_classes="col-controls", min_width=300):
                    video_in = gr.Video(label=t("video_entrada", lang), elem_id="vb-input",
                                        sources=["upload"])
                    # Botón de mejorar ARRIBA del selector de motores.
                    with gr.Row():
                        boton_v = gr.Button(t("boton_video", lang), variant="primary",
                                            elem_classes="cta")
                        cancelar_v = gr.Button(t("cancelar", lang), variant="stop",
                                               size="sm")
                    motor_v = gr.Radio([(t("m_" + i, lang), i) for i in ids_v],
                                       value=ids_v[0], label=t("motor", lang),
                                       elem_classes="engine-picker")
                    nota_v = gr.Markdown(_nota_video(ids_v[0], lang),
                                         elem_classes="engine-note")
                    _otros_v = _otros_motores_md(_CAT_VIDEO, ids_v,
                                                 lambda m: t("m_" + m, lang), lang)
                    if _otros_v:
                        gr.Markdown(_otros_v, elem_classes="engine-otros")
                    escala = gr.Slider(2, 4, value=2, step=1, label=t("escala", lang),
                                       visible=ids_v[0] in ("realesrgan", "realcugan", "waifu2x", "metalfx"))
                    ruido = gr.Dropdown([-1, 0, 3], value=0, label=t("ruido", lang), visible=False)
                    mult = gr.Slider(2, 4, value=2, step=1, label=t("mult_fps", lang), visible=False)
                    with gr.Group(visible=ids_v[0] in ("seedvr2", "seedvr2_mlx")) as grupo_sv2:
                        resolucion = gr.Dropdown([720, 1080, 1440, 2160, 4320], value=1080,
                                                 label=t("resolucion_obj", lang))
                        modelo_sv2 = gr.Dropdown(seedvr2.MODELOS, value=HW["seedvr2_modelo"],
                                                 label=t("modelo_auto", lang))
                        batch_sv2 = gr.Dropdown(seedvr2.BATCHES, value=HW["seedvr2_batch"],
                                                label=t("batch", lang))
                    formato_v = gr.Dropdown(
                        [(lbl, val) for lbl, val in _FORMATOS_VIDEO],
                        value=ajustes.formato_video(),
                        label=t("formato_salida_v", lang))
                    gr.Markdown(t("formato_nota", lang), elem_classes="formato-nota")
                    preview = gr.Markdown(elem_classes="size-preview")
                # --- Centro: resultado + comparación por el frame del propio video ---
                with gr.Column(elem_classes="col-stage", min_width=320):
                    video_out = gr.Video(label=t("resultado_preview", lang),
                                         elem_id="vb-result", sources=["upload"])
                    descarga_v = gr.DownloadButton(t("descargar_v", lang), visible=False,
                                                   elem_classes="cta")
                    comparador_v = gr.HTML(label=t("comparador_video", lang))
                    # Posición (fracción 0-1) que el JS rellena con el tiempo actual
                    # del reproductor de resultado/entrada.
                    pos_frac = gr.Number(0.3, visible=False)
                    log_v = gr.Textbox(label=t("progreso", lang), lines=12, max_lines=12,
                                       elem_classes="console")
                    # Barra de avance minimalista, DEBAJO de la consola; solo visible
                    # mientras un proceso corre (la ceden procesar/aplicar).
                    barra_v = gr.HTML("", visible=False, elem_classes="vb-bar-wrap")

                # --- Columna 3: elegir filtro (botón Aplicar ARRIBA) ---
                ids_f = filtros_video()
                # Filtros "simples" (grano/desentrelazar/ruido/estabilizar): sus
                # opciones van JUNTAS en un solo grupo. El revelado (lut) va aparte.
                _SIMPLES = {"grano", "desentrelazar", "denoise", "estabilizar", "limpiar",
                            "cine", "lente", "ia"}
                _CON_CTRL = _SIMPLES | {"lut"}
                with gr.Column(elem_classes="col-aside", min_width=220):
                    gr.Markdown(f"### {t('filtros_titulo', lang)}\n{t('filtros_intro', lang)}",
                                elem_classes="filtros-head")
                    boton_filtro = gr.Button(t("filtros_aplicar", lang), variant="primary",
                                             elem_classes="cta")
                    gr.Markdown(t("filtros_aplicar_nota", lang), elem_classes="formato-nota")
                    filtro_v = gr.Radio([(t("m_" + i, lang), i) for i in ids_f],
                                        value=ids_f[0], label=t("filtros_picker", lang),
                                        elem_classes="engine-picker")
                    nota_filtro = gr.Markdown(t(MOTORES_VIDEO_NOTAS[ids_f[0]], lang),
                                              elem_classes="engine-note")

                # --- Columna 4 (derecha): los AJUSTES del filtro elegido ---
                #     (revelado/LUTs/presets, grano, ruido o estabilizar; se abre
                #     según el filtro seleccionado, igual que el revelado).
                with gr.Column(elem_classes="col-revelado", min_width=300,
                               visible=ids_f[0] in _CON_CTRL) as col_revelado:
                    # Grupo único con TODAS las opciones de los filtros simples.
                    with gr.Group(visible=ids_f[0] in _SIMPLES) as grupo_simples:
                        gr.Markdown(f"**{t('m_grano', lang).split(' — ')[0]}**",
                                    elem_classes="filtros-head")
                        _gg, gpre_v, gint_v, gtam_v, gcol_v = grupo_grano(True)
                        gr.Markdown(f"**{t('m_denoise', lang).split(' — ')[0]}**",
                                    elem_classes="filtros-head")
                        den_luma = gr.Slider(0.0, 10.0, value=3.0, step=0.5, label=t("den_luma", lang))
                        den_croma = gr.Slider(0.0, 10.0, value=2.0, step=0.5, label=t("den_chroma", lang))
                        gr.Markdown(f"**{t('m_estabilizar', lang).split(' — ')[0]}**",
                                    elem_classes="filtros-head")
                        est_suav = gr.Slider(1, 30, value=10, step=1, label=t("est_suavidad", lang))
                        est_zoom = gr.Slider(0.0, 1.0, value=0.3, step=0.05, label=t("est_zoom", lang))
                        gr.Markdown(f"**{t('m_lente', lang).split(' — ')[0]}**",
                                    elem_classes="filtros-head")
                        lente_k1 = gr.Slider(-0.5, 0.5, value=0.0, step=0.01, label=t("lente_k1", lang))
                        lente_k2 = gr.Slider(-0.5, 0.5, value=0.0, step=0.01, label=t("lente_k2", lang))
                        gr.Markdown(f"**{t('m_ia', lang).split(' — ')[0]}**",
                                    elem_classes="filtros-head")
                        ia_modelo = gr.Dropdown(
                            [(t("ia_" + k, lang), k) for k in video_ia.MODELOS],
                            value="ruido", label=t("ia_modelo", lang))
                    grupo_l_v, rev_v = grupo_revelado(
                        ids_f[0] == "lut", fuente=video_out, pos=pos_frac, es_video=True)

            def controles_v(motor):
                return (
                    gr.update(value=_nota_video(motor, lang)),
                    gr.update(visible=motor in ("realesrgan", "realcugan", "waifu2x", "metalfx")),
                    gr.update(visible=motor in ("realcugan", "waifu2x")),
                    gr.update(visible=motor in ("rife", "practical_rife", "film", "ema_vfi")),
                    gr.update(visible=motor in ("seedvr2", "seedvr2_mlx")),
                )

            motor_v.change(controles_v, motor_v,
                           [nota_v, escala, ruido, mult, grupo_sv2])
            for comp in (video_in, motor_v, escala, mult, resolucion):
                comp.change(hacer_vista_previa(lang),
                            [video_in, motor_v, escala, mult, resolucion], preview)
            # Al cargar un video, vuélcalo al reproductor central (#vb-result) para
            # que SIEMPRE haya un video con barra que mover y elegir el frame, aun
            # antes de mejorar. Tras mejorar, el resultado lo reemplaza.
            video_in.change(lambda v: v, video_in, video_out)
            ev_v = boton_v.click(
                hacer_procesar_video(lang),
                [video_in, motor_v, escala, ruido, mult, resolucion, modelo_sv2,
                 batch_sv2, formato_v],
                [log_v, video_out, comparador_v, descarga_v, barra_v])
            cancelar_v.click(fn=None, cancels=[ev_v])

            # --- Filtros (post-proceso): controles, vista previa y aplicar ---
            def controles_filtro(filtro):
                return (
                    gr.update(value=t(MOTORES_VIDEO_NOTAS[filtro], lang)),  # nota
                    gr.update(visible=filtro in _SIMPLES),  # grupo único grano/ruido/estabilizar
                    gr.update(visible=filtro == "lut"),     # panel revelado
                    gr.update(visible=filtro in _CON_CTRL), # 4ª columna (se abre si hay ajustes)
                )

            filtro_v.change(controles_filtro, filtro_v,
                            [nota_filtro, grupo_simples, grupo_l_v, col_revelado])

            # Vista previa EN VIVO del filtro (sin botones): el comparador central se
            # actualiza solo al cambiar de filtro o tocar un LUT/control.
            _prev_in = [pos_frac, video_out, video_in, filtro_v, gpre_v, gint_v,
                        gtam_v, gcol_v, den_luma, den_croma, *rev_v]
            _prev_fn = hacer_preview_filtro(lang)

            def _auto_prev(componente, evento="change"):
                """Engancha el auto-preview (en vivo) a un control del filtro."""
                getattr(componente, evento)(_prev_fn, _prev_in, comparador_v, js=_JS_POS)

            _auto_prev(filtro_v)  # al cambiar de filtro
            # LUTs en vivo: dropdowns (change) y mezclas (release, al soltar).
            for _i, _c in enumerate(rev_v):
                _auto_prev(_c, "change" if _i in (0, 2, 4) else "release")
            # Grano y ruido también en vivo.
            _auto_prev(gpre_v); _auto_prev(gcol_v)
            for _c in (gint_v, gtam_v, den_luma, den_croma):
                _auto_prev(_c, "release")

            boton_filtro.click(
                hacer_aplicar_filtros(lang),
                [video_out, video_in, filtro_v, gpre_v, gint_v, gtam_v, gcol_v,
                 den_luma, den_croma, est_suav, est_zoom, lente_k1, lente_k2,
                 ia_modelo, formato_v, *rev_v],
                [log_v, video_out, comparador_v, descarga_v, barra_v])

        with gr.Tab(t("tab_imagenes", lang)):
            ids_i = motores_imagen()
            etiquetas_i = {"faithdiff": "i_faithdiff",
                           "seedvr2_img": "i_seedvr2", "realesrgan_img": "i_realesrgan",
                           "codeformer": "i_codeformer", "instantir": "i_instantir",
                           "ddcolor": "i_ddcolor", "grano": "m_grano", "lut": "m_lut",
                           "diffbir": "i_diffbir", "pmrf": "i_pmrf", "osdface": "i_osdface",
                           "seedvr2_mlx_img": "i_seedvr2_mlx",
                           "realesrgan_mlx_img": "i_realesrgan_mlx",
                           "restormer": "i_restormer", "retinexformer": "i_retinexformer",
                           "dreamclear": "i_dreamclear", "hat": "i_hat",
                           "nafnet": "i_nafnet", "scunet": "i_scunet",
                           "fbcnn": "i_fbcnn", "fftformer": "i_fftformer",
                           "dehazeformer": "i_dehazeformer", "hvi_cidnet": "i_hvi_cidnet",
                           "darkir": "i_darkir", "inspyrenet": "i_inspyrenet",
                           "birefnet": "i_birefnet", "restoreformerpp": "i_restoreformerpp",
                           "dsrnet": "i_dsrnet", "shadowformer": "i_shadowformer",
                           "iclight": "i_iclight"}
            if not _hay_mejorador_imagen():
                gr.Markdown(f"{t('sin_mejorador_i', lang)}\n\n{_como_instalar(lang)}",
                            elem_classes="aviso-sin-motor")
            with gr.Row():
                with gr.Column(elem_classes="col-controls"):
                    img_in = gr.Image(type="filepath", label=t("imagen_entrada", lang),
                                      sources=["upload", "clipboard"])
                    motor_i = gr.Radio([(t(etiquetas_i[i], lang), i) for i in ids_i],
                                       value=ids_i[0], label=t("motor", lang),
                                       elem_classes="engine-picker")
                    nota_i = gr.Markdown(t(MOTORES_IMG_NOTAS[ids_i[0]], lang),
                                         elem_classes="engine-note")
                    _otros_i = _otros_motores_md(
                        _CAT_IMG, ids_i, lambda m: t(etiquetas_i.get(m, m), lang), lang)
                    if _otros_i:
                        gr.Markdown(_otros_i, elem_classes="engine-otros")
                    prompt_i = gr.Textbox(label=t("prompt", lang), placeholder=t("prompt_ej", lang),
                                          visible=ids_i[0] in IMG_CON_PROMPT)
                    escala_i = gr.Slider(2, 4, value=2, step=1, label=t("escala", lang),
                                         visible=ids_i[0] not in ("seedvr2_img", "instantir",
                                                                  "ddcolor", "grano", "lut",
                                                                  "pmrf", "osdface",
                                                                  "seedvr2_mlx_img",
                                                                  "realesrgan_mlx_img",
                                                                  "restormer", "retinexformer",
                                                                  "hat", "nafnet", "scunet",
                                                                  "fbcnn", "fftformer",
                                                                  "dehazeformer", "hvi_cidnet",
                                                                  "darkir", "inspyrenet",
                                                                  "birefnet", "restoreformerpp",
                                                                  "dsrnet", "shadowformer",
                                                                  "iclight"))
                    resolucion_i = gr.Dropdown([1080, 1440, 2160, 2880, 4320], value=2160,
                                               label=t("resolucion_obj", lang),
                                               visible=ids_i[0] in ("seedvr2_img", "seedvr2_mlx_img"))
                    fidelidad_i = gr.Slider(0.0, 1.0, value=0.7, step=0.1,
                                            label=t("fidelidad", lang),
                                            visible=ids_i[0] == "codeformer")
                    tarea_rest_i = gr.Dropdown(
                        [(t(f"rest_{k.lower()}", lang), k) for k in restormer.TAREAS],
                        value="Motion_Deblurring", label=t("rest_tarea", lang),
                        visible=ids_i[0] == "restormer")
                    grupo_g_i, gpre_i, gint_i, gtam_i, gcol_i = grupo_grano(
                        ids_i[0] == "grano")
                    grupo_l_i, rev_i = grupo_revelado(
                        ids_i[0] == "lut", fuente=img_in, es_video=False)
                    formato_i = gr.Dropdown(
                        [(lbl, val) for lbl, val in _FORMATOS_IMG],
                        value=ajustes.formato_img(),
                        label=t("formato_salida_i", lang))
                    preview_i = gr.Markdown(elem_classes="size-preview")
                    with gr.Row():
                        boton_i = gr.Button(t("boton_imagen", lang), variant="primary",
                                            elem_classes="cta")
                        cancelar_i = gr.Button(t("cancelar", lang), variant="stop",
                                               size="sm")
                # --- Centro: el resultado / comparador ---
                with gr.Column(elem_classes="col-stage"):
                    gr.Markdown(t("arrastra_comparar", lang), elem_classes="size-preview")
                    img_out = gr.HTML()
                    descarga_i = gr.DownloadButton(t("descargar", lang), visible=False,
                                                   elem_classes="cta")
                # --- Derecha: progreso ---
                with gr.Column(elem_classes="col-aside"):
                    log_i = gr.Textbox(label=t("progreso", lang), lines=18, max_lines=18,
                                       elem_classes="console")

            def controles_i(motor):
                return (
                    gr.update(value=t(MOTORES_IMG_NOTAS[motor], lang)),
                    gr.update(visible=motor in IMG_CON_PROMPT),
                    gr.update(visible=motor not in ("seedvr2_img", "instantir",
                                                    "ddcolor", "grano", "lut",
                                                    "pmrf", "osdface", "seedvr2_mlx_img",
                                                    "realesrgan_mlx_img", "restormer",
                                                    "retinexformer", "hat", "nafnet",
                                                    "scunet", "fbcnn", "fftformer",
                                                    "dehazeformer", "hvi_cidnet", "darkir",
                                                    "inspyrenet", "birefnet",
                                                    "restoreformerpp", "dsrnet",
                                                    "shadowformer", "iclight")),
                    gr.update(visible=motor in ("seedvr2_img", "seedvr2_mlx_img")),
                    gr.update(visible=motor == "codeformer"),
                    gr.update(visible=motor == "restormer"),
                    gr.update(visible=motor == "grano"),
                    gr.update(visible=motor == "lut"),
                )

            motor_i.change(controles_i, motor_i,
                           [nota_i, prompt_i, escala_i, resolucion_i, fidelidad_i,
                            tarea_rest_i, grupo_g_i, grupo_l_i])

            _puede_8k_img = (HW["cuda"] and HW["vram_gb"] >= 16) or (HW["mps"] and HW["ram_gb"] >= 48)

            def _preview_imagen(motor, resolucion):
                if motor == "seedvr2_img" and int(resolucion or 0) >= 4320:
                    if _puede_8k_img:
                        return f"{t('obj_8k', lang)} · {t('hw_suficiente', lang)}"
                    mem = (f"{HW['vram_gb']:.0f} GB VRAM" if HW["cuda"]
                           else f"{HW['ram_gb']:.0f} GB RAM")
                    return (f"{t('obj_8k', lang)} · "
                            + t("aviso_8k_insuf", lang) + f" ({mem})")
                return ""

            motor_i.change(_preview_imagen, [motor_i, resolucion_i], preview_i)
            resolucion_i.change(_preview_imagen, [motor_i, resolucion_i], preview_i)

            ev_i = boton_i.click(
                hacer_procesar_imagen(lang),
                [img_in, motor_i, prompt_i, escala_i, resolucion_i, fidelidad_i,
                 tarea_rest_i, gpre_i, gint_i, gtam_i, gcol_i, formato_i, *rev_i],
                [log_i, img_out, descarga_i])
            cancelar_i.click(fn=None, cancels=[ev_i])


        # ---------------------------------------------------------------- Borrar objetos
        with gr.Tab(t("tab_borrar", lang)):
            if not iopaint_lama.disponible():
                gr.Markdown(f"{t('borrar_instalar', lang)}\n\n"
                            f"`bash install/extras_iopaint_lama.sh`",
                            elem_classes="aviso-sin-motor")
            gr.Markdown(t("borrar_intro", lang))
            with gr.Row():
                with gr.Column(elem_classes="col-controls", min_width=420):
                    borrar_editor = gr.ImageEditor(
                        label=t("borrar_lienzo", lang), type="numpy",
                        brush=gr.Brush(colors=["#ffffff"], default_size=28,
                                       color_mode="fixed"),
                        layers=True, sources=["upload", "clipboard"])
                    with gr.Row():
                        boton_borrar = gr.Button(t("borrar_boton", lang),
                                                 variant="primary", elem_classes="cta")
                        cancelar_borrar = gr.Button(t("cancelar", lang),
                                                    variant="stop", size="sm")
                with gr.Column(elem_classes="col-stage", min_width=320):
                    borrar_out = gr.HTML()
                    descarga_borrar = gr.DownloadButton(t("descargar", lang),
                                                        visible=False, elem_classes="cta")
                    log_borrar = gr.Textbox(label=t("progreso", lang), lines=10,
                                            max_lines=10, elem_classes="console")
            ev_b = boton_borrar.click(hacer_borrar(lang), borrar_editor,
                                      [log_borrar, borrar_out, descarga_borrar])
            cancelar_borrar.click(fn=None, cancels=[ev_b])

        # ---------------------------------------------------------------- Galería
        with gr.Tab(t("tab_galeria", lang)):
            def _listar_salidas():
                if not SALIDAS.exists():
                    return [], []
                archivos = sorted(SALIDAS.iterdir(), key=lambda p: p.stat().st_mtime,
                                  reverse=True)
                imgs = [str(p) for p in archivos
                        if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".tif",
                                                ".tiff", ".webp", ".bmp")]
                vids = [p.name for p in archivos
                        if p.suffix.lower() in (".mp4", ".mov", ".webm", ".mkv", ".avi")]
                return imgs, vids

            def _refrescar_galeria():
                imgs, vids = _listar_salidas()
                md = ""
                if vids:
                    md = f"### {t('galeria_videos', lang)}\n" + "\n".join(f"- {v}" for v in vids)
                elif not imgs:
                    md = t("galeria_vacia", lang)
                return imgs or [], md

            def _limpiar_galeria():
                if SALIDAS.exists():
                    for f in SALIDAS.iterdir():
                        try:
                            f.unlink()
                        except Exception:
                            pass
                return [], t("galeria_vacia", lang)

            imgs0, md0 = _refrescar_galeria()
            galeria = gr.Gallery(value=imgs0, label=t("galeria_imagenes", lang),
                                 columns=4, height="auto")
            galeria_md = gr.Markdown(md0)
            with gr.Row():
                btn_refrescar = gr.Button(t("galeria_refrescar", lang), size="sm")
                btn_limpiar = gr.Button(t("galeria_limpiar", lang), variant="stop",
                                        size="sm")
            # Borrado en dos pasos: el primer clic revela el botón de confirmar.
            with gr.Row(visible=False) as fila_confirmar:
                gr.Markdown(t("galeria_confirmar_aviso", lang))
                btn_confirmar = gr.Button(t("galeria_confirmar", lang),
                                          variant="stop", size="sm")
                btn_cancelar_limpiar = gr.Button(t("cancelar", lang), size="sm")

            btn_refrescar.click(_refrescar_galeria, None, [galeria, galeria_md])
            btn_limpiar.click(lambda: gr.update(visible=True), None, fila_confirmar)
            btn_cancelar_limpiar.click(lambda: gr.update(visible=False), None,
                                       fila_confirmar)
            btn_confirmar.click(_limpiar_galeria, None, [galeria, galeria_md]).then(
                lambda: gr.update(visible=False), None, fila_confirmar)

        # ---------------------------------------------------------------- Lote
        with gr.Tab(t("tab_lote", lang)):
            _disp_v = motores_video()
            _MOTORES_LOTE = [m for m in (
                "seedvr2", "realesrgan", "realcugan", "waifu2x", "rife",
                "flashvsr", "desentrelazar", "denoise"
            ) if m in _disp_v]
            with gr.Row():
                with gr.Column():
                    lote_files = gr.File(file_count="multiple",
                                         label=t("lote_archivos", lang))
                    lote_motor = gr.Dropdown(
                        _MOTORES_LOTE,
                        value=_MOTORES_LOTE[0] if _MOTORES_LOTE else "realesrgan",
                        label=t("lote_motor", lang))
                    lote_escala = gr.Slider(2, 4, value=2, step=1,
                                            label=t("lote_escala", lang))
                    lote_res = gr.Dropdown([720, 1080, 1440, 2160], value=1080,
                                           label=t("lote_resolucion", lang))
                    lote_fmt = gr.Dropdown(
                        [(lbl, val) for lbl, val in _FORMATOS_VIDEO],
                        value=ajustes.formato_video(),
                        label=t("formato_salida_v", lang))
                    with gr.Row():
                        lote_btn = gr.Button(t("lote_procesar", lang),
                                             variant="primary", elem_classes="cta")
                        lote_cancelar = gr.Button(t("cancelar", lang),
                                                   variant="stop", size="sm")
                with gr.Column():
                    lote_log = gr.Textbox(label=t("lote_progreso", lang),
                                          lines=20, max_lines=20,
                                          elem_classes="console")

            ev_lote = lote_btn.click(
                hacer_procesar_lote(lang),
                [lote_files, lote_motor, lote_escala, lote_res, lote_fmt],
                lote_log)
            lote_cancelar.click(fn=None, cancels=[ev_lote])

        with gr.Tab(t("tab_ajustes", lang)):
            # Datos para el rubro de Mantenimiento (se calculan antes de pintar
            # las columnas para saber si hay motores gestionables).
            _MANT_NOMBRES = {
                "seedvr2": "SeedVR2 — restauración IA",
                "vulkan": "Real-ESRGAN · Real-CUGAN · waifu2x · RIFE (Vulkan)",
                "codeformer": "CodeFormer — caras",
                "ddcolor": "DDColor — color",
                "seedvr2_mlx": "SeedVR2 (MLX) — Apple Silicon",
                "realesrgan_mlx": "Real-ESRGAN x4 (MLX) — Apple Silicon",
                "metalfx": "MetalFX — escalado rápido (Apple)",
                "diffbir": "DiffBIR — caras + escena (Apache-2.0)",
                "pmrf": "PMRF — caras (MIT)",
                "osdface": "OSDFace — caras ⚠️ sin licencia (pruebas)",
                "flashvsr": "FlashVSR — video rápido (Apache-2.0)",
                "restormer": "Restormer — deblur / lluvia / ruido (MIT)",
                "retinexformer": "Retinexformer — poca luz (MIT)",
                "dreamclear": "DreamClear — restauración real (Apache-2.0)",
                "hat": "HAT — super-resolución nítida (Apache-2.0)",
                "practical_rife": "Practical-RIFE — slow-mo / interpolación (MIT)",
                "film": "FILM — slow-mo movimiento grande (Apache-2.0)",
                "ema_vfi": "EMA-VFI — interpolación SOTA (Apache-2.0)",
                "nafnet": "NAFNet — denoise / deblur (MIT)",
                "scunet": "SCUNet — denoise ciego (Apache-2.0)",
                "fbcnn": "FBCNN — quitar artefactos JPEG (Apache-2.0)",
                "fftformer": "FFTformer — deblur de movimiento (MIT)",
                "dehazeformer": "DehazeFormer — quitar neblina (MIT)",
                "hvi_cidnet": "HVI-CIDNet — poca luz premium (MIT)",
                "darkir": "DarkIR — noche extrema (MIT)",
                "inspyrenet": "InSPyReNet — quitar fondo (MIT)",
                "birefnet": "BiRefNet — quitar fondo HR (MIT)",
                "restoreformerpp": "RestoreFormer++ — caras (Apache-2.0)",
                "dsrnet": "DSRNet — quitar reflejos (Apache-2.0)",
                "shadowformer": "ShadowFormer — quitar sombras (MIT)",
                "dut_stab": "DUT — estabilización por IA (MIT)",
                "iclight": "IC-Light — reiluminación (Apache-2.0)",
                "iopaint_lama": "IOPaint+LaMa — borrar objetos (Apache-2.0)",
            }
            # Motores de difusión SD → en la práctica solo NVIDIA; en Mac se
            # muestran en mantenimiento solo si ya están instalados.
            _MANT_NVIDIA = {"diffbir", "pmrf", "osdface", "flashvsr",
                            "restormer", "retinexformer", "dreamclear", "hat",
                            "film", "ema_vfi", "fftformer", "dut_stab", "iclight"}

            def _mant_aplica(m):
                if m == "seedvr2":
                    return HW["mps"] or HW["cuda"]
                if m in ("seedvr2_mlx", "realesrgan_mlx", "metalfx"):
                    return HW["mps"]  # MLX / MetalFX solo en Apple Silicon
                if m in _MANT_NVIDIA:
                    return HW["cuda"] or mantenimiento.ubicacion(m)["existe"]
                return True  # vulkan, codeformer, ddcolor sirven en cualquier equipo

            _gestionables = [m for m in mantenimiento.MOTORES if _mant_aplica(m)]

            @contextlib.contextmanager
            def _seccion(titulo):
                """Tarjeta de sección (no colapsable): título + contenido."""
                with gr.Group(elem_classes="aj-card"):
                    gr.Markdown("### " + titulo)
                    yield

            # Tres columnas siempre desplegadas; cada sección muestra todo.
            with gr.Row(elem_classes="aj-cols", equal_height=False):
                # ───────── Columna IZQUIERDA: Idioma · Apariencia · Salida · Equipo ─────────
                with gr.Column():
                    with _seccion("🌐 " + t("aj_idioma", lang)):
                        idioma_sel = gr.Radio(IDIOMAS, value=lang, show_label=False,
                                              container=False, elem_classes="aj-idioma")
                        # Espejo del selector real (disparador de @gr.render, oculto
                        # arriba). .input → solo cuando el usuario elige.
                        idioma_sel.input(lambda v: v, idioma_sel, idioma)
                    with _seccion(t("ap_titulo", lang)):
                        gr.HTML(picker_temas_html(lang))
                        gr.HTML(picker_fuentes_html(lang))
                    with _seccion("📁 " + t("aj_salida", lang)):
                        gr.Markdown(t("aj_salida_intro", lang))
                        aj_fmt_v = gr.Dropdown(
                            [(lbl, val) for lbl, val in _FORMATOS_VIDEO],
                            value=ajustes.formato_video(), label=t("formato_salida_v", lang))
                        aj_fmt_i = gr.Dropdown(
                            [(lbl, val) for lbl, val in _FORMATOS_IMG],
                            value=ajustes.formato_img(), label=t("formato_salida_i", lang))
                        aj_msg = gr.Markdown(elem_classes="formato-nota")

                        def _guardar_fmt_v(v):
                            ajustes.guardar(formato_video=v)
                            return "✓ " + t("aj_guardado", lang)

                        def _guardar_fmt_i(v):
                            ajustes.guardar(formato_img=v)
                            return "✓ " + t("aj_guardado", lang)

                        aj_fmt_v.change(_guardar_fmt_v, aj_fmt_v, aj_msg)
                        aj_fmt_i.change(_guardar_fmt_i, aj_fmt_i, aj_msg)

                    with _seccion("🖥️ " + t("aj_equipo", lang)):
                        gr.Markdown(f"#### {gpu_resumen(lang)}")
                        gr.Markdown(texto_sistema(lang))
                        gr.Markdown(texto_niveles(lang))
                        gr.Markdown(texto_requisitos(lang))

                # ───────── Columna DERECHA: Guía · Mantenimiento · Licencia · Acerca ─────────
                with gr.Column():
                    with _seccion("📖 " + t("aj_guia", lang)):
                        gr.Markdown(t("aj_guia_txt", lang))

                    if _gestionables:
                        with _seccion("🔧 " + t("mant_titulo", lang)):
                            gr.Markdown(t("mant_intro", lang))
                            mant_log = gr.Textbox(label=t("mant_log", lang), lines=8,
                                                  max_lines=8, elem_classes="console",
                                                  visible=False)

                            def _hacer_mant(funcion, motor):
                                def correr_mant():
                                    log = []
                                    yield gr.update(value="", visible=True)
                                    for linea in funcion(motor):
                                        log.append(linea)
                                        yield gr.update(value="\n".join(log[-200:]),
                                                        visible=True)
                                return correr_mant

                            def _hacer_abrir(motor):
                                def abrir():
                                    return gr.update(value=mantenimiento.abrir_carpeta(motor),
                                                     visible=True)
                                return abrir

                            for _m in _gestionables:
                                _u = mantenimiento.ubicacion(_m)
                                _detalle = _u["tamano"] if _u["existe"] else t("mant_no_descargado", lang)
                                gr.Markdown(
                                    f"**{_MANT_NOMBRES[_m]}**  \n"
                                    f"{t('mant_ubic', lang)}: `{_u['ruta']}` · {_detalle}",
                                    elem_classes="mant-info")
                                with gr.Row():
                                    _btn_open = gr.Button(t("mant_abrir", lang), size="sm")
                                    _btn_re = gr.Button(t("mant_redescargar", lang), size="sm")
                                    _btn_ver = gr.Button(t("mant_comprobar", lang), size="sm")
                                _btn_open.click(_hacer_abrir(_m), None, mant_log)
                                _btn_re.click(_hacer_mant(mantenimiento.redescargar, _m), None, mant_log)
                                _btn_ver.click(_hacer_mant(mantenimiento.comprobar, _m), None, mant_log)

                    if licencias.requiere_licencia():
                        with _seccion("🔑 " + t("aj_licencia", lang)):
                            _lic = licencias.activa()
                            if _lic:
                                gr.Markdown(f"🔑 {t('lic_activada', lang)} **{_lic.get('cliente', '?')}**")
                            else:
                                gr.Markdown(t("lic_texto", lang))

                    with _seccion("ℹ️ " + t("aj_acerca", lang)):
                        gr.Markdown(texto_acerca(lang))


if __name__ == "__main__":
    demo.launch(inbrowser=True, **(_APARIENCIA if _GR6 else {}))
