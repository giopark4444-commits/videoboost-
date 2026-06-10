"""FaithDiff (CVPR 2025) — restauración fiel de imágenes por difusión sobre SDXL.

Alternativa de **licencia libre (MIT)** a los motores no comerciales: en los benchmarks de su
paper supera a SUPIR y es ~4× más rápido, y está pensado justo para rejuvenecer
fotos y películas antiguas. Apto para uso comercial.

SOLO NVIDIA/CUDA (construido sobre SDXL). En Mac usa SeedVR2.

Para no descargar LLaVA-13B (~26 GB) solo para autogenerar un caption, saltamos
ese paso (usamos test_wo_llava.py) y construimos el caption a partir de un prompt
opcional del usuario, como InstantIR. Vive en .venv-faithdiff y se instala
con install/extras_faithdiff.(sh|bat).
"""

import json
import shutil
import tempfile
from pathlib import Path

from engines import MODELS, SALIDAS, VENDOR, correr, python_venv

FAITHDIFF_DIR = VENDOR / "FaithDiff"
PESOS = MODELS / "FaithDiff"  # FaithDiff.bin + Real_4_SDXL/ + VAE_FP16/


def _bin_faithdiff():
    """Localiza el archivo de pesos FaithDiff (*.bin) descargado."""
    cands = sorted(PESOS.glob("*.bin"))
    for c in cands:
        if "faithdiff" in c.name.lower():
            return c
    return cands[0] if cands else None


def disponible() -> bool:
    return ((FAITHDIFF_DIR / "test_wo_llava.py").exists()
            and (PESOS / "Real_4_SDXL").exists()
            and _bin_faithdiff() is not None)


def _escribir_ckpt_pth():
    """Genera CKPT_PTH.py en el repo de FaithDiff con rutas absolutas a los pesos.

    El repo importa estas constantes; las reescribimos en cada ejecución para
    que apunten a models/FaithDiff/ sin depender del directorio de trabajo."""
    contenido = (
        f"SDXL_PATH = {str(PESOS / 'Real_4_SDXL') + '/'!r}\n"
        f"FAITHDIFF_PATH = {str(_bin_faithdiff())!r}\n"
        f"VAE_FP16_PATH = {str(PESOS / 'VAE_FP16') + '/'!r}\n"
        f"BSRNet_PATH = {str(PESOS / 'BSRNet.pth')!r}\n"
        "LLAVA_CLIP_PATH = ''\n"
        "LLAVA_MODEL_PATH = ''\n"
    )
    (FAITHDIFF_DIR / "CKPT_PTH.py").write_text(contenido)


def mejorar(entrada, prompt="", escala=2, pasos=20, cfg=5.0, fp8=False):
    """Generador: cede log y devuelve la ruta de salida."""
    import hardware

    if not hardware.info_sistema()["cuda"]:
        raise RuntimeError("FaithDiff requiere GPU NVIDIA/CUDA. En Mac usa SeedVR2.")
    if not disponible():
        raise RuntimeError(
            "FaithDiff no está instalado. Corre install/extras_faithdiff.sh (o .bat)."
        )
    entrada = Path(entrada)
    py = python_venv(".venv-faithdiff", "install/extras_faithdiff.sh")
    _escribir_ckpt_pth()

    tmp = Path(tempfile.mkdtemp(prefix="videoboost_faithdiff_"))
    in_dir, json_dir, out_dir = tmp / "in", tmp / "json", tmp / "out"
    for d in (in_dir, json_dir, out_dir):
        d.mkdir()
    shutil.copy(entrada, in_dir / entrada.name)

    # test_wo_llava.py descarta las 3 primeras palabras del caption (formato LLaVA
    # "the image shows…"); por eso prefijamos esas 3 palabras al prompt real.
    descripcion = prompt.strip() or "a high quality, sharp, detailed photograph"
    caption = "the image shows " + descripcion
    (json_dir / f"{entrada.stem}.json").write_text(json.dumps({"caption": caption}))

    cmd = [
        py, "test_wo_llava.py",
        "--img_dir", in_dir,
        "--json_dir", json_dir,
        "--save_dir", out_dir,
        "--upscale", escala,
        "--guidance_scale", cfg,
        "--num_inference_steps", pasos,
    ]
    if fp8:
        cmd.append("--use_fp8")

    try:
        yield (f"🚀 FaithDiff · x{escala} · {pasos} pasos · cfg {cfg}"
               + (f" · prompt: «{prompt}»" if prompt else ""))
        yield "ℹ️ Sin LLaVA: usa SDXL + VAE + pesos FaithDiff ya descargados por el instalador."
        yield from correr(cmd, cwd=FAITHDIFF_DIR)
        resultados = [p for p in out_dir.rglob("*")
                      if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
        if not resultados:
            raise RuntimeError("FaithDiff terminó pero no generó ninguna imagen.")
        salida = SALIDAS / f"{entrada.stem}_faithdiff.png"
        shutil.copy(resultados[0], salida)
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
