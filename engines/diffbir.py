"""DiffBIR (XPixelGroup, Apache-2.0) — restauración ciega por difusión con prior
de Stable Diffusion. Muy buen detalle orgánico tanto en caras como en escena
completa; sirve para fotos/película degradada y para humanos.

CLI estándar: inference.py --task {sr,face,face_background,denoise} --input
--output --upscale --version v2.1 --device cuda --precision fp16. Los pesos se
auto-descargan de HuggingFace en el primer uso. Vive en .venv-diffbir.

Solo NVIDIA en la práctica (difusión SDXL/SD2.1); el CLI admite --device cpu
pero es lentísimo. NO PROBADO EN GPU REAL desde aquí: verificar flags en la 4080.
"""

import shutil
import tempfile
from pathlib import Path

from engines import SALIDAS, VENDOR, correr, python_venv

DIFFBIR_DIR = VENDOR / "DiffBIR"

# Tareas expuestas: super-resolución general (cine/foto) y restauración de
# caras en imagen completa (humanos). "face" exige cara alineada; usamos
# "face_background" que maneja la imagen entera.
TAREAS = ["face_background", "sr", "denoise"]


def disponible() -> bool:
    return (DIFFBIR_DIR / "inference.py").exists()


def mejorar(entrada, tarea="face_background", escala=2, pasos=None):
    """Generador: cede log y devuelve la ruta de la imagen restaurada."""
    import hardware

    if not disponible():
        raise RuntimeError(
            "DiffBIR no está instalado. Corre install/extras_diffbir.sh (o .bat)."
        )
    entrada = Path(entrada)
    py = python_venv(".venv-diffbir", "install/extras_diffbir.sh")
    device = "cuda" if hardware.info_sistema()["cuda"] else "cpu"

    tmp = Path(tempfile.mkdtemp(prefix="videoboost_diffbir_"))
    in_dir, out_dir = tmp / "in", tmp / "out"
    in_dir.mkdir(), out_dir.mkdir()
    shutil.copy(entrada, in_dir / entrada.name)

    cmd = [
        py, "inference.py",
        "--task", tarea,
        "--upscale", int(escala),
        "--version", "v2.1",
        "--captioner", "none",       # evita cargar LLaVA (caption pesado)
        "--cfg_scale", "8",
        "--input", in_dir,
        "--output", out_dir,
        "--device", device,
        "--precision", "fp16" if device == "cuda" else "fp32",
    ]
    if pasos:
        cmd += ["--steps", int(pasos)]
    try:
        yield f"🚀 DiffBIR · {tarea} · x{escala} · {device}"
        yield "ℹ️ La primera vez descarga los pesos (SD 2.1 + DiffBIR) de HuggingFace."
        yield from correr(cmd, cwd=DIFFBIR_DIR)
        resultados = [p for p in out_dir.rglob("*")
                      if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
        if not resultados:
            raise RuntimeError("DiffBIR terminó pero no generó ninguna imagen.")
        salida = SALIDAS / f"{entrada.stem}_diffbir.png"
        shutil.copy(resultados[0], salida)
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
