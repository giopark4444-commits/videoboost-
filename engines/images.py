"""Motores de restauración de imágenes: HYPIR (por defecto) y SUPIR (máximo detalle).

Cada uno vive en su propio venv (.venv-imagenes / .venv-supir) porque sus
dependencias de diffusers no son compatibles entre sí ni con las de SeedVR2.
Se instalan con install/extras_imagenes.(sh|bat).

Licencia: HYPIR y SUPIR son de uso NO comercial sin permiso de sus autores.
Para uso personal no hay restricción.
"""

import shutil
import sys
import tempfile
from pathlib import Path

from engines import MODELS, RAIZ, SALIDAS, VENDOR, correr

HYPIR_DIR = VENDOR / "HYPIR"
SUPIR_DIR = VENDOR / "SUPIR"
HYPIR_PESOS = MODELS / "HYPIR" / "HYPIR_sd2.pth"

# Lista oficial de módulos LoRA del README de HYPIR (un solo argumento separado por comas).
_LORA_MODULES = ",".join([
    "to_k", "to_q", "to_v", "to_out.0", "conv", "conv1", "conv2",
    "conv_shortcut", "conv_out", "proj_in", "proj_out", "ff.net.2", "ff.net.0.proj",
])


def _python_venv(nombre: str) -> str:
    venv = RAIZ / nombre
    for rel in ("bin/python", "Scripts/python.exe"):
        p = venv / rel
        if p.exists():
            return str(p)
    raise RuntimeError(
        f"No existe el entorno {nombre}. Corre install/extras_imagenes.sh (o .bat)."
    )


def hypir_disponible() -> bool:
    return (HYPIR_DIR / "test.py").exists() and HYPIR_PESOS.exists()


def supir_disponible() -> bool:
    return (SUPIR_DIR / "test.py").exists()


def mejorar_hypir(entrada, prompt="", escala=2):
    """HYPIR: restauración SOTA en 1 paso, controlable con prompt de texto."""
    import hardware

    entrada = Path(entrada)
    py = _python_venv(".venv-imagenes")
    device = "cuda" if hardware.info_sistema()["cuda"] else "mps"

    tmp = Path(tempfile.mkdtemp(prefix="videoboost_hypir_"))
    lq, txt, out = tmp / "lq", tmp / "txt", tmp / "out"
    lq.mkdir(), txt.mkdir(), out.mkdir()
    shutil.copy(entrada, lq / entrada.name)
    (txt / f"{entrada.stem}.txt").write_text(prompt or "", encoding="utf-8")

    cmd = [
        py, "test.py",
        "--base_model_type", "sd2",
        "--base_model_path", "stabilityai/stable-diffusion-2-1-base",
        "--model_t", 200, "--coeff_t", 200,
        "--lora_rank", 256, "--lora_modules", _LORA_MODULES,
        "--weight_path", HYPIR_PESOS,
        "--patch_size", 512, "--stride", 256,
        "--lq_dir", lq, "--txt_dir", txt, "--output_dir", out,
        "--scale_by", "factor", "--upscale", escala,
        "--seed", 231, "--device", device,
    ]
    try:
        yield f"🚀 HYPIR · x{escala} · device {device}" + (f" · prompt: «{prompt}»" if prompt else "")
        yield from correr(cmd, cwd=HYPIR_DIR)
        resultados = [p for p in out.rglob("*") if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
        if not resultados:
            raise RuntimeError("HYPIR terminó pero no generó ninguna imagen.")
        salida = SALIDAS / f"{entrada.stem}_x{escala}_hypir.png"
        shutil.copy(resultados[0], salida)
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def mejorar_supir(entrada, escala=2, version="Q"):
    """SUPIR: máximo detalle reconstruido. Pesado; pensado para la RTX 4080.

    Requiere haber configurado los pesos según el README de SUPIR
    (install/extras_imagenes.sh --supir deja las instrucciones).
    """
    entrada = Path(entrada)
    py = _python_venv(".venv-supir")

    tmp = Path(tempfile.mkdtemp(prefix="videoboost_supir_"))
    img_dir, save_dir = tmp / "in", tmp / "out"
    img_dir.mkdir(), save_dir.mkdir()
    shutil.copy(entrada, img_dir / entrada.name)

    cmd = [
        py, "test.py",
        "--img_dir", img_dir, "--save_dir", save_dir,
        "--SUPIR_sign", version, "--upscale", escala,
    ]
    try:
        yield f"🚀 SUPIR-v0{version} · x{escala} (esto tarda: 25-35 pasos de difusión)"
        yield from correr(cmd, cwd=SUPIR_DIR)
        resultados = [p for p in save_dir.rglob("*") if p.suffix.lower() in (".png", ".jpg", ".jpeg")]
        if not resultados:
            raise RuntimeError("SUPIR terminó pero no generó ninguna imagen.")
        salida = SALIDAS / f"{entrada.stem}_x{escala}_supir.png"
        shutil.copy(resultados[0], salida)
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
