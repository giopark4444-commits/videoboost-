"""InstantIR (instantX-research) — restauración de imágenes por difusión con
referencia generativa instantánea.

Alternativa a SUPIR para la pestaña de imágenes: calidad comparable o superior,
pero más rápida (no necesita los 25-35 pasos lentos de SUPIR) y con licencia
**Apache 2.0** (uso comercial libre, a diferencia de SUPIR/HYPIR).

SOLO NVIDIA/CUDA: está construido sobre SDXL + DINOv2 y los autores no dan
soporte para Apple Silicon. En Mac usar HYPIR o SeedVR2.

Vive en .venv-instantir (SDXL/diffusers chocan con el resto). Se instala con
install/extras_instantir.(sh|bat). Permite un prompt opcional que guía la
restauración, igual que HYPIR/SUPIR.
"""

import shutil
import sys
import tempfile
from pathlib import Path

from engines import MODELS, RAIZ, SALIDAS, VENDOR, correr

INSTANTIR_DIR = VENDOR / "InstantIR"
PESOS = MODELS / "InstantIR"  # checkpoint de InstantX/InstantIR
SDXL = MODELS / "sdxl-base-1.0"
DINOV2 = MODELS / "dinov2-large"


def _python_venv() -> str:
    venv = RAIZ / ".venv-instantir"
    for rel in ("bin/python", "Scripts/python.exe"):
        p = venv / rel
        if p.exists():
            return str(p)
    raise RuntimeError(
        "No existe el entorno .venv-instantir. Corre install/extras_instantir.sh (o .bat)."
    )


def disponible() -> bool:
    return (INSTANTIR_DIR / "infer.py").exists() and PESOS.exists()


def mejorar(entrada, prompt="", pasos=30, cfg=7.0, ancho=None, alto=None):
    """Generador: cede log y devuelve la ruta de salida."""
    import hardware

    if not hardware.info_sistema()["cuda"]:
        raise RuntimeError("InstantIR requiere GPU NVIDIA/CUDA. En Mac usa HYPIR o SeedVR2.")
    if not disponible():
        raise RuntimeError(
            "InstantIR no está instalado. Corre install/extras_instantir.sh (o .bat)."
        )
    entrada = Path(entrada)
    py = _python_venv()

    tmp = Path(tempfile.mkdtemp(prefix="videoboost_instantir_"))
    in_dir, out_dir = tmp / "in", tmp / "out"
    in_dir.mkdir(), out_dir.mkdir()
    shutil.copy(entrada, in_dir / entrada.name)

    cmd = [
        py, "infer.py",
        "--sdxl_path", SDXL,
        "--vision_encoder_path", DINOV2,
        "--instantir_path", PESOS,
        "--test_path", in_dir,
        "--out_path", out_dir,
        "--num_inference_steps", pasos,
        "--cfg", cfg,
        "--batch_size", 1,
    ]
    if prompt:
        cmd += ["--prompt", prompt]
    if ancho and alto:
        cmd += ["--width", ancho, "--height", alto]

    try:
        yield f"🚀 InstantIR · {pasos} pasos · cfg {cfg}" + (f" · prompt: «{prompt}»" if prompt else "")
        yield "ℹ️ Primera vez: usa SDXL + DINOv2 + pesos InstantIR ya descargados por el instalador."
        yield from correr(cmd, cwd=INSTANTIR_DIR)
        resultados = [p for p in out_dir.rglob("*")
                      if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
        if not resultados:
            raise RuntimeError("InstantIR terminó pero no generó ninguna imagen.")
        salida = SALIDAS / f"{entrada.stem}_instantir.png"
        shutil.copy(resultados[0], salida)
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
