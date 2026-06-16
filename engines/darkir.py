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

# El repo tiene dos modelos: DarkIR_64width.pt (width=64) y DarkIR_384.pt (width=32).
# Solo DarkIR_384.pt está en HuggingFace; usamos el que esté disponible.
_PESO_64 = DARKIR_DIR / "models" / "DarkIR_64width.pt"
_PESO_384 = DARKIR_DIR / "models" / "DarkIR_384.pt"

# Config temporal que escribimos para usar DarkIR_384 cuando no está el _64width.
_CONFIG_384 = """#### red
network:
  name: DarkIR
  img_channels: 3
  width: 32
  middle_blk_num_enc: 2
  middle_blk_num_dec: 2
  enc_blk_nums: [1, 2, 3]
  dec_blk_nums: [3, 1, 1]
  dilations: [1, 4, 9]
  extra_depth_wise: True
save:
  path: ./models/DarkIR_384.pt
Resize: False
"""


def _config_activo() -> tuple:
    """Devuelve (ruta_config, existe_peso)."""
    if _PESO_64.exists():
        return "./options/inference/LOLBlur.yml", True
    if _PESO_384.exists():
        return "./options/inference/_vb_384.yml", True
    return "./options/inference/LOLBlur.yml", False


def disponible() -> bool:
    return (DARKIR_DIR / "inference.py").exists() and (_PESO_64.exists() or _PESO_384.exists())


def mejorar(entrada):
    """Generador: cede log y devuelve la ruta de la imagen restaurada (luz+ruido+blur)."""
    import hardware

    if not disponible():
        raise RuntimeError(
            "DarkIR no está instalado (o falta el peso). Corre "
            "install/extras_darkir.sh y espera a que descargue desde HuggingFace."
        )
    entrada = Path(entrada)
    py = python_venv(".venv-darkir", "install/extras_darkir.sh")
    cuda = hardware.info_sistema()["cuda"]

    config_yml, _ = _config_activo()
    # Si usamos el modelo 384, escribimos la config temporal.
    if config_yml.endswith("_vb_384.yml"):
        cfg_path = DARKIR_DIR / "options" / "inference" / "_vb_384.yml"
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        cfg_path.write_text(_CONFIG_384)

    tmp = Path(tempfile.mkdtemp(prefix="videoboost_darkir_"))
    in_dir = tmp / "in"
    in_dir.mkdir()
    shutil.copy(entrada, in_dir / entrada.name)

    # El repo escribe SIEMPRE en <repo>/images/results conservando el nombre del
    # archivo; lo limpiamos antes para quedarnos solo con nuestro resultado.
    out_dir = DARKIR_DIR / "images" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    prev = {p for p in out_dir.glob("*")}

    cmd = [py, "inference.py", "-p", config_yml, "-i", in_dir]

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
