"""Previsualización rápida de un filtro de post-proceso sobre un solo frame.

Antes de aplicar un filtro (sobre todo un revelado/LUT) a TODO el video, el
usuario quiere ver cómo quedará. Esto extrae un único frame del video y le
aplica el filtro elegido en modo imagen — es órdenes de magnitud más rápido que
procesar el video entero (típicamente ~1 s por preview).

Devuelve siempre `(antes, despues, soporta_preview)`:
  · antes  → ruta del frame extraído sin tocar (referencia "antes").
  · despues→ ruta del frame con el filtro aplicado (o el mismo frame si el
             filtro no tiene sentido sobre un solo cuadro).
  · soporta_preview → False para filtros TEMPORALES (desentrelazar, estabilizar):
             necesitan movimiento entre frames, así que un still no muestra nada
             útil; en ese caso `despues` == `antes`.

Los filtros con preview real son: "lut" (revelado), "grano" y "denoise".
100% FFmpeg/CPU, igual que los motores que envuelve; no usa GPU ni venv propio.
"""

from pathlib import Path

from engines import SALIDAS, correr
from engines import ffmpeg_utils as ff
from engines import grano, luts

# Filtros temporales: un solo frame no muestra su efecto (necesitan movimiento).
_TEMPORALES = {"desentrelazar", "estabilizar"}

# Orden de los 18 ajustes Lumetri dentro de la tupla `rev`, idéntico a
# app.py `_CLAVES_REVELADO` (lo replicamos aquí para no importar de app.py).
_CLAVES_REVELADO = (
    "exposicion", "contraste", "altas", "sombras", "blancos", "negros",
    "temperatura", "tinte", "saturacion",
    "vibranza", "matiz", "desvaido", "tinte_sombras", "tinte_altas",
    "nitidez", "claridad", "ruido", "vineta",
)


def _agotar(gen) -> str:
    """Consume un generador de motor (que cede log) y devuelve su `return`."""
    try:
        while True:
            next(gen)
    except StopIteration as fin:
        return fin.value
    finally:
        gen.close()


def previsualizar(base_video, filtro, pos=0.3, *, g_preset=None, g_int=None,
                  g_tam=None, g_color=None, den_luma=3.0, den_croma=2.0, rev=()):
    """Genera el preview de un solo frame para `filtro` sobre `base_video`.

    Parámetros:
      base_video — ruta del video del que se extrae el frame.
      filtro     — "lut" | "grano" | "denoise" | "desentrelazar" | "estabilizar".
      pos        — posición relativa del frame en el video (0.0–1.0).
      g_preset/g_int/g_tam/g_color — parámetros del motor de grano (preset y
                   sus pisos manuales; ver engines/grano.py).
      den_luma/den_croma — fuerza de denoise en luma/croma (igual que filtros.denoise).
      rev        — tupla plana del panel de revelado, MISMO orden que en app.py:
                   (lut1, mix1, lut2, mix2, lut3, mix3, *18 ajustes de _CLAVES_REVELADO).

    Devuelve `(antes_path, despues_path, soporta_preview: bool)`.
    """
    antes = ff.extraer_frame_preview(base_video, pos)
    if not antes:
        raise RuntimeError("No se pudo extraer un frame del video para el preview.")
    antes = str(antes)

    # Filtros temporales: nada que mostrar en un still → devolvemos el frame intacto.
    if filtro in _TEMPORALES:
        return antes, antes, False

    if filtro == "lut":
        # Espejo de app.py `_revelar`, pero es_video=False (escribe un PNG).
        l1, m1, l2, m2, l3, m3, *ajustes = rev
        gen = luts.etalonar(
            antes, es_video=False, looks=[(l1, m1), (l2, m2), (l3, m3)],
            **{k: float(v) for k, v in zip(_CLAVES_REVELADO, ajustes)},
        )
        despues = _agotar(gen)
        return antes, despues, True

    if filtro == "grano":
        gen = grano.aplicar(antes, es_video=False, preset=g_preset or "clasico",
                            intensidad=g_int, tamano=g_tam, grano_color=g_color)
        despues = _agotar(gen)
        return antes, despues, True

    if filtro == "denoise":
        # hqdn3d sobre el frame único, vía llamada directa a ffmpeg.
        despues = str(SALIDAS / f"{Path(antes).stem}_denoise_preview.png")
        filtro_ff = f"hqdn3d={den_luma:.1f}:{den_croma:.1f}:{den_luma:.1f}:{den_croma:.1f}"
        cmd = [ff.ffmpeg(), "-y", "-i", antes, "-vf", filtro_ff,
               "-frames:v", "1", "-update", "1", despues]
        for _ in correr(cmd):
            pass
        return antes, despues, True

    raise RuntimeError(f"Filtro de preview desconocido: {filtro}")
