"""Preferencias persistentes de PixelBooster (formato de salida por defecto).

Se guardan en un JSON local junto a los presets de revelado; sin servidor, 100%
local. Si el archivo no existe o está corrupto, se usan los valores por defecto.
"""

import json
from pathlib import Path

_ARCHIVO = Path(__file__).parent / "presets" / "ajustes.json"
_DEFECTOS = {"formato_video": "h264", "formato_img": "png"}


def cargar() -> dict:
    try:
        d = json.loads(_ARCHIVO.read_text("utf-8"))
        return {k: d.get(k, v) for k, v in _DEFECTOS.items()}
    except Exception:
        return dict(_DEFECTOS)


def guardar(**cambios) -> dict:
    d = cargar()
    d.update({k: v for k, v in cambios.items() if k in _DEFECTOS and v})
    try:
        _ARCHIVO.parent.mkdir(exist_ok=True)
        _ARCHIVO.write_text(json.dumps(d, ensure_ascii=False, indent=2), "utf-8")
    except Exception:
        pass
    return d


def formato_video() -> str:
    return cargar()["formato_video"]


def formato_img() -> str:
    return cargar()["formato_img"]
