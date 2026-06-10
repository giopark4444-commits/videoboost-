"""VideoBoost — mejora de videos e imágenes con IA, 100% local.

Interfaz Gradio multilingüe (español / English / français). Detecta el hardware
al arrancar y solo ofrece los motores que pueden funcionar en esta máquina
(Mac con chip M o PC con NVIDIA; cualquier otra GPU se queda con los motores
Vulkan). La UI se regenera completa al cambiar de idioma (gr.render).
"""

import base64
import io
import traceback

import gradio as gr

import hardware
import ui_theme
from engines import ffmpeg_utils as ff
from engines import (color, faces, faithdiff, flashvsr, grano, instantir, luts,
                     seedvr2, vulkan)
from i18n import IDIOMAS, idioma_por_defecto, t

HW = hardware.info_sistema()

# ids internos estables; las etiquetas visibles salen de i18n
MOTORES_VIDEO_NOTAS = {
    "seedvr2": "n_seedvr2", "realesrgan": "n_realesrgan", "realcugan": "n_realcugan",
    "waifu2x": "n_waifu2x", "rife": "n_rife", "flashvsr": "n_flashvsr",
    "grano": "n_grano", "lut": "n_lut",
}
MOTORES_IMG_NOTAS = {
    "faithdiff": "n_faithdiff", "seedvr2_img": "n_seedvr2_img",
    "realesrgan_img": "n_realesrgan_img", "codeformer": "n_codeformer",
    "instantir": "n_instantir", "ddcolor": "n_ddcolor", "grano": "n_grano",
    "lut": "n_lut",
}
# Presets de grano analógico (etiqueta i18n ↔ id de engines/grano.py)
GRANO_PRESETS = ["fino", "clasico", "alta_iso", "super8", "bn_plata"]
# Motores de imagen que aceptan un prompt opcional.
IMG_CON_PROMPT = ("faithdiff", "instantir")


def motores_video():
    m = []
    if HW["seedvr2"]:
        m.append("seedvr2")
    if HW["vulkan"]:
        m += ["realesrgan", "realcugan", "waifu2x", "rife"]
    if HW["flashvsr"] and flashvsr.disponible():
        m.append("flashvsr")
    if HW["ffmpeg"]:
        m += ["lut", "grano"]
    return m or ["realesrgan"]  # que la UI nunca quede vacía


def motores_imagen():
    m = []
    if faithdiff.disponible():
        m.append("faithdiff")  # recomendado por defecto (MIT, supera a SUPIR)
    if HW["seedvr2"]:
        m.append("seedvr2_img")
    if instantir.disponible():
        m.append("instantir")
    if faces.disponible():
        m.append("codeformer")
    if color.disponible():
        m.append("ddcolor")
    if HW["vulkan"]:
        m.append("realesrgan_img")
    if HW["ffmpeg"]:
        m += ["lut", "grano"]
    return m or ["realesrgan_img"]


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
        # No rompemos el flujo: el archivo ya está en salidas/ y el botón de
        # descarga funciona; avisamos en vez de dejar el panel en blanco.
        return (f'<p style="color:var(--vb-muted,#7c776d)">{t("listo", lang)} — '
                f'{despues}</p>')
    return (
        '<div class="ba-cmp" style="--pos:50%">'
        f'<img class="ba-after" src="{d}">'
        f'<img class="ba-before" src="{a}" '
        'style="clip-path:inset(0 calc(100% - var(--pos)) 0 0)">'
        '<div class="ba-line"></div>'
        f'<span class="ba-tag ba-l">{t("antes", lang)}</span>'
        f'<span class="ba-tag ba-r">{t("despues", lang)}</span>'
        '<input type="range" min="0" max="100" value="50" '
        "oninput=\"this.parentNode.style.setProperty('--pos', this.value+'%')\">"
        '</div>'
    )


# ---------------------------------------------------------------- lógica

# Orden plano del panel de revelado (debe coincidir con grupo_revelado).
_CLAVES_REVELADO = (
    "exposicion", "contraste", "altas", "sombras", "blancos", "negros",
    "temperatura", "tinte", "saturacion",
    "vibranza", "matiz", "desvaido", "tinte_sombras", "tinte_altas",
    "nitidez", "claridad", "ruido", "vineta",
)


def _revelar(entrada, es_video, rev):
    """Convierte los valores planos del panel (3 LUTs + ajustes) en etalonar()."""
    l1, m1, l2, m2, l3, m3, *ajustes = rev
    return luts.etalonar(
        entrada, es_video=es_video, looks=[(l1, m1), (l2, m2), (l3, m3)],
        **{k: float(v) for k, v in zip(_CLAVES_REVELADO, ajustes)},
    )

def _consumir(gen, log):
    """Consume el generador del motor cediendo el log acumulado; captura su retorno."""
    while True:
        try:
            linea = next(gen)
        except StopIteration as fin:
            return fin.value
        log.append(linea)
        yield "\n".join(log[-400:])


def hacer_procesar_video(lang):
    def procesar(video, motor, escala, ruido, mult, resolucion, modelo, batch,
                 g_preset, g_int, g_tam, g_color, *rev):
        if not video:
            yield t("sube_video", lang), None
            return
        log = [f"▶ {motor}"]
        try:
            if motor == "seedvr2":
                gen = seedvr2.mejorar(video, resolucion=int(resolucion), modelo=modelo,
                                      batch_size=int(batch), es_video=True)
            elif motor == "rife":
                gen = vulkan.interpolar_video(video, mult=int(mult))
            elif motor == "flashvsr":
                gen = flashvsr.mejorar(video)
            elif motor == "grano":
                gen = grano.aplicar(video, es_video=True, preset=g_preset,
                                    intensidad=float(g_int), tamano=int(g_tam),
                                    grano_color=bool(g_color))
            elif motor == "lut":
                gen = _revelar(video, es_video=True, rev=rev)
            else:
                gen = vulkan.mejorar_video(video, motor=motor, escala=int(escala),
                                           ruido=int(ruido))
            consumo = _consumir(gen, log)
            salida = None
            while True:
                try:
                    yield next(consumo), None
                except StopIteration as fin:
                    salida = fin.value
                    break
            log.append(f"{t('listo', lang)}: {salida}")
            yield "\n".join(log[-400:]), salida
        except Exception as e:
            log += ["", f"{t('error', lang)}: {e}", traceback.format_exc(limit=3)]
            yield "\n".join(log[-400:]), None

    return procesar


def hacer_procesar_imagen(lang):
    def procesar(imagen, motor, prompt, escala, resolucion, fidelidad,
                 g_preset, g_int, g_tam, g_color, *rev):
        oculto = gr.update(visible=False)
        if not imagen:
            yield t("sube_imagen", lang), "", oculto
            return
        log = [f"▶ {motor}"]
        try:
            if motor == "faithdiff":
                gen = faithdiff.mejorar(imagen, prompt=prompt or "", escala=int(escala))
            elif motor == "seedvr2_img":
                gen = seedvr2.mejorar(imagen, resolucion=int(resolucion), es_video=False)
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
            log.append(f"{t('listo', lang)}: {salida}")
            yield ("\n".join(log[-400:]), comparador_html(imagen, salida, lang),
                   gr.update(value=salida, visible=True))
        except Exception as e:
            log += ["", f"{t('error', lang)}: {e}", traceback.format_exc(limit=3)]
            yield "\n".join(log[-400:]), "", oculto

    return procesar


def hacer_vista_previa(lang):
    def vista_previa(video, motor, escala, mult, resolucion):
        if not video or not all((escala, mult, resolucion)):
            return ""
        try:
            info = ff.info_video(video)
        except Exception:
            return ""
        w, h = info["ancho"], info["alto"]
        if motor in ("grano", "lut"):
            return f"{w}×{h} {t('se_mantiene', lang)}"
        if motor == "rife":
            return (f"{w}×{h} {t('se_mantiene', lang)} · {info['fps']:.0f} fps → "
                    f"**{info['fps'] * int(mult):.0f} fps**")
        if motor in ("seedvr2", "flashvsr"):
            factor = int(resolucion) / min(w, h)
            nw, nh = round(w * factor / 2) * 2, round(h * factor / 2) * 2
        else:
            nw, nh = w * int(escala), h * int(escala)
        aviso = t("supera_4k", lang) if max(nw, nh) > 4096 else ""
        return f"{w}×{h} → **{nw}×{nh}**{aviso}"

    return vista_previa


def header_html(lang):
    if HW["cuda"]:
        gpu = f"NVIDIA {HW['gpu']} · {HW['vram_gb']} GB VRAM"
    elif HW["mps"]:
        gpu = f"Apple Silicon · {HW['ram_gb']} {t('mem_unificada', lang)}"
    else:
        gpu = t("gpu_generica", lang)
    tier = f"{t('nivel', lang)} {HW['nivel']} · {t('nivel_' + str(HW['nivel']), lang)}"
    return (
        '<div id="vb-header">'
        f'<h1 class="vb-title">{t("titulo", lang)}</h1>'
        f'<p class="vb-sub-text">{t("subtitulo", lang)}</p>'
        '<div class="vb-sub">'
        f'<span class="vb-pill"><span class="vb-dot"></span>{gpu}</span>'
        f'<span class="vb-tier">{tier}</span>'
        '</div></div>'
    )


def texto_sistema(lang):
    sv2 = (f"{t('s_listo_modelo', lang)} `{HW['seedvr2_modelo']}`" if HW["seedvr2"]
           else t("s_no_instalado", lang))
    filas = [
        f"- **{t('s_sistema', lang)}:** {HW['so']}" + (" (Apple Silicon)" if HW["apple_silicon"] else ""),
        f"- **GPU:** {HW['gpu'] or ('Apple Silicon / Metal' if HW['mps'] else t('s_sin_gpu', lang))}",
        f"- **VRAM:** {HW['vram_gb']} GB" if HW["cuda"] else f"- **RAM:** {HW['ram_gb']} GB",
        f"- **Vulkan:** {t('s_instalados', lang) if HW['vulkan'] else t('s_corre_inst', lang)}",
        f"- **SeedVR2:** {sv2}",
        f"- **FaithDiff:** {'✅' if faithdiff.disponible() else t('s_opcional_nvidia', lang)}",
        f"- **InstantIR:** {'✅' if instantir.disponible() else t('s_opcional_nvidia', lang)}",
        f"- **CodeFormer (caras):** {'✅' if faces.disponible() else t('s_opcional', lang)}",
        f"- **DDColor (color):** {'✅' if color.disponible() else t('s_opcional', lang)}",
        f"- **FlashVSR:** {'✅' if HW['flashvsr'] and flashvsr.disponible() else t('s_opcional_nvidia', lang)}",
        "",
        t("combo", lang),
    ]
    return "\n".join(filas)


# ---------------------------------------------------------------- interfaz

with gr.Blocks(title="VideoBoost", theme=ui_theme.TEMA, css=ui_theme.CSS) as demo:
    idioma = gr.Radio(IDIOMAS, value=idioma_por_defecto(), show_label=False,
                      container=False, elem_id="vb-lang", scale=0)

    @gr.render(inputs=idioma)
    def ui(lang):
        gr.HTML(header_html(lang))

        def grupo_grano(visible):
            """Controles del grano analógico (compartidos por video e imagen).
            El preset fija valores de partida; los sliders siempre mandan."""
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

        def grupo_revelado(visible):
            """Panel de revelado estilo Lumetri: 3 capas de LUT + corrección básica.
            Devuelve el grupo y la lista plana de 16 componentes (orden fijo que
            espera el despachador: l1,m1,l2,m2,l3,m3 + 10 ajustes)."""
            opciones = [(t("l_ninguno", lang), "ninguno")] + \
                       [(n, k) for k, n in luts.NOMBRES.items()]
            comps = []
            with gr.Group(visible=visible) as g:
                with gr.Accordion(t("l_sec_looks", lang), open=True):
                    for n in range(3):
                        with gr.Row():
                            lk = gr.Dropdown(opciones, scale=2, label=f"LUT {n + 1}",
                                             value="portra400" if n == 0 else "ninguno")
                            mz = gr.Slider(0.0, 1.0, value=1.0, step=0.05, scale=1,
                                           label=t("l_mezcla", lang))
                        comps += [lk, mz]
                # Orden Lumetri. El despachador (_revelar) desempaqueta esta
                # lista plana: mantener orden y cantidad sincronizados.
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
            return g, comps

        with gr.Tab(t("tab_video", lang)):
            ids_v = motores_video()
            with gr.Row():
                with gr.Column():
                    video_in = gr.Video(label=t("video_entrada", lang))
                    motor_v = gr.Radio([(t("m_" + i, lang), i) for i in ids_v],
                                       value=ids_v[0], label=t("motor", lang),
                                       elem_classes="engine-picker")
                    nota_v = gr.Markdown(t(MOTORES_VIDEO_NOTAS[ids_v[0]], lang),
                                         elem_classes="engine-note")
                    escala = gr.Slider(2, 4, value=2, step=1, label=t("escala", lang),
                                       visible=ids_v[0] in ("realesrgan", "realcugan", "waifu2x"))
                    ruido = gr.Dropdown([-1, 0, 3], value=0, label=t("ruido", lang), visible=False)
                    mult = gr.Slider(2, 4, value=2, step=1, label=t("mult_fps", lang), visible=False)
                    with gr.Group(visible=ids_v[0] == "seedvr2") as grupo_sv2:
                        resolucion = gr.Dropdown([720, 1080, 1440, 2160], value=1080,
                                                 label=t("resolucion_obj", lang))
                        modelo_sv2 = gr.Dropdown(seedvr2.MODELOS, value=HW["seedvr2_modelo"],
                                                 label=t("modelo_auto", lang))
                        batch_sv2 = gr.Dropdown(seedvr2.BATCHES, value=HW["seedvr2_batch"],
                                                label=t("batch", lang))
                    grupo_g_v, gpre_v, gint_v, gtam_v, gcol_v = grupo_grano(
                        ids_v[0] == "grano")
                    grupo_l_v, rev_v = grupo_revelado(ids_v[0] == "lut")
                    preview = gr.Markdown(elem_classes="size-preview")
                    boton_v = gr.Button(t("boton_video", lang), variant="primary",
                                        elem_classes="cta")
                with gr.Column():
                    log_v = gr.Textbox(label=t("progreso", lang), lines=18, max_lines=18,
                                       elem_classes="console")
                    video_out = gr.Video(label=t("resultado", lang))

            def controles_v(motor):
                return (
                    gr.update(value=t(MOTORES_VIDEO_NOTAS[motor], lang)),
                    gr.update(visible=motor in ("realesrgan", "realcugan", "waifu2x")),
                    gr.update(visible=motor in ("realcugan", "waifu2x")),
                    gr.update(visible=motor == "rife"),
                    gr.update(visible=motor == "seedvr2"),
                    gr.update(visible=motor == "grano"),
                    gr.update(visible=motor == "lut"),
                )

            motor_v.change(controles_v, motor_v,
                           [nota_v, escala, ruido, mult, grupo_sv2, grupo_g_v, grupo_l_v])
            for comp in (video_in, motor_v, escala, mult, resolucion):
                comp.change(hacer_vista_previa(lang),
                            [video_in, motor_v, escala, mult, resolucion], preview)
            boton_v.click(hacer_procesar_video(lang),
                          [video_in, motor_v, escala, ruido, mult, resolucion, modelo_sv2,
                           batch_sv2, gpre_v, gint_v, gtam_v, gcol_v, *rev_v],
                          [log_v, video_out])

        with gr.Tab(t("tab_imagenes", lang)):
            ids_i = motores_imagen()
            etiquetas_i = {"faithdiff": "i_faithdiff",
                           "seedvr2_img": "i_seedvr2", "realesrgan_img": "i_realesrgan",
                           "codeformer": "i_codeformer", "instantir": "i_instantir",
                           "ddcolor": "i_ddcolor", "grano": "m_grano", "lut": "m_lut"}
            with gr.Row():
                with gr.Column():
                    img_in = gr.Image(type="filepath", label=t("imagen_entrada", lang))
                    motor_i = gr.Radio([(t(etiquetas_i[i], lang), i) for i in ids_i],
                                       value=ids_i[0], label=t("motor", lang),
                                       elem_classes="engine-picker")
                    nota_i = gr.Markdown(t(MOTORES_IMG_NOTAS[ids_i[0]], lang),
                                         elem_classes="engine-note")
                    prompt_i = gr.Textbox(label=t("prompt", lang), placeholder=t("prompt_ej", lang),
                                          visible=ids_i[0] in IMG_CON_PROMPT)
                    escala_i = gr.Slider(2, 4, value=2, step=1, label=t("escala", lang),
                                         visible=ids_i[0] not in ("seedvr2_img", "instantir",
                                                                  "ddcolor", "grano", "lut"))
                    resolucion_i = gr.Dropdown([1080, 1440, 2160, 2880], value=2160,
                                               label=t("resolucion_obj", lang),
                                               visible=ids_i[0] == "seedvr2_img")
                    fidelidad_i = gr.Slider(0.0, 1.0, value=0.7, step=0.1,
                                            label=t("fidelidad", lang),
                                            visible=ids_i[0] == "codeformer")
                    grupo_g_i, gpre_i, gint_i, gtam_i, gcol_i = grupo_grano(
                        ids_i[0] == "grano")
                    grupo_l_i, rev_i = grupo_revelado(ids_i[0] == "lut")
                    boton_i = gr.Button(t("boton_imagen", lang), variant="primary",
                                        elem_classes="cta")
                with gr.Column():
                    log_i = gr.Textbox(label=t("progreso", lang), lines=14, max_lines=14,
                                       elem_classes="console")
                    gr.Markdown(t("arrastra_comparar", lang), elem_classes="size-preview")
                    img_out = gr.HTML()
                    descarga_i = gr.DownloadButton(t("descargar", lang), visible=False,
                                                   elem_classes="cta")

            def controles_i(motor):
                return (
                    gr.update(value=t(MOTORES_IMG_NOTAS[motor], lang)),
                    gr.update(visible=motor in IMG_CON_PROMPT),
                    gr.update(visible=motor not in ("seedvr2_img", "instantir",
                                                    "ddcolor", "grano", "lut")),
                    gr.update(visible=motor == "seedvr2_img"),
                    gr.update(visible=motor == "codeformer"),
                    gr.update(visible=motor == "grano"),
                    gr.update(visible=motor == "lut"),
                )

            motor_i.change(controles_i, motor_i,
                           [nota_i, prompt_i, escala_i, resolucion_i, fidelidad_i,
                            grupo_g_i, grupo_l_i])
            boton_i.click(hacer_procesar_imagen(lang),
                          [img_in, motor_i, prompt_i, escala_i, resolucion_i, fidelidad_i,
                           gpre_i, gint_i, gtam_i, gcol_i, *rev_i],
                          [log_i, img_out, descarga_i])

        with gr.Tab(t("tab_sistema", lang)):
            gr.Markdown(texto_sistema(lang), elem_classes="sys-card")


if __name__ == "__main__":
    demo.launch(inbrowser=True)
