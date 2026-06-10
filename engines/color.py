"""DDColor (ICCV 2023) — colorización fotorrealista de imágenes en blanco y negro.

Es el "colorize model" tipo HitPaw, pero más nuevo y mejor que DeOldify: doble
decodificador que produce colores ricos y coherentes. Da vida a fotos antiguas.

Funciona en CUDA (NVIDIA). En Mac el script oficial cae a **CPU** (no usa MPS):
más lento pero funciona para imágenes sueltas. Vive en .venv-color y se instala
con install/extras_color.(sh|bat). Licencia Apache 2.0.
"""

import shutil
import tempfile
from pathlib import Path

from engines import MODELS, RAIZ, SALIDAS, VENDOR, correr

DDCOLOR_DIR = VENDOR / "DDColor"
PESOS = MODELS / "DDColor" / "pytorch_model.pt"


def _python_venv() -> str:
    venv = RAIZ / ".venv-color"
    for rel in ("bin/python", "Scripts/python.exe"):
        p = venv / rel
        if p.exists():
            return str(p)
    raise RuntimeError(
        "No existe el entorno .venv-color. Corre install/extras_color.sh (o .bat)."
    )


def disponible() -> bool:
    return (DDCOLOR_DIR / "scripts" / "infer.py").exists() and PESOS.exists()


def colorizar(entrada, tamano=512):
    """Generador: cede log y devuelve la ruta de la imagen coloreada."""
    import hardware

    if not disponible():
        raise RuntimeError(
            "DDColor no está instalado. Corre install/extras_color.sh (o .bat)."
        )
    entrada = Path(entrada)
    py = _python_venv()

    tmp = Path(tempfile.mkdtemp(prefix="videoboost_color_"))
    in_dir, out_dir = tmp / "in", tmp / "out"
    in_dir.mkdir(), out_dir.mkdir()
    shutil.copy(entrada, in_dir / entrada.name)

    cmd = [
        py, "scripts/infer.py",
        "--model_path", PESOS,
        "--model_size", "large",
        "--input", in_dir,
        "--output", out_dir,
        "--input_size", tamano,
    ]
    en_mac = hardware.info_sistema()["es_mac"]
    try:
        yield f"🎨 DDColor · entrada {tamano}px" + (" · (Mac: corre en CPU, paciencia)" if en_mac else "")
        yield from correr(cmd, cwd=DDCOLOR_DIR)
        resultados = [p for p in out_dir.rglob("*")
                      if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
        if not resultados:
            raise RuntimeError("DDColor terminó pero no generó ninguna imagen.")
        salida = SALIDAS / f"{entrada.stem}_color_ddcolor.png"
        shutil.copy(resultados[0], salida)
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
