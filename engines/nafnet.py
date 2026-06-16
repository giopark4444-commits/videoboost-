"""NAFNet (megvii-research, MIT) — restauración de imagen por red simple (sin
difusión): quita ruido (denoise, pesos SIDD) o desenfoque de movimiento (deblur,
pesos GoPro). Rápido y ligero, ideal como paso de limpieza antes de un upscaler.

Funciona en AMBAS plataformas: al ser una CNN normal (no SD), corre razonable en
Mac/MPS-CPU y en NVIDIA/CUDA. Apto para uso comercial (MIT).

Inferencia oficial vía BasicSR: `basicsr/demo.py -opt <yml> --input_path <in>
--output_path <out>`. Los pesos NO son un flag: van en la clave
`path.pretrain_network_g` del .yml; usamos los .yml oficiales de
options/test/SIDD y options/test/GoPro tal cual, y el instalador deja los pesos
en vendor/NAFNet/experiments/pretrained_models/ (las rutas por defecto del yml).

Vive en .venv-nafnet. NO PROBADO EN GPU REAL desde aquí: verificar flags y la
ruta de salida en la 4080 (y rendimiento en Mac).
"""

import shutil
import tempfile
from pathlib import Path

from engines import SALIDAS, VENDOR, correr, python_venv

NAFNET_DIR = VENDOR / "NAFNet"
PESOS = NAFNET_DIR / "experiments" / "pretrained_models"

# Tarea -> (yml oficial de test, nombre del peso que espera ese yml). El yml ya
# apunta a experiments/pretrained_models/<peso>, así que solo verificamos que el
# .pth exista; no reescribimos el yml.
TAREAS = {
    "denoise": ("options/test/SIDD/NAFNet-width64.yml", "NAFNet-SIDD-width64.pth"),
    "deblur": ("options/test/GoPro/NAFNet-width64.yml", "NAFNet-GoPro-width64.pth"),
}


def disponible() -> bool:
    if not (NAFNET_DIR / "basicsr" / "demo.py").exists():
        return False
    # Necesitamos al menos un juego de pesos descargado.
    return any((PESOS / peso).exists() for _, peso in TAREAS.values())


def mejorar(entrada, tarea="denoise"):
    """Generador: cede log y DEVUELVE la ruta de la imagen restaurada.

    tarea: "denoise" (ruido, pesos SIDD) o "deblur" (desenfoque, pesos GoPro)."""
    if tarea not in TAREAS:
        raise ValueError(f"Tarea NAFNet desconocida: {tarea!r}. Usa denoise/deblur.")
    if not disponible():
        raise RuntimeError(
            "NAFNet no está instalado (faltan repo o pesos). "
            "Corre install/extras_nafnet.sh (o .bat)."
        )

    opt_yml, peso = TAREAS[tarea]
    if not (PESOS / peso).exists():
        raise RuntimeError(
            f"Falta el peso de la tarea «{tarea}»: {peso}. "
            "Vuelve a correr install/extras_nafnet.sh para descargarlo."
        )

    entrada = Path(entrada)
    py = python_venv(".venv-nafnet", "install/extras_nafnet.sh")

    tmp = Path(tempfile.mkdtemp(prefix="videoboost_nafnet_"))
    salida_tmp = tmp / f"{entrada.stem}_nafnet.png"

    # demo.py espera rutas de un solo archivo (input/output), no carpetas.
    cmd = [
        py, "basicsr/demo.py",
        "-opt", opt_yml,
        "--input_path", str(entrada),
        "--output_path", str(salida_tmp),
    ]
    try:
        yield f"🚀 NAFNet · {tarea} ({'SIDD' if tarea == 'denoise' else 'GoPro'})"
        yield "ℹ️ Red simple (sin difusión): corre en Mac (MPS/CPU) y en NVIDIA."
        yield from correr(cmd, cwd=NAFNET_DIR)
        if not salida_tmp.exists():
            raise RuntimeError("NAFNet terminó pero no generó la imagen de salida.")
        salida = SALIDAS / f"{entrada.stem}_nafnet_{tarea}.png"
        shutil.copy(salida_tmp, salida)
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
