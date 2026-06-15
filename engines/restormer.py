"""Restormer (swz30, MIT) — restaurador por Transformer eficiente para imágenes.
SOTA en su paper para desenfoque de movimiento, desenfoque de desenfoque (defocus),
quitar lluvia y denoise real. Una sola pasada determinista (no es difusión), así que
es rápido y no inventa textura: ideal para degradaciones "clásicas" de cámara.

CLI estándar del repo: demo.py --task <TAREA> --input_dir <dir-o-archivo>
--result_dir <dir> [--tile N --tile_overlap 32]. NO tiene flag de device: el script
usa CUDA si está disponible. Cada tarea carga un .pth con ruta RELATIVA fija dentro
del repo (<Carpeta>/pretrained_models/<archivo>.pth); el instalador los baja del
release v1.0 de GitHub. La salida se guarda en {result_dir}/{tarea}/{stem}.png,
conservando el nombre de entrada y siempre en PNG.

Modelo PyTorch/CUDA → en la práctica solo NVIDIA. Vive en .venv-restormer. NO
PROBADO EN GPU REAL desde aquí (este Mac no tiene CUDA): verificar flags en la 4080.
"""

import shutil
import tempfile
from pathlib import Path

from engines import SALIDAS, VENDOR, correr, python_venv

RESTORMER_DIR = VENDOR / "Restormer"

# Tareas expuestas (las que tienen pesos descargables y sentido en este flujo):
# desenfoque de movimiento, desenfoque por desenfoque (defocus), quitar lluvia y
# denoise de fotos reales. Dejamos fuera las variantes gaussianas por sigma fijo
# (Gaussian_*_Denoising) porque el "blind" cubre el caso general.
TAREAS = [
    "Motion_Deblurring",
    "Single_Image_Defocus_Deblurring",
    "Deraining",
    "Real_Denoising",
]

# Ruta relativa (dentro del repo) del .pth que demo.py espera por tarea. Si falta,
# el script revienta al hacer torch.load (no autodescarga): el instalador los coloca.
PESOS = {
    "Motion_Deblurring":
        "Motion_Deblurring/pretrained_models/motion_deblurring.pth",
    "Single_Image_Defocus_Deblurring":
        "Defocus_Deblurring/pretrained_models/single_image_defocus_deblurring.pth",
    "Deraining":
        "Deraining/pretrained_models/deraining.pth",
    "Real_Denoising":
        "Denoising/pretrained_models/real_denoising.pth",
}


def disponible() -> bool:
    """Hay Restormer si existe demo.py y al menos un .pth de tarea descargado."""
    if not (RESTORMER_DIR / "demo.py").exists():
        return False
    return any((RESTORMER_DIR / rel).exists() for rel in PESOS.values())


def mejorar(entrada, tarea="Motion_Deblurring"):
    """Generador: cede log y devuelve la ruta de la imagen restaurada."""
    if not disponible():
        raise RuntimeError(
            "Restormer no está instalado. Corre install/extras_restormer.sh (o .bat)."
        )
    if tarea not in TAREAS:
        raise RuntimeError(f"Tarea Restormer desconocida: {tarea}. Usa una de {TAREAS}.")
    if not (RESTORMER_DIR / PESOS[tarea]).exists():
        raise RuntimeError(
            f"Faltan los pesos de '{tarea}' ({PESOS[tarea]}). Vuelve a correr el "
            "instalador para descargarlos del release v1.0."
        )

    entrada = Path(entrada)
    py = python_venv(".venv-restormer", "install/extras_restormer.sh")

    tmp = Path(tempfile.mkdtemp(prefix="videoboost_restormer_"))
    in_dir, out_dir = tmp / "in", tmp / "out"
    in_dir.mkdir(), out_dir.mkdir()
    shutil.copy(entrada, in_dir / entrada.name)

    # demo.py no tiene flag de device: usa CUDA si la hay. --tile None procesa a
    # resolución completa; si la GPU se queda corta con imágenes grandes, en la 4080
    # se puede añadir "--tile", "720" (y --tile_overlap 32 ya es el default).
    cmd = [
        py, "demo.py",
        "--task", tarea,
        "--input_dir", in_dir,
        "--result_dir", out_dir,
    ]
    try:
        yield f"🚀 Restormer · {tarea}"
        yield from correr(cmd, cwd=RESTORMER_DIR)
        # La salida queda en {result_dir}/{tarea}/{stem}.png.
        resultados = [p for p in out_dir.rglob("*")
                      if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
        if not resultados:
            raise RuntimeError("Restormer terminó pero no generó ninguna imagen.")
        salida = SALIDAS / f"{entrada.stem}_restormer.png"
        shutil.copy(resultados[0], salida)
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
