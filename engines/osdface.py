"""OSDFace (difusión de 1 paso, CVPR 2025) — restauración de caras con textura
muy orgánica (pestañas, cejas, hebras de pelo, piel). Fue base del ganador del
reto NTIRE 2026 de caras reales.

⚠️ SIN LICENCIA: el repo no incluye archivo de licencia → por defecto "todos los
derechos reservados". **No apto para la build de venta** sin permiso por escrito
de los autores (jkwang28 et al.). Aquí queda como motor de PRUEBA / uso personal.

CLI: infer.py --input_image <carpeta> --output_dir <carpeta>
--pretrained_model_name_or_path stabilityai/stable-diffusion-2-1-base
--img_encoder_weight <ckpt>/associate_2.ckpt --ckpt_path <ckpt> --merge_lora.
Base SD2.1 (auto de HF); pesos OSDFace de Google Drive (los baja el instalador).
Vive en .venv-osdface. Solo NVIDIA. NO PROBADO EN GPU REAL desde aquí.
"""

import shutil
import tempfile
from pathlib import Path

from engines import MODELS, SALIDAS, VENDOR, correr, python_venv

OSDFACE_DIR = VENDOR / "OSDFace"
CKPT_DIR = MODELS / "OSDFace"   # pesos descargados (associate_2.ckpt, etc.)

# Marca para la UI: este motor no puede ir en una build comercial.
NO_COMERCIAL = True


def disponible() -> bool:
    return (OSDFACE_DIR / "infer.py").exists() and CKPT_DIR.exists() \
        and (CKPT_DIR / "associate_2.ckpt").exists()


def mejorar(entrada):
    """Generador: cede log y devuelve la ruta de la cara restaurada."""
    if not disponible():
        raise RuntimeError(
            "OSDFace no está instalado. Corre install/extras_osdface.sh (o .bat)."
        )
    entrada = Path(entrada)
    py = python_venv(".venv-osdface", "install/extras_osdface.sh")

    tmp = Path(tempfile.mkdtemp(prefix="videoboost_osdface_"))
    in_dir, out_dir = tmp / "in", tmp / "out"
    in_dir.mkdir(), out_dir.mkdir()
    shutil.copy(entrada, in_dir / entrada.name)

    cmd = [
        py, "infer.py",
        "--input_image", in_dir,
        "--output_dir", out_dir,
        "--pretrained_model_name_or_path", "stabilityai/stable-diffusion-2-1-base",
        "--img_encoder_weight", CKPT_DIR / "associate_2.ckpt",
        "--ckpt_path", CKPT_DIR,
        "--merge_lora",
        "--gpu_id", 0,
    ]
    try:
        yield "🚀 OSDFace · difusión 1 paso (⚠️ uso personal — sin licencia comercial)"
        yield "ℹ️ La primera vez descarga SD 2.1 (HuggingFace) + pesos OSDFace."
        yield from correr(cmd, cwd=OSDFACE_DIR)
        resultados = [p for p in out_dir.rglob("*")
                      if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
        if not resultados:
            raise RuntimeError("OSDFace terminó pero no generó ninguna imagen.")
        salida = SALIDAS / f"{entrada.stem}_osdface.png"
        shutil.copy(resultados[0], salida)
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
