"""Diagnóstico de VideoBoost — ¿qué está listo para procesar?

Uso:  python check.py

No necesita GPU. Revisa el hardware, los entornos (.venv-*), los repos clonados y
los pesos descargados de cada motor, y te dice en una tabla qué está listo, qué
falta y con qué comando instalarlo. Pensado para correrlo en la máquina real
ANTES del primer uso, para no descubrir lo que falta a mitad de un proceso.
"""

import sys
from pathlib import Path

from engines import RAIZ, VENDOR

# Colores ANSI (se desactivan si la salida no es una terminal)
_TTY = sys.stdout.isatty()
def _c(txt, code):
    return f"\033[{code}m{txt}\033[0m" if _TTY else txt
VERDE, AMAR, ROJO, GRIS, NEGR = "32", "33", "31", "90", "1"

LISTO = _c("✅ listo", VERDE)
INCOMPLETO = _c("⚠️  incompleto", AMAR)
NO_INST = _c("◻️  no instalado", GRIS)
FALTA = _c("❌ falta", ROJO)


def _venv_ok(nombre):
    d = RAIZ / nombre
    return (d / "bin" / "python").exists() or (d / "Scripts" / "python.exe").exists()


def _estado(venv, disponible):
    """Combina presencia del entorno y de repo+pesos en un veredicto legible."""
    if venv is None:
        # Sin entorno propio (FFmpeg, binarios Vulkan): el veredicto es binario.
        return (LISTO, None) if disponible else (NO_INST, None)
    tiene_venv = _venv_ok(venv)
    if disponible and tiene_venv:
        return LISTO, None
    if tiene_venv and not disponible:
        return INCOMPLETO, "entorno creado pero faltan repo o pesos — reejecuta el instalador"
    if disponible and not tiene_venv:
        return INCOMPLETO, f"faltan dependencias del entorno {venv} — reejecuta el instalador"
    return NO_INST, None


def _seguro(fn):
    try:
        return bool(fn())
    except Exception:
        return False


def main():
    import hardware

    hw = hardware.info_sistema()
    print()
    print(_c("  VideoBoost · diagnóstico", NEGR))
    print("  " + "─" * 46)
    print("  " + hardware.resumen().replace("**", ""))
    print()

    # Importa los motores con tolerancia a fallos de import.
    import importlib
    mods = {}
    for nombre in ("faithdiff", "instantir", "faces", "color", "flashvsr"):
        try:
            mods[nombre] = importlib.import_module(f"engines.{nombre}")
        except Exception as e:
            mods[nombre] = e

    def disp(nombre, attr):
        m = mods.get(nombre)
        if isinstance(m, Exception) or m is None:
            return False
        return _seguro(getattr(m, attr))

    # (categoría, etiqueta, venv, fn_disponible, comando, solo_nvidia)
    seedvr2_ok = (VENDOR / "seedvr2" / "inference_cli.py").exists()
    filas = [
        ("Base", "FFmpeg", None, lambda: hw["ffmpeg"], "instalador base / Homebrew", False),
        ("Base", "Entorno principal (.venv)", ".venv", lambda: True, "instalar_mac.sh / INSTALAR_NVIDIA.bat", False),
        ("Base", "Motores Vulkan (Real-ESRGAN, CUGAN, waifu2x, RIFE)", None,
         lambda: hw["vulkan"], "instalador base (descargar_vulkan.py)", False),

        ("Video", "SeedVR2", ".venv", lambda: seedvr2_ok, "instalador base", False),
        ("Video", "FlashVSR", ".venv-flashvsr", lambda: disp("flashvsr", "disponible"),
         "install/extras_flashvsr", True),

        ("Imagen", "FaithDiff  (recomendado, MIT)", ".venv-faithdiff",
         lambda: disp("faithdiff", "disponible"), "install/extras_faithdiff", True),
        ("Imagen", "InstantIR", ".venv-instantir", lambda: disp("instantir", "disponible"),
         "install/extras_instantir", True),
        ("Imagen", "CodeFormer (caras)", ".venv-caras", lambda: disp("faces", "disponible"),
         "install/extras_caras", False),
        ("Imagen", "DDColor (color)", ".venv-color", lambda: disp("color", "disponible"),
         "install/extras_color", False),
    ]

    listos = pendientes = 0
    cat_actual = None
    for cat, etiqueta, venv, fn, comando, solo_nvidia in filas:
        if cat != cat_actual:
            print(f"  {_c(cat, NEGR)}")
            cat_actual = cat
        estado, detalle = _estado(venv, _seguro(fn))
        nota = ""
        if solo_nvidia and not hw["cuda"]:
            estado = _c("— solo NVIDIA", GRIS)
            nota = "no aplica en esta máquina"
        elif estado is LISTO:
            listos += 1
        elif estado is NO_INST:
            pendientes += 1
            nota = f"instala con: {comando}"
        elif estado is INCOMPLETO:
            pendientes += 1
            nota = detalle or f"instala con: {comando}"
        linea = f"    {etiqueta:<48} {estado}"
        print(linea + (f"   {_c('· ' + nota, GRIS)}" if nota else ""))
    print()
    print("  " + "─" * 46)
    print(f"  {_c(str(listos) + ' listos', VERDE)} · "
          f"{_c(str(pendientes) + ' por instalar', AMAR)}")
    print()
    if pendientes:
        print(_c("  Sugerencia: instala primero la base, luego los extras que vayas a usar.", GRIS))
        print(_c("  No hace falta instalarlos todos: solo los motores que quieras.", GRIS))
        print()


if __name__ == "__main__":
    main()
