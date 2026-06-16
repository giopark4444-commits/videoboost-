"""FFTformer (kkkls, MIT) — desenfoque de movimiento (motion deblur) SOTA.
Transformer eficiente en el dominio de frecuencia (FFT) que alcanza 34.21 dB en
GoPro. Una sola pasada determinista (no es difusión): rápido y sin inventar
textura, ideal para fotogramas movidos / fotos con trepidación de cámara.

El repo NO usa un .yml de basicsr (-opt): su `test.py` es argparse puro
(--model_name --data_dir --test_model --save_image). Además su Dataset lee de
DOS subcarpetas, `{data_dir}/test/input/` y `{data_dir}/test/target/` (la
"target" es la etiqueta para medir PSNR; aquí no la usamos, así que la
rellenamos con una copia de la entrada). La salida se guarda SIEMPRE en
`results/{model_name}/GoPro/{nombre-de-entrada}` dentro del repo, conservando el
nombre del archivo; por eso usamos un model_name único por ejecución y luego
limpiamos esa carpeta.

Pesos: GoPro/HIDE viene COMMITEADO en el repo (pretrain_model/fftformer_GoPro.pth,
~66 MB) → llega solo al clonar. RealBlur está en Google Drive (lo baja el
instalador con FFTFORMER_GDRIVE, o se coloca a mano).

⚠️ El script fija `device = torch.device('cuda')` y llama a
`torch.cuda.synchronize()`, así que en la práctica es SOLO NVIDIA (en Mac sin
CUDA revienta). Vive en .venv-fftformer. NO PROBADO EN GPU REAL desde aquí (este
Mac no tiene CUDA): verificar flags y la ruta de salida en la 4080.
"""

import shutil
import tempfile
import time
from pathlib import Path

from engines import SALIDAS, VENDOR, correr, python_venv

FFTFORMER_DIR = VENDOR / "FFTformer"

# Tareas expuestas = los dos pesos preentrenados que tienen sentido para deblur
# de movimiento. Cada una mapea a su .pth (ruta RELATIVA dentro del repo).
TAREAS = ["GoPro", "RealBlur"]

PESOS = {
    "GoPro": "pretrain_model/fftformer_GoPro.pth",        # viene en el repo
    "RealBlur": "pretrain_model/fftformer_RealBlur.pth",  # Google Drive (instalador)
}


def disponible() -> bool:
    """Hay FFTformer si existe test.py y al menos un .pth descargado."""
    if not (FFTFORMER_DIR / "test.py").exists():
        return False
    return any((FFTFORMER_DIR / rel).exists() for rel in PESOS.values())


def mejorar(entrada, tarea="GoPro"):
    """Generador: cede log y devuelve la ruta de la imagen sin desenfoque."""
    if not disponible():
        raise RuntimeError(
            "FFTformer no está instalado. Corre install/extras_fftformer.sh (o .bat)."
        )
    if tarea not in TAREAS:
        raise RuntimeError(f"Tarea FFTformer desconocida: {tarea}. Usa una de {TAREAS}.")
    if not (FFTFORMER_DIR / PESOS[tarea]).exists():
        raise RuntimeError(
            f"Faltan los pesos de '{tarea}' ({PESOS[tarea]}). "
            "Vuelve a correr el instalador para descargarlos."
        )

    entrada = Path(entrada)
    py = python_venv(".venv-fftformer", "install/extras_fftformer.sh")

    # El Dataset exige extensión png/jpg/jpeg; normalizamos el nombre a .png para
    # no chocar con entradas .webp u otras.
    nombre = entrada.stem + ".png"

    # data_dir debe contener test/input/<img> y test/target/<img> (mismo nombre).
    # La "target" es solo la etiqueta de PSNR: la rellenamos con la propia entrada.
    tmp = Path(tempfile.mkdtemp(prefix="videoboost_fftformer_"))
    in_dir = tmp / "test" / "input"
    tg_dir = tmp / "test" / "target"
    in_dir.mkdir(parents=True), tg_dir.mkdir(parents=True)
    shutil.copy(entrada, in_dir / nombre)
    shutil.copy(entrada, tg_dir / nombre)

    # model_name único → la salida va a results/<model_name>/GoPro/ (carpeta fija
    # en el código, da igual la tarea) dentro del repo; lo limpiamos al terminar.
    model_name = f"vb_{int(time.time() * 1000)}"
    out_dir = FFTFORMER_DIR / "results" / model_name

    # test.py NO tiene flag de device (usa cuda fija). --save_image True guarda la
    # imagen; pasamos un str no vacío porque su default es bool(True).
    cmd = [
        py, "test.py",
        "--model_name", model_name,
        "--data_dir", str(tmp),
        "--test_model", PESOS[tarea],
        "--save_image", "True",
    ]
    try:
        yield f"🚀 FFTformer · deblur · {tarea}"
        yield from correr(cmd, cwd=FFTFORMER_DIR)
        # La salida queda en results/<model_name>/GoPro/<nombre>.
        resultados = [p for p in out_dir.rglob("*")
                      if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
        if not resultados:
            raise RuntimeError("FFTformer terminó pero no generó ninguna imagen.")
        salida = SALIDAS / f"{entrada.stem}_fftformer.png"
        shutil.copy(resultados[0], salida)
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(out_dir, ignore_errors=True)
