"""IOPaint + LaMa (ambos Apache-2.0) — BORRAR objetos/personas/defectos de una
imagen mediante inpainting. El usuario marca lo que sobra con una MÁSCARA (blanco
= zona a borrar) y LaMa rellena el hueco de forma coherente.

IOPaint es un paquete pip ("iopaint"), no un repo a clonar: la instalación crea
.venv-iopaint_lama con el ejecutable `iopaint`. Usamos su CLI por lotes headless:

    iopaint run --model=lama --device=<cpu|cuda|mps> \
        --image=<carpeta_imagenes> --mask=<carpeta_o_archivo_mascara> \
        --output=<carpeta_salida> --model-dir=<models/IOPaint>

Reglas de la máscara (según docs de IOPaint): si --mask es un archivo, se aplica
a todas las imágenes; si es carpeta, cada máscara debe llamarse igual que su
imagen. La máscara se reescala sola al tamaño de la imagen. Aquí pasamos UNA
imagen + UNA máscara, así que damos la máscara como archivo.

LaMa es ligero (no es difusión): corre razonablemente en CPU, CUDA y MPS, así que
sirve tanto en Mac Apple Silicon como en la RTX 4080. Los pesos se descargan
solos la primera vez a --model-dir. NO PROBADO EN GPU REAL desde aquí: verificar
flags con `iopaint run --help` al estrenarlo.
"""

import shutil
import tempfile
from pathlib import Path

from engines import MODELS, SALIDAS, correr, python_venv

# IOPaint se instala como paquete pip; no hay carpeta vendor/. El marcador .ok que
# escribe el instalador es la prueba de que el paquete quedó bien instalado.
from engines import RAIZ

VENV = ".venv-iopaint_lama"
MODEL_DIR = MODELS / "IOPaint"


def disponible() -> bool:
    # El paquete iopaint vive dentro del venv; basta con que exista el venv con su
    # marcador .ok (lo escribe extras_iopaint_lama.sh tras instalar iopaint).
    return (RAIZ / VENV / ".ok").exists()


def borrar(entrada, mascara, device=None):
    """Generador: cede log y DEVUELVE la ruta de la imagen con el objeto borrado.

    entrada : imagen original.
    mascara : imagen en blanco y negro del mismo encuadre; BLANCO = lo que se
              borra, negro = lo que se conserva. Se reescala sola al tamaño de la
              imagen, así que no hace falta que coincidan los píxeles exactos.
    device  : "cpu" | "cuda" | "mps". Si es None, se autodetecta por hardware.
    """
    import hardware

    if not disponible():
        raise RuntimeError(
            "IOPaint (LaMa) no está instalado. Corre install/extras_iopaint_lama.sh (o .bat)."
        )
    entrada = Path(entrada)
    mascara = Path(mascara)
    if not mascara.exists():
        raise RuntimeError("Falta la máscara: marca en blanco lo que quieres borrar.")

    py = python_venv(VENV, "install/extras_iopaint_lama.sh")
    # El CLI se invoca como módulo del venv para no depender del PATH:
    #   <python> -m iopaint run ...
    if device is None:
        hw = hardware.info_sistema()
        device = "cuda" if hw["cuda"] else ("mps" if hw["mps"] else "cpu")

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    tmp = Path(tempfile.mkdtemp(prefix="videoboost_iopaint_"))
    in_dir, out_dir = tmp / "in", tmp / "out"
    in_dir.mkdir(), out_dir.mkdir()
    # Copiamos la imagen a una carpeta; la máscara la pasamos como archivo único
    # (IOPaint la aplica a todas las imágenes de la carpeta).
    shutil.copy(entrada, in_dir / entrada.name)
    mask_file = tmp / f"mask{mascara.suffix or '.png'}"
    shutil.copy(mascara, mask_file)

    cmd = [
        py, "-m", "iopaint", "run",
        "--model", "lama",
        "--device", device,
        "--image", in_dir,
        "--mask", mask_file,
        "--output", out_dir,
        "--model-dir", MODEL_DIR,
    ]
    try:
        yield f"🧽 IOPaint · LaMa · borrado de objetos · {device}"
        yield "ℹ️ La primera vez descarga el modelo LaMa (~200 MB)."
        yield from correr(cmd)
        resultados = [p for p in out_dir.rglob("*")
                      if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
        if not resultados:
            raise RuntimeError("IOPaint terminó pero no generó ninguna imagen.")
        salida = SALIDAS / f"{entrada.stem}_borrado_lama.png"
        shutil.copy(resultados[0], salida)
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
