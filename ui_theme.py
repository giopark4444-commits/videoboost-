"""Sistema de diseño de PixelBooster — estética cálida y minimalista inspirada en
la app de Claude: fondo crema, acento arcilla, mucho aire, tipografía de sistema
(sin fuentes externas, para seguir 100% local), tarjetas limpias y responsive.

Exporta TEMA (gr.themes.Base configurado) y CSS (string que se inyecta en Blocks).
"""

import json

import gradio as gr
from gradio.themes.utils import colors, sizes

# Paleta "arcilla Claude" para el hue primario.
_arcilla = colors.Color(
    name="arcilla",
    c50="#fbf3ef", c100="#f6e2d9", c200="#ecc4b4", c300="#e0a288",
    c400="#d4825f", c500="#c96442", c600="#b5512f", c700="#963f24",
    c800="#6f2f1c", c900="#4a2014", c950="#2a1109",
)

TEMA = gr.themes.Base(
    primary_hue=_arcilla,
    secondary_hue=_arcilla,
    neutral_hue=colors.stone,  # gris cálido, no azulado
    radius_size=sizes.radius_lg,
    text_size=sizes.text_md,
    spacing_size=sizes.spacing_md,
    font=["-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto",
          "Helvetica", "Arial", "sans-serif"],
    font_mono=["ui-monospace", "SFMono-Regular", "Menlo", "Consolas", "monospace"],
).set(
    # Claro
    body_background_fill="#faf9f5",
    body_text_color="#23211d",
    block_background_fill="#ffffff",
    block_border_width="1px",
    block_border_color="#ece7dd",
    block_label_text_color="#7c776d",
    block_title_text_color="#7c776d",
    block_shadow="none",
    block_radius="14px",
    panel_background_fill="#ffffff",
    border_color_primary="#ece7dd",
    input_background_fill="#ffffff",
    input_border_color="#e3ddd1",
    input_border_color_focus="#c96442",
    button_large_radius="12px",
    button_small_radius="10px",
    button_primary_background_fill="#c96442",
    button_primary_background_fill_hover="#b5512f",
    button_primary_text_color="#ffffff",
    button_primary_border_color="#c96442",
    button_secondary_background_fill="#ffffff",
    button_secondary_background_fill_hover="#f5f2ec",
    button_secondary_border_color="#e3ddd1",
    button_secondary_text_color="#3a372f",
    # Oscuro (Claude también tiene modo noche)
    body_background_fill_dark="#262624",
    body_text_color_dark="#ece9e1",
    block_background_fill_dark="#30302e",
    block_border_color_dark="#3c3b38",
    panel_background_fill_dark="#30302e",
    input_background_fill_dark="#2b2b29",
    border_color_primary_dark="#3c3b38",
)


# --- Galería de temas (3 claros + 3 oscuros) ---------------------------------
# Cada tema define una paleta COMPLETA que se aplica en cliente (vía JS) sobre
# document.body, sobreescribiendo tanto las variables propias (--vb-*) como las
# de Gradio (fondo, texto, bordes, botones). Los temas oscuros además activan la
# clase .dark para que los componentes nativos de Gradio se adapten.
# Contraste texto/fondo verificado ≥ 12:1 y texto-tenue/fondo ≥ 5:1 (WCAG AA+):
# las letras nunca se pierden con el fondo.

def _paleta(bg, bg2, surface, surface_hover, elev, border, border_strong,
            text, muted, accent, accent_hover, accent_text, accent_soft):
    return {
        "--vb-bg": bg, "--body-background-fill": bg,
        "--background-fill-primary": bg, "--background-fill-secondary": bg2,
        "--vb-surface": surface, "--block-background-fill": surface,
        "--panel-background-fill": surface, "--input-background-fill": surface,
        "--vb-surface-hover": surface_hover, "--vb-elev": elev,
        "--vb-border": border, "--border-color-primary": border,
        "--block-border-color": border, "--input-border-color": border,
        "--vb-border-strong": border_strong,
        "--vb-text": text, "--body-text-color": text,
        "--vb-muted": muted, "--block-label-text-color": muted,
        "--block-title-text-color": muted, "--body-text-color-subdued": muted,
        "--vb-accent": accent, "--color-accent": accent, "--primary-500": accent,
        "--button-primary-background-fill": accent,
        "--input-border-color-focus": accent,
        "--primary-600": accent_hover,
        "--button-primary-background-fill-hover": accent_hover,
        "--button-primary-text-color": accent_text,
        "--button-primary-border-color": accent,
        "--vb-accent-soft": accent_soft,
    }


TEMAS = {
    # Claros                bg        bg2       surface   surf.hover elev      border    bord.str  text      muted     accent    acc.hover acc.text  acc.soft
    "arcilla":    {"dark": False, "vars": _paleta("#faf9f5","#f3f1ea","#ffffff","#fbfaf7","#f6f4ee","#ece7dd","#ddd5c7","#23211d","#6f6a60","#c96442","#b5512f","#ffffff","#fbf2ee")},
    "niebla":     {"dark": False, "vars": _paleta("#f4f6fa","#e9eef5","#ffffff","#f7f9fc","#eef2f8","#e0e6ef","#cfd8e4","#1b2330","#5a6677","#2f6df0","#2257cf","#ffffff","#e9f0fe")},
    "menta":      {"dark": False, "vars": _paleta("#f2f6f2","#e6efe8","#ffffff","#f6faf6","#ebf3ed","#dde8e0","#cadbcf","#182519","#566b5b","#1f9e63","#16804f","#ffffff","#e6f5ec")},
    # Oscuros
    "noche":      {"dark": True,  "vars": _paleta("#262624","#1f1f1d","#30302e","#383836","#2b2b29","#3c3b38","#4a4844","#ece9e1","#a8a39a","#e08a63","#ce744c","#2a1109","#3a322c")},
    "medianoche": {"dark": True,  "vars": _paleta("#0f1626","#0a0f1c","#18223a","#1f2b48","#141d33","#283450","#354465","#e7ecf6","#93a1bd","#5b8dff","#4070ec","#ffffff","#1c2944")},
    "carbon":     {"dark": True,  "vars": _paleta("#18181d","#121216","#232330","#2b2b3a","#1e1e28","#33333f","#42424f","#eae8f2","#a29fb2","#b692f5","#a074ee","#1a1320","#2a2440")},
}

TEMAS_CLAROS = ["arcilla", "niebla", "menta"]
TEMAS_OSCUROS = ["noche", "medianoche", "carbon"]
TEMA_DEFECTO = "arcilla"


def temas_js():
    """JS que define window.VB_TEMAS y window.vbTema(id): aplica la paleta sobre
    body, marca el tema activo (atributo data-vbtema, que sobrevive a los
    re-render de @gr.render) y lo persiste en localStorage."""
    data = {tid: {"dark": v["dark"], "vars": v["vars"]} for tid, v in TEMAS.items()}
    return ("window.VB_TEMAS = %s;\n" % json.dumps(data)) + """
window.vbTema = (id) => {
  const t = window.VB_TEMAS[id]; if (!t) return;
  const s = document.body.style;
  Object.values(window.VB_TEMAS).forEach(o =>
    Object.keys(o.vars).forEach(k => s.removeProperty(k)));
  document.body.classList.toggle('dark', !!t.dark);
  for (const k in t.vars) s.setProperty(k, t.vars[k]);
  document.body.setAttribute('data-vbtema', id);
  try { localStorage.setItem('vb_tema', id); } catch (e) {}
};"""


# --- Tipografías (solo fuentes del sistema, sin descargas → 100% local) -------
FUENTES = {
    "sistema":  ["-apple-system", "BlinkMacSystemFont", '"Segoe UI"', "Roboto",
                 "Helvetica", "Arial", "sans-serif"],
    "grotesca": ['"Avenir Next"', '"Helvetica Neue"', "Helvetica", "Arial",
                 "sans-serif"],
    "redonda":  ['"SF Pro Rounded"', '"Hiragino Maru Gothic ProN"',
                 '"Varela Round"', "system-ui", "sans-serif"],
    "serif":    ['"Iowan Old Style"', "Georgia", '"Times New Roman"', "serif"],
    "mono":     ["ui-monospace", "SFMono-Regular", "Menlo", "Consolas",
                 "monospace"],
}
FUENTES_ORDEN = ["sistema", "grotesca", "redonda", "serif", "mono"]
FUENTE_DEFECTO = "sistema"


def fuentes_js():
    """JS: window.vbFuente(id) cambia la tipografía de toda la app (variable
    --font de Gradio + body), marca la activa y la persiste."""
    data = {fid: ", ".join(stack) for fid, stack in FUENTES.items()}
    return ("window.VB_FUENTES = %s;\n" % json.dumps(data)) + """
window.vbFuente = (id) => {
  const f = window.VB_FUENTES[id]; if (!f) return;
  document.body.style.setProperty('--font', f);
  document.body.style.fontFamily = f;
  document.body.setAttribute('data-vbfuente', id);
  try { localStorage.setItem('vb_fuente', id); } catch (e) {}
};"""


# Resalta el botón del tema/fuente activos según el atributo del body (CSS puro,
# así no depende de clases que se pierden al reconstruir la UI al cambiar idioma).
_TEMAS_ACTIVOS_CSS = "\n".join(
    f'body[data-vbtema="{tid}"] .vb-tema[data-tema="{tid}"]{{'
    f'border-color:var(--vb-accent) !important;'
    f'box-shadow:inset 0 0 0 1.5px var(--vb-accent);}}'
    for tid in TEMAS) + "\n" + "\n".join(
    f'body[data-vbfuente="{fid}"] .vb-fuente[data-fuente="{fid}"]{{'
    f'border-color:var(--vb-accent) !important;'
    f'box-shadow:inset 0 0 0 1.5px var(--vb-accent); color:var(--vb-accent) !important;}}'
    for fid in FUENTES)


CSS = """
:root{
  --vb-bg:#faf9f5; --vb-surface:#ffffff; --vb-surface-hover:#fbfaf7;
  --vb-elev:#f6f4ee; --vb-border:#ece7dd;
  --vb-border-strong:#ddd5c7; --vb-text:#23211d; --vb-muted:#6f6a60;
  --vb-accent:#c96442; --vb-accent-soft:#fbf2ee;
}
/* Modo oscuro: Gradio añade la clase .dark al body; las variables cascada
   y todos los elementos propios se adaptan solos. (Los 6 temas inyectan su
   paleta completa por JS sobre body; esto es solo el respaldo inicial.) */
body.dark, .dark{
  --vb-bg:#262624; --vb-surface:#30302e; --vb-surface-hover:#383836;
  --vb-elev:#2b2b29; --vb-border:#3c3b38;
  --vb-border-strong:#4a4844; --vb-text:#ece9e1; --vb-muted:#a8a39a;
  --vb-accent:#e08a63; --vb-accent-soft:#3a322c;
}
.dark .engine-picker label:hover{background:var(--vb-surface-hover) !important;}
/* Lienzo a pantalla completa: ocupa todo el ancho disponible, con un margen
   lateral cómodo que escala (no los ~400px de hueco que dejaba el tope de
   1140px en monitores grandes). */
.gradio-container{max-width:100% !important; margin:0 !important;
  padding:0 clamp(16px, 2vw, 40px) 56px !important;}
footer{display:none !important;}

/* Layout de 3 columnas (estilo GptPlatform): controles · escenario · panel.
   El escenario (resultado + comparador) se lleva todo el espacio sobrante; los
   laterales quedan a un ancho cómodo y estable. Por debajo de 1180px todo se
   reacomoda en una sola columna. */
/* 4 columnas: controles · escenario · filtros · revelado(LUTs/presets) */
.col-controls{flex:0 0 320px !important; max-width:320px;}
.col-aside{flex:0 0 250px !important; max-width:250px;}
.col-revelado{flex:0 0 330px !important; max-width:330px;}
.col-stage{flex:1 1 0 !important; min-width:0;}
@media (max-width:1280px){
  .col-controls, .col-aside, .col-revelado, .col-stage{
    flex:1 1 100% !important; max-width:none !important;}
}
/* Topes de longitud de línea: el texto no se estira en monitores anchos */
.engine-note p, .formato-nota p, .size-preview p,
.aviso-sin-motor p, .cmp-cap{max-width:72ch;}
.sys-card{max-width:80ch;}

/* Selector de idioma: ahora vive dentro de ⚙️ Ajustes (tarjeta «Idioma»). El
   selector real es el disparador de @gr.render y queda oculto arriba, sigue
   funcionando como espejo del visible. */
#vb-lang{display:none !important;}
.aj-idioma{margin-bottom:2px;}

/* Pestañas (Gradio 5: .tab-wrapper › .tab-container[role=tablist] › button).
   Logo a la izquierda + pestañas grandes en negrilla, todo en una fila. */
/* El logo queda alineado con el margen de las columnas/tarjetas de abajo (sin
   sangre): la fila vive dentro del padding lateral del contenedor. */
.tab-wrapper{display:flex !important; align-items:center !important;
  justify-content:flex-start !important; gap:16px !important; height:auto !important;
  padding:8px 0 0 !important;
  border-bottom:1px solid var(--vb-border) !important;}
.tab-container::after{display:none !important;}  /* quitamos el subrayado nativo */
/* el contenedor nativo fija altura y recorta: lo liberamos para los botones grandes */
.tab-container{gap:4px !important; height:auto !important; overflow:visible !important;}
.tab-container button{font-weight:800 !important; color:var(--vb-muted) !important;
  padding:6px 18px !important; font-size:19px !important; letter-spacing:-.01em;}
.tab-container button.selected{color:var(--vb-text) !important;
  box-shadow:inset 0 -2px 0 var(--vb-accent) !important;}
/* Wordmark "PixelBooster": color de acento sólido (siempre visible), con un
   separador fino. Primer ítem flex del contenedor de pestañas. */
.tab-wrapper::before{
  content:"✦ PixelBooster"; flex:0 0 auto; align-self:center; white-space:nowrap;
  font-size:20px; font-weight:800; letter-spacing:-.02em; line-height:1;
  padding-right:16px; border-right:1px solid var(--vb-border);
  color:var(--vb-accent) !important; -webkit-text-fill-color:var(--vb-accent);
  cursor:pointer;}

/* ⚙️ Ajustes: tres columnas siempre desplegadas, cada sección en su tarjeta */
.aj-cols{align-items:flex-start !important; gap:18px !important;}
.aj-card{background:var(--vb-surface) !important; border:1px solid var(--vb-border) !important;
  border-radius:16px !important; padding:16px 18px 18px !important;
  margin-bottom:16px !important; box-shadow:none !important;}
.aj-card > .md:first-child h3, .aj-card h3:first-child{margin-top:0 !important;}
.aj-card h3{font-size:16px !important; font-weight:650 !important;
  color:var(--vb-text) !important; margin:0 0 12px !important;}
.aj-card h4{font-size:14.5px !important; color:var(--vb-text) !important;
  margin:2px 0 6px !important;}
.aj-card p, .aj-card li{font-size:13.5px !important; line-height:1.55 !important;}

/* Selector de motores como tarjetas */
.engine-picker fieldset{display:flex; flex-direction:column; gap:8px;
  border:none !important; padding:0 !important;}
.engine-picker .wrap{gap:8px !important;}
.engine-picker label{display:flex !important; align-items:center; gap:11px;
  margin:0 !important; padding:13px 15px !important; width:100%;
  border:1px solid var(--vb-border) !important; border-radius:12px !important;
  background:var(--vb-surface) !important; cursor:pointer; transition:border-color .15s, background .15s;}
.engine-picker label:hover{border-color:var(--vb-border-strong) !important;
  background:var(--vb-surface-hover) !important;}
.engine-picker label:has(input:checked){border-color:var(--vb-accent) !important;
  background:var(--vb-accent-soft) !important; box-shadow:inset 0 0 0 1px var(--vb-accent);}
.engine-picker input[type=radio]{accent-color:var(--vb-accent);}

/* Nota del motor: callout suave */
.engine-note{background:var(--vb-elev) !important; border:1px solid var(--vb-border) !important;
  border-radius:12px !important; padding:13px 15px !important;}
.engine-note p{margin:0 !important; color:var(--vb-text) !important; font-size:13.5px !important;
  line-height:1.55 !important;}

/* Vista previa de resolución */
.size-preview p{margin:2px 0 0 !important; font-size:14.5px !important; color:var(--vb-text) !important;}

/* Consola de progreso oscura tipo terminal */
.console textarea{background:#1f1e1c !important; color:#d6d2c7 !important;
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace !important; font-size:12.5px !important;
  line-height:1.65 !important; border-radius:12px !important; border:none !important;}

/* Catálogo atenuado de motores no disponibles en este equipo (🔒 NVIDIA / ⬇ instalar) */
.engine-otros{margin:4px 0 10px !important; padding:9px 12px !important;
  border-radius:10px !important; background:rgba(0,0,0,.025) !important;
  border:1px dashed rgba(0,0,0,.12) !important;}
.dark .engine-otros{background:rgba(255,255,255,.03) !important;
  border-color:rgba(255,255,255,.13) !important;}
.engine-otros, .engine-otros p, .engine-otros span{color:#a79f93 !important;
  font-size:12px !important; line-height:1.7 !important;}
.engine-otros b{color:#b9714e !important; font-weight:600 !important;}
.engine-otros strong{color:#8c857a !important;}
.dark .engine-otros, .dark .engine-otros p{color:#8b8478 !important;}

/* Barra de avance minimalista, justo debajo de la consola (solo durante el proceso) */
.vb-bar-wrap{padding:6px 2px 0 !important;}
.vb-bar{height:5px; border-radius:999px; background:rgba(0,0,0,.10); overflow:hidden;}
.dark .vb-bar{background:rgba(255,255,255,.12);}
.vb-bar-fill{height:100%; border-radius:999px; background:var(--vb-accent);
  transition:width .25s cubic-bezier(.22,1,.36,1);}
.vb-bar-pct{font-size:11px; opacity:.6; text-align:right; margin-top:3px;
  font-variant-numeric:tabular-nums; letter-spacing:.02em;}

/* Galería del comparador de LUTs (dentro de los looks): miniaturas compactas */
.vb-frame-cmp{margin-top:6px;}
.vb-frame-cmp .grid-wrap{max-height:none !important;}

/* Botón de acción a ancho completo */
.cta button{width:100% !important; padding:13px !important; font-size:15px !important;
  font-weight:600 !important;}

/* Aviso destacado: no hay motor de mejora por IA instalado */
.aviso-sin-motor{background:#fdf1e7 !important; border:1px solid #e9b894 !important;
  border-left:4px solid var(--vb-accent) !important; border-radius:12px !important;
  padding:14px 18px !important; margin:4px 0 18px !important;}
.aviso-sin-motor p{margin:0 0 6px !important; color:#5a3a2a !important; font-size:14px !important;
  line-height:1.55 !important;}
.aviso-sin-motor p:last-child{margin:0 !important;}
.aviso-sin-motor code{background:#f4dcc9 !important; color:#7a3d20 !important;
  padding:1px 6px !important; border-radius:6px !important; font-size:12.5px !important;}
.dark .aviso-sin-motor{background:#3a2a1f !important; border-color:#6f4a30 !important;}
.dark .aviso-sin-motor p{color:#f0d4c0 !important;}
.dark .aviso-sin-motor code{background:#4a3424 !important; color:#f0c4a0 !important;}

/* Nota bajo el selector de formato */
.formato-nota p{margin:4px 0 0 !important; font-size:12.5px !important;
  color:var(--vb-muted) !important; line-height:1.5 !important;}

/* Título de cada frame fijado en el comparador avanzado */
.cmp-cap{margin:10px 0 4px !important; font-size:12.5px !important;
  color:var(--vb-muted) !important; font-weight:600 !important;}

/* Comparador antes/después (CSS puro, sin dependencias).
   La imagen "después" (en flujo) define la altura exacta del contenedor; la
   "antes" se superpone con el MISMO tamaño (width:100%, alto automático) para
   que el corte coincida pixel a pixel. Sin min-height: forzarlo desalineaba
   las capas cuando la imagen era más baja. */
.ba-cmp{position:relative; width:100%; border-radius:14px; overflow:hidden;
  border:1px solid var(--vb-border); background:#1f1e1c; line-height:0; user-select:none;
  touch-action:none;}
.ba-cmp img{display:block; width:100%;}
.ba-cmp .ba-before{position:absolute; top:0; left:0; width:100%; height:auto;}

/* Botón de pantalla completa (encima del slider invisible; abajo-derecha
   para no chocar con la etiqueta "Después") */
.ba-cmp .ba-fs{position:absolute; bottom:9px; right:9px; z-index:4; width:30px; height:30px;
  display:flex; align-items:center; justify-content:center; padding:0; line-height:1;
  font-size:16px; border:none; border-radius:8px; cursor:pointer;
  background:rgba(31,30,28,.72); color:#fff; box-shadow:0 1px 4px rgba(0,0,0,.3);}
.ba-cmp .ba-fs:hover{background:rgba(31,30,28,.92);}

/* En pantalla completa: ambas capas con el mismo encuadre (contain) para que
   sigan alineadas, centradas sobre fondo negro. */
.ba-cmp:fullscreen, .ba-cmp:-webkit-full-screen{background:#000; display:flex;
  align-items:center; justify-content:center; border:none; border-radius:0;}
.ba-cmp:fullscreen .ba-after, .ba-cmp:fullscreen .ba-before,
.ba-cmp:-webkit-full-screen .ba-after, .ba-cmp:-webkit-full-screen .ba-before{
  position:absolute; top:0; left:0; width:100vw; height:100vh; object-fit:contain;}
.ba-cmp .ba-line{position:absolute; top:0; bottom:0; left:var(--pos,50%); width:2px;
  background:#fff; box-shadow:0 0 0 1px rgba(0,0,0,.22); transform:translateX(-1px);
  pointer-events:none;}
.ba-cmp .ba-line::after{content:""; position:absolute; top:50%; left:50%; width:36px; height:36px;
  transform:translate(-50%,-50%); border-radius:50%; background:#fff;
  box-shadow:0 1px 5px rgba(0,0,0,.35);}
.ba-cmp input[type=range]{position:absolute; inset:0; width:100%; height:100%; margin:0;
  opacity:0; cursor:ew-resize; -webkit-appearance:none; appearance:none; background:transparent;}
.ba-cmp .ba-tag{position:absolute; top:11px; padding:3px 9px; font-size:11px; line-height:1.45;
  border-radius:7px; background:rgba(31,30,28,.72); color:#fff; pointer-events:none;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;}
.ba-cmp .ba-l{left:11px;} .ba-cmp .ba-r{right:11px;}

/* Pestaña Sistema más legible */
.sys-card{background:var(--vb-surface); border:1px solid var(--vb-border); border-radius:14px; padding:6px 20px;}

/* Mantenimiento: nombre del motor + ruta de descarga */
.mant-info p{margin:0 !important; font-size:14px !important; line-height:1.5 !important;}
.mant-info code{font-size:11.5px !important; color:var(--vb-muted) !important;
  background:var(--vb-accent-soft) !important; padding:1px 6px !important;
  border-radius:6px !important; word-break:break-all;}

/* Selector de temas (galería de swatches) */
.vb-temas{display:flex; flex-direction:column; gap:18px; padding:4px 2px 2px;}
.vb-temas-tit{display:block; font-size:11.5px; font-weight:700; letter-spacing:.06em;
  text-transform:uppercase; color:var(--vb-muted); margin:0 0 10px;}
.vb-temas-row{display:flex; flex-wrap:wrap; gap:10px;}
.vb-tema{display:inline-flex; align-items:center; gap:11px; padding:9px 15px 9px 9px;
  border:1px solid var(--vb-border); border-radius:13px; background:var(--vb-surface);
  cursor:pointer; font-family:inherit; font-size:13.5px; font-weight:600;
  color:var(--vb-text); transition:border-color .15s, box-shadow .15s, transform .12s;}
.vb-tema:hover{border-color:var(--vb-border-strong); transform:translateY(-1px);}
.vb-tema:focus-visible{outline:2px solid var(--vb-accent); outline-offset:2px;}
.vb-tema-sw{position:relative; width:36px; height:36px; border-radius:9px; flex:0 0 auto;
  overflow:hidden; box-shadow:inset 0 0 0 1px rgba(0,0,0,.10);
  background:linear-gradient(135deg, var(--c1) 0 52%, var(--c2) 52% 100%);}
.vb-tema-sw::after{content:""; position:absolute; right:5px; bottom:5px; width:12px; height:12px;
  border-radius:50%; background:var(--c3); box-shadow:0 0 0 2px var(--c2);}
.vb-tema-nom{white-space:nowrap;}

/* Selector de tipografía: cada botón se muestra EN su propia fuente (preview) */
.vb-tipo-tit{display:block; font-size:11.5px; font-weight:700; letter-spacing:.06em;
  text-transform:uppercase; color:var(--vb-muted); margin:18px 0 10px;}
.vb-fuentes{display:flex; flex-wrap:wrap; gap:8px;}
.vb-fuente{padding:9px 15px; border:1px solid var(--vb-border); border-radius:11px;
  background:var(--vb-surface); color:var(--vb-text); cursor:pointer; font-size:15px;
  font-weight:600; transition:border-color .15s, box-shadow .15s, transform .12s;}
.vb-fuente:hover{border-color:var(--vb-border-strong); transform:translateY(-1px);}
.vb-fuente:focus-visible{outline:2px solid var(--vb-accent); outline-offset:2px;}

/* Responsive */
@media (max-width:760px){
  .gradio-container{padding:0 14px 40px !important;}
  .tab-wrapper{gap:10px !important;}
  .tab-wrapper::before{font-size:17px; padding-right:10px;}
  .tab-container button{font-size:16px !important; padding:10px 13px !important;}
}
"""

# Reglas que resaltan el tema activo (generadas a partir de TEMAS).
CSS += "\n\n/* Tema activo */\n" + _TEMAS_ACTIVOS_CSS + "\n"
