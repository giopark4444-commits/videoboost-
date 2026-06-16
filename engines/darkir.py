"""DarkIR (cidautai, MIT) — restauración all-in-one para escenas con poca luz:
corrige a la vez baja iluminación, ruido y desenfoque (motion blur) con un solo
modelo ligero (3.3M / 13M parámetros). Pesos entrenados en LOL-Blur.

CLI estándar: inference.py -p <config.yml> -i <carpeta_entrada>. Lee la
configuración de ./options/inference/LOLBlur.yml (que apunta a los pesos en
./models/DarkIR_64width.pt) y escribe cada imagen restaurada en
./images/results conservando su nombre. Vive en .venv-darkir.

Modelo convolucional ligero (NO difusión), así que corre tanto en NVIDIA como en
Mac (MPS/CPU). OJO: el inference.py del repo fija CUDA_VISIBLE_DEVICES="1" a mano
(pensado para su servidor multi-GPU); aquí lo forzamos a "0" en CUDA para que la
4080 sea visible, y lo vaciamos en Mac. NO PROBADO EN GPU REAL desde aquí:
verificar flags y la ubicación/nombre del peso en la 4080.
"""

import os
import shutil
import tempfile
from pathlib import Path

from engines import SALIDAS, VENDOR, correr, python_venv

DARKIR_DIR = VENDOR / "DarkIR"
# Config de inferencia por defecto del repo (all-in-one LOL-Blur).
CONFIG = "./options/inference/LOLBlur.yml"


def disponible() -> bool:
    # Requiere el script y que el peso ya esté descargado (no es automático).
    peso = DARKIR_DIR / "models" / "DarkIR_64width.pt"
    return (DARKIR_DIR / "inference.py").exists() and peso.exists()


def mejorar(entrada):
    """Generador: cede log y devuelve la ruta de la imagen restaurada (luz+ruido+blur)."""
    import hardware

    if not disponible():
        raise RuntimeError(
            "DarkIR no está instalado (o falta el peso). Corre "
            "install/extras_darkir.sh (o .bat) y coloca el modelo en "
            "vendor/DarkIR/models/DarkIR_64width.pt."
        )
    entrada = Path(entrada)
    py = python_venv(".venv-darkir", "install/extras_darkir.sh")
    cuda = hardware.info_sistema()["cuda"]

    tmp = Path(tempfile.mkdtemp(prefix="videoboost_darkir_"))
    in_dir = tmp / "in"
    in_dir.mkdir()
    shutil.copy(entrada, in_dir / entrada.name)

    # El repo escribe SIEMPRE en <repo>/images/results conservando el nombre del
    # archivo; lo limpiamos antes para quedarnos solo con nuestro resultado.
    out_dir = DARKIR_DIR / "images" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    prev = {p for p in out_dir.glob("*")}

    cmd = [py, "inference.py", "-p", CONFIG, "-i", in_dir]

    # Sobrescribimos el CUDA_VISIBLE_DEVICES="1" hardcodeado del script: en CUDA
    # exponemos la GPU 0 (la 4080); en Mac lo vaciamos para no confundir a torch.
    env = dict(os.environ)
    env["CUDA_VISIBLE_DEVICES"] = "0" if cuda else ""

    try:
        yield f"🚀 DarkIR · luz+ruido+desenfoque · {'cuda' if cuda else 'cpu/mps'}"
        yield "ℹ️ Modelo ligero LOL-Blur (all-in-one). El peso debe estar en vendor/DarkIR/models/."
        yield from correr(cmd, cwd=DARKIR_DIR, env=env)
        nuevos = [p for p in out_dir.glob("*")
                  if p not in prev and p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
        if not nuevos:
            raise RuntimeError("DarkIR terminó pero no generó ninguna imagen.")
        salida = SALIDAS / f"{entrada.stem}_darkir.png"
        shutil.copy(nuevos[0], salida)
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
