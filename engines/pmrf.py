"""PMRF (Posterior-Mean Rectified Flow, MIT) — restauración de caras muy natural
y orgánica (top en NTIRE 2025). Licencia MIT, la más limpia para uso comercial.

CLI: inference.py --ckpt_path ohayonguy/PMRF_blind_face_image_restoration
--ckpt_path_is_huggingface --lq_data_path <in> --output_dir <out>
--num_flow_steps 25. El checkpoint se auto-descarga de HuggingFace. Vive en
.venv-pmrf.

IMPORTANTE: el modelo está entrenado para **caras cuadradas y alineadas** (una
cara). Para fotos generales con caras sin alinear, DiffBIR (face_background) es
mejor opción. Solo NVIDIA en la práctica. NO PROBADO EN GPU REAL desde aquí.
"""

import shutil
import tempfile
from pathlib import Path

from engines import SALIDAS, VENDOR, correr, python_venv

PMRF_DIR = VENDOR / "PMRF"
HF_CKPT = "ohayonguy/PMRF_blind_face_image_restoration"


def disponible() -> bool:
    return (PMRF_DIR / "inference.py").exists()


def mejorar(entrada, pasos=25):
    """Generador: cede log y devuelve la ruta de la cara restaurada.

    Espera una imagen de cara cuadrada y alineada (ver nota del módulo).
    """
    if not disponible():
        raise RuntimeError(
            "PMRF no está instalado. Corre install/extras_pmrf.sh (o .bat)."
        )
    entrada = Path(entrada)
    py = python_venv(".venv-pmrf", "install/extras_pmrf.sh")

    tmp = Path(tempfile.mkdtemp(prefix="videoboost_pmrf_"))
    in_dir, out_dir = tmp / "in", tmp / "out"
    in_dir.mkdir(), out_dir.mkdir()
    shutil.copy(entrada, in_dir / entrada.name)

    cmd = [
        py, "inference.py",
        "--ckpt_path", HF_CKPT,
        "--ckpt_path_is_huggingface",
        "--lq_data_path", in_dir,
        "--output_dir", out_dir,
        "--batch_size", 1,
        "--num_flow_steps", int(pasos),
    ]
    try:
        yield f"🚀 PMRF · {pasos} pasos de flow"
        yield "ℹ️ Espera caras alineadas (1 cara). La primera vez descarga el modelo de HuggingFace."
        yield from correr(cmd, cwd=PMRF_DIR)
        resultados = [p for p in out_dir.rglob("*")
                      if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
        if not resultados:
            raise RuntimeError("PMRF terminó pero no generó ninguna imagen.")
        salida = SALIDAS / f"{entrada.stem}_pmrf.png"
        shutil.copy(resultados[0], salida)
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
