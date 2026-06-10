"""Looks de película analógica como LUTs 3D (.cube) con mezcla regulable.

Genera localmente un LUT .cube (formato estándar de la industria, 33³) por cada
carrete icónico, codificando su carácter documentado: balance cálido/frío,
saturación, contraste, lift de sombras, rolloff suave de altas luces y mezcla
de canales para los B/N. Se aplican con el filtro `lut3d` de FFmpeg y la
intensidad se controla fundiendo con el original (`blend` con opacidad), así
que "cuánto LUT" va de 0 a 100%.

Honestidad: son looks *inspirados* en el carácter conocido de cada película,
no escaneos colorimétricos de los fabricantes. Para el grano, combinar con el
motor de grano analógico (aplicar primero el LUT, luego el grano).

100% FFmpeg/CPU, sin venv propio. Video e imagen; en video el audio se copia.
"""

from pathlib import Path

from engines import MODELS, SALIDAS, correr
from engines import ffmpeg_utils as ff

LUTS_DIR = MODELS / "LUTs"
_TAMANO = 33  # rejilla del LUT 3D

# Carácter de cada carrete. Parámetros:
#   temp  : +cálido / -frío (desplaza R↑ B↓)        tint : +magenta / -verde
#   sat   : saturación (1 = neutra; 0 en B/N)       contraste : pivote en 0.45
#   lift  : levanta sombras (negro lechoso)          rolloff : compresión de altas luces
#   gamma : (r,g,b) por canal                        bw : pesos de mezcla a mono
LOOKS = {
    # ---- negativo color ----
    "portra400":   dict(temp=.055, tint=.010, sat=.92, contraste=.94, lift=.020, rolloff=.18),
    "portra160":   dict(temp=.040, tint=.008, sat=.89, contraste=.90, lift=.018, rolloff=.20),
    "portra800":   dict(temp=.065, tint=.012, sat=.96, contraste=1.00, lift=.030, rolloff=.15),
    "ektar100":    dict(temp=.030, sat=1.24, contraste=1.16, rolloff=.06, gamma=(.985, 1, 1)),
    "gold200":     dict(temp=.095, tint=.015, sat=1.06, contraste=1.00, lift=.015,
                        rolloff=.12, gamma=(.965, 1, 1.075)),
    "ultramax400": dict(temp=.060, sat=1.12, contraste=1.06, lift=.010, rolloff=.10),
    "colorplus200": dict(temp=.085, sat=.94, contraste=.93, lift=.040, rolloff=.14,
                         gamma=(.97, 1, 1.06)),
    "superia400":  dict(temp=-.010, tint=-.028, sat=1.08, contraste=1.05, lift=.012,
                        rolloff=.10, gamma=(1, .975, 1)),
    "c200":        dict(temp=-.020, tint=-.018, sat=1.00, contraste=1.00, rolloff=.10),
    "cinestill800t": dict(temp=-.095, tint=.020, sat=.94, contraste=.96, lift=.050,
                          rolloff=.16),
    "cinestill400d": dict(temp=.010, sat=.88, contraste=.91, lift=.030, rolloff=.20),
    # ---- diapositiva ----
    "velvia50":    dict(temp=.020, sat=1.38, contraste=1.24, lift=-.010, rolloff=.04),
    "provia100f":  dict(temp=-.008, sat=1.06, contraste=1.06, rolloff=.07),
    "ektachrome100": dict(temp=-.025, sat=1.07, contraste=1.07, rolloff=.07,
                          gamma=(1, 1, .97)),
    # ---- blanco y negro ----
    "trix400":     dict(bw=(.25, .50, .25), contraste=1.18, lift=.010, rolloff=.10),
    "hp5":         dict(bw=(.28, .46, .26), contraste=1.07, lift=.030, rolloff=.14),
    "tmax400":     dict(bw=(.24, .50, .26), contraste=1.11, rolloff=.10),
    "delta3200":   dict(bw=(.30, .45, .25), contraste=1.15, lift=.050, rolloff=.14),
    "acros100":    dict(bw=(.22, .48, .30), contraste=1.12, lift=-.008, rolloff=.08),
    "fp4":         dict(bw=(.26, .49, .25), contraste=1.06, rolloff=.10),
}

# Nombres visibles (los carretes son nombres propios: iguales en es/en/fr).
NOMBRES = {
    "portra400": "Kodak Portra 400", "portra160": "Kodak Portra 160",
    "portra800": "Kodak Portra 800", "ektar100": "Kodak Ektar 100",
    "gold200": "Kodak Gold 200", "ultramax400": "Kodak UltraMax 400",
    "colorplus200": "Kodak ColorPlus 200", "superia400": "Fujifilm Superia X-TRA 400",
    "c200": "Fujifilm C200", "cinestill800t": "CineStill 800T",
    "cinestill400d": "CineStill 400D", "velvia50": "Fujifilm Velvia 50",
    "provia100f": "Fujifilm Provia 100F", "ektachrome100": "Kodak Ektachrome E100",
    "trix400": "Kodak Tri-X 400 (B/N)", "hp5": "Ilford HP5 Plus (B/N)",
    "tmax400": "Kodak T-Max 400 (B/N)", "delta3200": "Ilford Delta 3200 (B/N)",
    "acros100": "Fuji Neopan Acros 100 (B/N)", "fp4": "Ilford FP4 Plus (B/N)",
}


def _transformar(rgb, p):
    """Aplica el carácter del carrete a un array Nx3 en [0,1]. Devuelve Nx3."""
    import numpy as np

    r, g, b = rgb[:, 0].copy(), rgb[:, 1].copy(), rgb[:, 2].copy()

    # Balance de blancos (temperatura/tinte)
    temp, tint = p.get("temp", 0.0), p.get("tint", 0.0)
    r *= 1 + temp
    b *= 1 - temp
    g *= 1 + tint

    # Mezcla a mono (B/N de plata)
    if "bw" in p:
        wr, wg, wb = p["bw"]
        y = wr * r + wg * g + wb * b
        r = g = b = y

    out = np.stack([r, g, b], axis=1)

    # Lift de sombras y contraste con pivote
    lift = p.get("lift", 0.0)
    out = lift + (1 - lift) * out
    out = 0.45 + (out - 0.45) * p.get("contraste", 1.0)
    out = np.clip(out, 0, 1)

    # Rolloff suave de altas luces (hombro fílmico)
    a = p.get("rolloff", 0.0)
    if a:
        out = (1 + a) * out / (1 + a * out)

    # Gamma por canal
    gr, gg, gb = p.get("gamma", (1, 1, 1))
    out[:, 0] **= gr
    out[:, 1] **= gg
    out[:, 2] **= gb

    # Saturación (alrededor de luma 709)
    sat = 0.0 if "bw" in p else p.get("sat", 1.0)
    luma = (0.2126 * out[:, 0] + 0.7152 * out[:, 1] + 0.0722 * out[:, 2])[:, None]
    out = luma + (out - luma) * sat

    return np.clip(out, 0, 1)


def generar_lut(look: str) -> Path:
    """Escribe models/LUTs/{look}.cube (si no existe) y devuelve su ruta."""
    import numpy as np

    ruta = LUTS_DIR / f"{look}.cube"
    if ruta.exists():
        return ruta
    LUTS_DIR.mkdir(parents=True, exist_ok=True)

    n = _TAMANO
    ejes = np.linspace(0, 1, n)
    # .cube: el canal R varía más rápido → orden de bucles b, g, r
    bb, gg, rr = np.meshgrid(ejes, ejes, ejes, indexing="ij")
    rgb = np.stack([rr.ravel(), gg.ravel(), bb.ravel()], axis=1)
    out = _transformar(rgb, LOOKS[look])

    lineas = [f'TITLE "VideoBoost {NOMBRES[look]}"', f"LUT_3D_SIZE {n}"]
    lineas += [f"{r:.6f} {g:.6f} {b:.6f}" for r, g, b in out]
    ruta.write_text("\n".join(lineas) + "\n")
    return ruta


# Ajustes neutros del panel de revelado (set Lumetri completo). Cualquier valor
# en neutro se omite de la cadena de filtros (cero coste).
NEUTRO = dict(
    # corrección básica
    exposicion=0.0, contraste=1.0, altas=0.0, sombras=0.0, blancos=0.0,
    negros=0.0, temperatura=6500, tinte=0.0, saturacion=1.0,
    # creativo
    vibranza=0.0, matiz=0.0, desvaido=0.0, tinte_sombras=0.0, tinte_altas=0.0,
    # detalle y viñeta
    nitidez=0.0, claridad=0.0, ruido=0.0, vineta=0.0,
)


def _r(x, lim):
    return max(-lim, min(lim, float(x)))


def _cadena_basica(a):
    """Filtros de corrección (solo los que se apartan del neutro)."""
    f = []
    if abs(a["exposicion"]) > 1e-3:
        f.append(f"exposure=exposure={a['exposicion']:.2f}")        # en EV
    if int(a["temperatura"]) != 6500:
        f.append(f"colortemperature=temperature={int(a['temperatura'])}")
    if abs(a["matiz"]) > 1e-2:
        f.append(f"hue=h={_r(a['matiz'], 45):.1f}")                  # rotación en grados

    # Blancos / negros / película desvaída → niveles (lineal, siempre monótono).
    b, w, fd = _r(a["negros"], 0.15), _r(a["blancos"], 0.15), max(0.0, min(1.0, a["desvaido"]))
    if abs(b) > 1e-3 or abs(w) > 1e-3 or fd > 1e-3:
        imin = max(0.0, -b)                  # negros − : hunde el punto negro
        omin = max(0.0, b) + fd * 0.10       # negros + / desvaído: lo levanta
        imax = 1.0 - max(0.0, w)             # blancos + : empuja el punto blanco
        omax = 1.0 + min(0.0, w) - fd * 0.05  # blancos − / desvaído: lo retrae
        f.append(f"colorlevels=rimin={imin:.3f}:gimin={imin:.3f}:bimin={imin:.3f}"
                 f":romin={omin:.3f}:gomin={omin:.3f}:bomin={omin:.3f}"
                 f":rimax={imax:.3f}:gimax={imax:.3f}:bimax={imax:.3f}"
                 f":romax={omax:.3f}:gomax={omax:.3f}:bomax={omax:.3f}")

    s, h = _r(a["sombras"], 0.18), _r(a["altas"], 0.18)
    if abs(s) > 1e-3 or abs(h) > 1e-3:
        # curva maestra: sombras en 0.25, altas luces en 0.75
        f.append(f"curves=all='0/0 0.25/{0.25 + s:.3f} 0.75/{0.75 + h:.3f} 1/1'")

    # Tinte global (verde↔magenta) + split toning (frío↔cálido por rango),
    # todo en una sola pasada de colorbalance.
    ti, ts, ta = _r(a["tinte"], 0.3), _r(a["tinte_sombras"], 0.3), _r(a["tinte_altas"], 0.3)
    if abs(ti) > 1e-3 or abs(ts) > 1e-3 or abs(ta) > 1e-3:
        f.append(f"colorbalance=rs={ts:.3f}:bs={-ts:.3f}"
                 f":rh={ta:.3f}:bh={-ta:.3f}"
                 f":gm={-ti:.3f}:gh={-ti / 2:.3f}")

    eq = []
    if abs(a["contraste"] - 1) > 1e-3:
        eq.append(f"contrast={a['contraste']:.3f}")
    if abs(a["saturacion"] - 1) > 1e-3:
        eq.append(f"saturation={a['saturacion']:.3f}")
    if eq:
        f.append("eq=" + ":".join(eq))
    if abs(a["vibranza"]) > 1e-3:
        f.append(f"vibrance=intensity={a['vibranza']:.2f}")          # protege pieles
    return f


def _cadena_detalle(a):
    f = []
    if a["ruido"] > 1e-2:
        f.append(f"hqdn3d={min(10.0, a['ruido']):.1f}")              # antes de afilar
    if a["claridad"] > 1e-3:
        # contraste local: máscara de enfoque ancha y suave
        f.append(f"unsharp=lx=13:ly=13:la={min(1.5, a['claridad']):.2f}")
    if a["nitidez"] > 1e-3:
        f.append(f"unsharp=5:5:{min(3.0, a['nitidez']):.2f}")
    if a["vineta"] > 1e-3:
        f.append(f"vignette=angle={min(1.0, a['vineta']) * 0.628:.3f}")  # hasta ~PI/5
    return f


def etalonar(entrada, es_video, looks=(), **ajustes):
    """Generador: revelado completo — hasta 3 LUTs apilados + corrección básica.

    looks: lista de (look, mezcla) que se aplican EN ORDEN, cada uno fundido
    con el resultado anterior según su mezcla. Los ajustes en neutro no cuestan.
    Orden de la cadena (como Lumetri): corrección básica → LUTs → detalle/viñeta.
    """
    entrada = Path(entrada)
    a = {**NEUTRO, **{k: v for k, v in ajustes.items() if v is not None}}
    capas = [(lk, max(0.0, min(1.0, float(m)))) for lk, m in looks
             if lk and lk != "ninguno" and float(m) > 0]
    for lk, _ in capas:
        if lk not in LOOKS:
            raise RuntimeError(f"Look desconocido: {lk}")

    partes, cur = [], "[0:v]"
    basica = _cadena_basica(a)
    if basica:
        partes.append(f"{cur}{','.join(basica)}[c0]")
        cur = "[c0]"

    # Capas de LUT apiladas. En modo `normal`, blend pondera la PRIMERA entrada
    # con all_opacity: ponemos el LUT primero para que mezcla = "cuánto LUT".
    for n, (lk, m) in enumerate(capas):
        lut_esc = str(generar_lut(lk)).replace("\\", "/").replace(":", "\\:")
        partes.append(
            f"{cur}format=rgb24,split[a{n}][b{n}];"
            f"[b{n}]lut3d='{lut_esc}'[l{n}];"
            f"[l{n}][a{n}]blend=all_mode=normal:all_opacity={m:.3f}[c{n + 1}]"
        )
        cur = f"[c{n + 1}]"

    detalle = _cadena_detalle(a)
    cola = (detalle + ["format=yuv420p"])
    partes.append(f"{cur}{','.join(cola)}[v]")
    filtro = ";".join(partes)

    if es_video:
        salida = SALIDAS / f"{entrada.stem}_revelado.mp4"
        extra = ["-map", "[v]", "-map", "0:a?", "-c:a", "copy",
                 "-c:v", "libx264", "-crf", "17", "-preset", "medium"]
    else:
        salida = SALIDAS / f"{entrada.stem}_revelado.png"
        extra = ["-map", "[v]", "-frames:v", "1", "-update", "1"]

    cmd = [ff.ffmpeg(), "-y", "-i", entrada, "-filter_complex", filtro, *extra, salida]
    resumen = " + ".join(f"{NOMBRES[lk]} {m:.0%}" for lk, m in capas) or "sin LUT"
    tocados = [k for k in NEUTRO if abs(a[k] - NEUTRO[k]) > 1e-3]
    yield f"🎛️ Revelado · {resumen}" + (f" · ajustes: {', '.join(tocados)}" if tocados else "")
    yield from correr(cmd)
    return str(salida)
