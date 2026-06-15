"""Mantenimiento de motores: re-descargar sus pesos/binarios y comprobar si hay
una versión más nueva del repo del motor.

Pensado para los botones de la pestaña Sistema. Cada motor declara qué archivos
borrar al re-descargar, con qué instalador se vuelve a bajar, y (si aplica) su
repo git para comparar versiones con el remoto.
"""

import shutil
import subprocess
import sys
from pathlib import Path

from engines import BIN, MODELS, RAIZ, VENDOR, correr

# id → cómo gestionarlo.
#   repo:        carpeta de un repo git (para comprobar versión), o None.
#   borrar:      rutas a eliminar al re-descargar.
#   instalador:  comando (lista) que vuelve a bajar el motor, o None si el peso
#                se re-descarga solo al usar el motor (caso SeedVR2).
_GESTION = {
    "seedvr2": dict(
        repo=VENDOR / "seedvr2",
        carpeta=MODELS / "SEEDVR2",   # dónde viven los pesos descargados
        borrar=[MODELS / "SEEDVR2"],
        instalador=None,  # el modelo se vuelve a descargar solo al pulsar «Mejorar»
    ),
    "vulkan": dict(
        repo=None,  # binarios de release fijo (sin auto-actualización)
        carpeta=BIN,
        borrar=[BIN / "realesrgan", BIN / "realcugan", BIN / "waifu2x", BIN / "rife"],
        instalador=["python", "install/descargar_vulkan.py"],
    ),
    "codeformer": dict(
        repo=VENDOR / "CodeFormer",
        carpeta=VENDOR / "CodeFormer" / "weights",
        borrar=[VENDOR / "CodeFormer" / "weights", RAIZ / ".venv-caras" / ".ok"],
        instalador=["bash", "install/extras_caras.sh"],
    ),
    "ddcolor": dict(
        repo=VENDOR / "DDColor",
        carpeta=MODELS / "DDColor",
        borrar=[MODELS / "DDColor", RAIZ / ".venv-color" / ".ok"],
        instalador=["bash", "install/extras_color.sh"],
    ),
    "diffbir": dict(
        repo=VENDOR / "DiffBIR",
        carpeta=VENDOR / "DiffBIR" / "weights",
        borrar=[VENDOR / "DiffBIR" / "weights", RAIZ / ".venv-diffbir" / ".ok"],
        instalador=["bash", "install/extras_diffbir.sh"],
    ),
    "pmrf": dict(
        repo=VENDOR / "PMRF",
        carpeta=VENDOR / "PMRF",
        borrar=[RAIZ / ".venv-pmrf" / ".ok"],
        instalador=["bash", "install/extras_pmrf.sh"],
    ),
    "osdface": dict(
        repo=VENDOR / "OSDFace",
        carpeta=MODELS / "OSDFace",
        borrar=[MODELS / "OSDFace", RAIZ / ".venv-osdface" / ".ok"],
        instalador=["bash", "install/extras_osdface.sh"],
    ),
    "flashvsr": dict(
        repo=VENDOR / "FlashVSR",
        carpeta=VENDOR / "FlashVSR" / "examples" / "WanVSR" / "FlashVSR-v1.1",
        borrar=[VENDOR / "FlashVSR" / "examples" / "WanVSR" / "FlashVSR-v1.1"],
        instalador=["bash", "install/extras_flashvsr.sh"],
    ),
}

MOTORES = list(_GESTION)


def _tamano_dir(p: Path) -> int:
    """Bytes totales de un archivo o carpeta (0 si no existe)."""
    if not p.exists():
        return 0
    if p.is_file():
        return p.stat().st_size
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())


def _humano(n: int) -> str:
    tam = float(n)
    for unidad in ("B", "KB", "MB", "GB"):
        if tam < 1024 or unidad == "GB":
            return f"{tam:.0f} {unidad}" if unidad == "B" else f"{tam:.1f} {unidad}"
        tam /= 1024
    return f"{tam:.1f} GB"


def carpeta(motor: str) -> Path:
    """Carpeta del disco donde se guardan los archivos descargados del motor."""
    g = _GESTION.get(motor)
    if not g:
        raise RuntimeError(f"Motor desconocido: {motor}")
    return g["carpeta"]


def ubicacion(motor: str) -> dict:
    """Info de almacenamiento: ruta absoluta, si existe y tamaño en disco."""
    p = carpeta(motor)
    total = _tamano_dir(p)
    return {"ruta": str(p), "existe": p.exists() and total > 0,
            "tamano": _humano(total) if total else None}


def abrir_carpeta(motor: str) -> str:
    """Abre la carpeta del motor en el explorador del sistema (Finder/Explorer)."""
    p = carpeta(motor)
    objetivo = p if p.exists() else p.parent  # si aún no existe, abre el contenedor
    objetivo.mkdir(parents=True, exist_ok=True)
    if sys.platform == "darwin":
        subprocess.run(["open", str(objetivo)])
    elif sys.platform == "win32":
        subprocess.run(["explorer", str(objetivo)])
    else:
        subprocess.run(["xdg-open", str(objetivo)])
    return f"📁 Abierto en el explorador: {objetivo}"


def _borrar(p: Path):
    if p.is_dir():
        shutil.rmtree(p, ignore_errors=True)
    elif p.exists():
        p.unlink()


def redescargar(motor: str):
    """Generador: borra los archivos del motor y los vuelve a descargar."""
    g = _GESTION.get(motor)
    if not g:
        raise RuntimeError(f"Motor desconocido: {motor}")
    yield f"🗑️ Borrando archivos descargados de {motor}…"
    for p in g["borrar"]:
        _borrar(p)
        yield f"   • borrado: {p.relative_to(RAIZ) if RAIZ in p.parents else p}"
    if g["instalador"]:
        yield f"⬇️ Re-descargando {motor}… (puede tardar varios minutos)"
        yield from correr(g["instalador"], cwd=RAIZ)
        yield f"✅ {motor}: re-descarga completa."
    else:
        yield (f"✅ Hecho. El modelo de {motor} se volverá a descargar "
               f"automáticamente la próxima vez que pulses «Mejorar».")


def comprobar(motor: str):
    """Generador: comprueba si el repo del motor tiene una versión más nueva."""
    g = _GESTION.get(motor)
    if not g:
        raise RuntimeError(f"Motor desconocido: {motor}")
    repo = g["repo"]
    if repo is None:
        yield (f"ℹ️ {motor}: usa binarios de una versión fija (sin auto-"
               f"actualización). Re-descárgalo solo si se corrompieron.")
        return
    if not (repo / ".git").exists():
        yield f"⚠️ {motor}: no está instalado como repo git. Re-descárgalo."
        return
    yield f"🔍 Comprobando la última versión de {motor}…"
    try:
        subprocess.run(["git", "-C", str(repo), "fetch", "--depth", "1", "origin"],
                       check=True, capture_output=True, text=True, timeout=90)
        local = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                               capture_output=True, text=True).stdout.strip()
        remoto = subprocess.run(["git", "-C", str(repo), "rev-parse", "FETCH_HEAD"],
                                capture_output=True, text=True).stdout.strip()
    except Exception as e:
        yield f"⚠️ No se pudo comprobar la versión: {e}"
        return
    if local == remoto:
        yield f"✅ {motor} está en la última versión (commit {local[:7]})."
    else:
        yield (f"🆕 Hay una versión más nueva de {motor} "
               f"(tienes {local[:7]}, hay {remoto[:7]}). "
               f"Pulsa «Re-descargar» para actualizar.")
