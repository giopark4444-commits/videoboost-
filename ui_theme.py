"""Sistema de diseño de VideoBoost — estética cálida y minimalista inspirada en
la app de Claude: fondo crema, acento arcilla, mucho aire, tipografía de sistema
(sin fuentes externas, para seguir 100% local), tarjetas limpias y responsive.

Exporta TEMA (gr.themes.Base configurado) y CSS (string que se inyecta en Blocks).
"""

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

CSS = """
:root{
  --vb-bg:#faf9f5; --vb-surface:#ffffff; --vb-border:#ece7dd;
  --vb-border-strong:#ddd5c7; --vb-text:#23211d; --vb-muted:#7c776d;
  --vb-accent:#c96442; --vb-accent-soft:#fbf2ee;
}
/* Lienzo centrado y bien proporcionado en todo dispositivo */
.gradio-container{max-width:1140px !important; margin:0 auto !important;
  padding:0 20px 56px !important;}
footer{display:none !important;}

/* Cabecera */
#vb-header{padding:30px 0 22px; border-bottom:1px solid var(--vb-border); margin-bottom:22px;}
#vb-header .vb-title{font-size:30px; font-weight:650; letter-spacing:-.01em;
  color:var(--vb-text); margin:0;}
#vb-header .vb-sub-text{margin:8px 0 14px; color:var(--vb-muted); font-size:14.5px;}
#vb-header .vb-sub{margin:0; color:var(--vb-muted); font-size:14.5px;
  display:flex; flex-wrap:wrap; align-items:center; gap:10px;}
#vb-header .vb-pill{display:inline-flex; align-items:center; gap:7px;
  background:#fff; border:1px solid var(--vb-border); border-radius:999px;
  padding:5px 13px; font-size:13px; color:var(--vb-text);}
#vb-header .vb-pill .vb-dot{width:7px; height:7px; border-radius:50%;
  background:var(--vb-accent);}
#vb-header .vb-tier{color:var(--vb-muted); font-size:13.5px;}

/* Selector de idioma minimalista (arriba a la derecha) */
#vb-lang{position:absolute; top:34px; right:20px; z-index:5; max-width:300px;}
#vb-lang fieldset{border:none; padding:0;}
#vb-lang .wrap{gap:0 !important;}
#vb-lang label{padding:6px 13px !important; font-size:13px !important;
  border:1px solid var(--vb-border) !important; background:#fff !important;}

/* Pestañas: subrayado fino, calmado */
.tab-nav{border-bottom:1px solid var(--vb-border) !important; gap:2px !important;}
.tab-nav button{font-weight:600 !important; color:var(--vb-muted) !important;
  padding:11px 16px !important;}
.tab-nav button.selected{color:var(--vb-text) !important;
  border-bottom:2px solid var(--vb-accent) !important;}

/* Selector de motores como tarjetas */
.engine-picker fieldset{display:flex; flex-direction:column; gap:8px;
  border:none !important; padding:0 !important;}
.engine-picker .wrap{gap:8px !important;}
.engine-picker label{display:flex !important; align-items:center; gap:11px;
  margin:0 !important; padding:13px 15px !important; width:100%;
  border:1px solid var(--vb-border) !important; border-radius:12px !important;
  background:#fff !important; cursor:pointer; transition:border-color .15s, background .15s;}
.engine-picker label:hover{border-color:var(--vb-border-strong) !important;
  background:#fdfcfa !important;}
.engine-picker label:has(input:checked){border-color:var(--vb-accent) !important;
  background:var(--vb-accent-soft) !important; box-shadow:inset 0 0 0 1px var(--vb-accent);}
.engine-picker input[type=radio]{accent-color:var(--vb-accent);}

/* Nota del motor: callout suave */
.engine-note{background:#f6f4ee !important; border:1px solid var(--vb-border) !important;
  border-radius:12px !important; padding:13px 15px !important;}
.engine-note p{margin:0 !important; color:#54514a !important; font-size:13.5px !important;
  line-height:1.55 !important;}

/* Vista previa de resolución */
.size-preview p{margin:2px 0 0 !important; font-size:14.5px !important; color:var(--vb-text) !important;}

/* Consola de progreso oscura tipo terminal */
.console textarea{background:#1f1e1c !important; color:#d6d2c7 !important;
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace !important; font-size:12.5px !important;
  line-height:1.65 !important; border-radius:12px !important; border:none !important;}

/* Botón de acción a ancho completo */
.cta button{width:100% !important; padding:13px !important; font-size:15px !important;
  font-weight:600 !important;}

/* Comparador antes/después (CSS puro, sin dependencias) */
.ba-cmp{position:relative; width:100%; border-radius:14px; overflow:hidden;
  border:1px solid var(--vb-border); background:#1f1e1c; line-height:0; user-select:none;
  touch-action:none;}
.ba-cmp img{display:block; width:100%;}
.ba-cmp .ba-before{position:absolute; top:0; left:0; width:100%; height:100%; object-fit:cover;}
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
.sys-card{background:#fff; border:1px solid var(--vb-border); border-radius:14px; padding:6px 20px;}

/* Responsive */
@media (max-width:760px){
  .gradio-container{padding:0 14px 40px !important;}
  #vb-lang{position:static; max-width:none; margin-top:14px;}
  #vb-header{padding-top:22px;}
  #vb-header .vb-title{font-size:25px;}
}
"""
