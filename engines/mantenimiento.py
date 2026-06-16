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
    "seedvr2_mlx": dict(
        repo=None,  # paquete pip (mflux); los pesos van al cache de HuggingFace
        carpeta=RAIZ / ".venv-mlx",
        borrar=[RAIZ / ".venv-mlx" / ".ok"],
        instalador=["bash", "install/extras_mlx.sh"],
    ),
    "realesrgan_mlx": dict(
        repo=None,  # pesos MLX descargados de HuggingFace al vendor
        carpeta=VENDOR / "realesrgan-mlx",
        borrar=[VENDOR / "realesrgan-mlx"],
        instalador=["bash", "install/extras_realesrgan_mlx.sh"],
    ),
    "metalfx": dict(
        repo=VENDOR / "fx-upscale",   # checkout git → se puede comprobar versión
        carpeta=VENDOR / "fx-upscale",
        borrar=[VENDOR / "fx-upscale" / ".build"],
        instalador=["bash", "install/extras_metalfx.sh"],
    ),
    "restormer": dict(
        repo=VENDOR / "Restormer",
        carpeta=VENDOR / "Restormer",
        borrar=[RAIZ / ".venv-restormer" / ".ok"],
        instalador=["bash", "install/extras_restormer.sh"],
    ),
    "retinexformer": dict(
        repo=VENDOR / "Retinexformer",
        carpeta=VENDOR / "Retinexformer" / "pretrained_weights",
        borrar=[VENDOR / "Retinexformer" / "pretrained_weights",
                RAIZ / ".venv-retinexformer" / ".ok"],
        instalador=["bash", "install/extras_retinexformer.sh"],
    ),
    "dreamclear": dict(
        repo=VENDOR / "DreamClear",
        carpeta=MODELS / "DreamClear",
        borrar=[MODELS / "DreamClear", RAIZ / ".venv-dreamclear" / ".ok"],
        instalador=["bash", "install/extras_dreamclear.sh"],
    ),
    "hat": dict(
        repo=VENDOR / "HAT",
        carpeta=VENDOR / "HAT" / "experiments" / "pretrained_models",
        borrar=[VENDOR / "HAT" / "experiments" / "pretrained_models",
                RAIZ / ".venv-hat" / ".ok"],
        instalador=["bash", "install/extras_hat.sh"],
    ),
    "practical_rife": dict(
        repo=VENDOR / "Practical-RIFE",
        carpeta=VENDOR / "Practical-RIFE" / "train_log",
        borrar=[RAIZ / ".venv-prife" / ".ok"],
        instalador=["bash", "install/extras_practical_rife.sh"],
    ),
    "film": dict(
        repo=VENDOR / "frame-interpolation",
        carpeta=MODELS / "FILM",
        borrar=[MODELS / "FILM", RAIZ / ".venv-film" / ".ok"],
        instalador=["bash", "install/extras_film.sh"],
    ),
    "ema_vfi": dict(
        repo=VENDOR / "EMA-VFI",
        carpeta=VENDOR / "EMA-VFI" / "ckpt",
        borrar=[VENDOR / "EMA-VFI" / "ckpt", RAIZ / ".venv-emavfi" / ".ok"],
        instalador=["bash", "install/extras_ema_vfi.sh"],
    ),
    "nafnet": dict(
        repo=VENDOR / "NAFNet",
        carpeta=VENDOR / "NAFNet" / "experiments" / "pretrained_models",
        borrar=[VENDOR / "NAFNet" / "experiments" / "pretrained_models",
                RAIZ / ".venv-nafnet" / ".ok"],
        instalador=["bash", "install/extras_nafnet.sh"],
    ),
    "scunet": dict(
        repo=VENDOR / "SCUNet",
        carpeta=MODELS / "SCUNet",
        borrar=[MODELS / "SCUNet", RAIZ / ".venv-scunet" / ".ok"],
        instalador=["bash", "install/extras_scunet.sh"],
    ),
    "fbcnn": dict(
        repo=VENDOR / "FBCNN",
        carpeta=VENDOR / "FBCNN" / "model_zoo",
        borrar=[VENDOR / "FBCNN" / "model_zoo", RAIZ / ".venv-fbcnn" / ".ok"],
        instalador=["bash", "install/extras_fbcnn.sh"],
    ),
    "fftformer": dict(
        repo=VENDOR / "FFTformer",
        carpeta=VENDOR / "FFTformer" / "pretrain_model",
        borrar=[RAIZ / ".venv-fftformer" / ".ok"],
        instalador=["bash", "install/extras_fftformer.sh"],
    ),
    "dehazeformer": dict(
        repo=VENDOR / "DehazeFormer",
        carpeta=VENDOR / "DehazeFormer",
        borrar=[RAIZ / ".venv-dehazeformer" / ".ok"],
        instalador=["bash", "install/extras_dehazeformer.sh"],
    ),
    "hvi_cidnet": dict(
        repo=VENDOR / "HVI-CIDNet",
        carpeta=VENDOR / "HVI-CIDNet",
        borrar=[RAIZ / ".venv-hvi_cidnet" / ".ok"],
        instalador=["bash", "install/extras_hvi_cidnet.sh"],
    ),
    "darkir": dict(
        repo=VENDOR / "DarkIR",
        carpeta=VENDOR / "DarkIR",
        borrar=[RAIZ / ".venv-darkir" / ".ok"],
        instalador=["bash", "install/extras_darkir.sh"],
    ),
    "inspyrenet": dict(
        repo=None,  # paquete pip transparent-background
        carpeta=RAIZ / ".venv-inspyrenet",
        borrar=[RAIZ / ".venv-inspyrenet" / ".ok"],
        instalador=["bash", "install/extras_inspyrenet.sh"],
    ),
    "birefnet": dict(
        repo=None,  # pesos de HuggingFace
        carpeta=RAIZ / ".venv-birefnet",
        borrar=[RAIZ / ".venv-birefnet" / ".ok"],
        instalador=["bash", "install/extras_birefnet.sh"],
    ),
    "restoreformerpp": dict(
        repo=VENDOR / "RestoreFormerPlusPlus",
        carpeta=VENDOR / "RestoreFormerPlusPlus",
        borrar=[RAIZ / ".venv-restoreformerpp" / ".ok"],
        instalador=["bash", "install/extras_restoreformerpp.sh"],
    ),
    "dsrnet": dict(
        repo=VENDOR / "DSRNet",
        carpeta=MODELS / "DSRNet",
        borrar=[MODELS / "DSRNet", RAIZ / ".venv-dsrnet" / ".ok"],
        instalador=["bash", "install/extras_dsrnet.sh"],
    ),
    "shadowformer": dict(
        repo=VENDOR / "ShadowFormer",
        carpeta=MODELS / "ShadowFormer",
        borrar=[MODELS / "ShadowFormer", RAIZ / ".venv-shadowformer" / ".ok"],
        instalador=["bash", "install/extras_shadowformer.sh"],
    ),
    "dut_stab": dict(
        repo=VENDOR / "DUTCode",
        carpeta=VENDOR / "DUTCode" / "ckpt",
        borrar=[VENDOR / "DUTCode" / "ckpt", RAIZ / ".venv-dut" / ".ok"],
        instalador=["bash", "install/extras_dut_stab.sh"],
    ),
    "iclight": dict(
        repo=VENDOR / "IC-Light",
        carpeta=VENDOR / "IC-Light" / "models",
        borrar=[RAIZ / ".venv-iclight" / ".ok"],
        instalador=["bash", "install/extras_iclight.sh"],
    ),
    "iopaint_lama": dict(
        repo=None,  # paquete pip iopaint; pesos LaMa al cache
        carpeta=RAIZ / ".venv-iopaint_lama",
        borrar=[RAIZ / ".venv-iopaint_lama" / ".ok"],
        instalador=["bash", "install/extras_iopaint_lama.sh"],
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
