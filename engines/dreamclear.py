"""DreamClear (shallowdream204/DreamClear, Apache-2.0) — restauración fotorealista
real-world de máxima calidad (NeurIPS 2024). Modelo de difusión de alta capacidad
sobre PixArt-α-1024 + SwinIR + VAE + T5-XXL (+ LLaVA opcional para caption). Pensado
para fotos degradadas del mundo real; escala x4 por defecto.

CLI documentado (cwd=vendor/DreamClear):
    python -m torch.distributed.launch --nproc_per_node 1 --master_port <p> \
        test.py configs/DreamClear/DreamClear_Test.py \
        --dreamclear_ckpt <DreamClear-1024.pth> \
        --swinir_ckpt   <general_swinir_v1.ckpt> \
        --vae_ckpt      <sd-vae-ft-ema/> \
        --t5_ckpt       <t5-v1_1-xxl/> \
        --llava_ckpt    <llava-v1.6-vicuna-13b/> \
        --lre --cfg_scale 4.5 --color_align wavelet \
        --image_path <carpeta_in> --save_dir <carpeta_out> \
        --mixed_precision fp16 --upscale 4

La salida queda en <save_dir>/results/output/<nombre_original>. Hay tiles latentes
(--latent_tiled_size / --latent_tiled_overlap) para imágenes grandes sin reventar VRAM.

⚠️ MUY pesado: pide MUCHA VRAM (PixArt 1024 + T5-XXL + SwinIR; LLaVA-13B suma ~26 GB
si se usa). En la 4080 (16 GB) probablemente haya que dejar LLaVA fuera y/o bajar los
tiles latentes. Es de difusión SD → SOLO NVIDIA en la práctica. Vive en .venv-dreamclear.

NO PROBADO EN GPU REAL desde aquí (este Mac no tiene CUDA). Verificar en la 4080:
  - que test.py corre sin torch.distributed.launch (lanzamos el script directo;
    expone --local_rank/--local-rank pero el flujo es de inferencia mono-GPU);
  - el flag de tiles y si LLaVA cabe; si no, ver si test.py admite omitir --llava_ckpt;
  - que el config DreamClear_Test.py apunta al PixArt local (lo parcheamos por run,
    igual que FaithDiff con CKPT_PTH.py).
"""

import re
import shutil
import tempfile
from pathlib import Path

from engines import MODELS, SALIDAS, VENDOR, correr, python_venv

DREAMCLEAR_DIR = VENDOR / "DreamClear"
PESOS = MODELS / "DreamClear"
CONFIG = "configs/DreamClear/DreamClear_Test.py"

# Pesos esperados (los baja el instalador a models/DreamClear/). Todos salen del
# repo HF shallowdream204/DreamClear salvo LLaVA (liuhaotian/llava-v1.6-vicuna-13b).
DREAMCLEAR_CKPT = PESOS / "DreamClear-1024.pth"
SWINIR_CKPT = PESOS / "general_swinir_v1.ckpt"
PIXART_CKPT = PESOS / "PixArt-XL-2-1024-MS.pth"
VAE_CKPT = PESOS / "sd-vae-ft-ema"
T5_CKPT = PESOS / "t5-v1_1-xxl"
LLAVA_CKPT = PESOS / "llava-v1.6-vicuna-13b"


def disponible() -> bool:
    """True si el repo y los pesos imprescindibles están presentes. LLaVA es
    opcional (el caption se puede omitir si no cabe en VRAM), así que no se exige."""
    return (
        (DREAMCLEAR_DIR / "test.py").exists()
        and DREAMCLEAR_CKPT.exists()
        and SWINIR_CKPT.exists()
        and PIXART_CKPT.exists()
        and VAE_CKPT.exists()
        and T5_CKPT.exists()
    )


def _parchear_config_pixart():
    """El config DreamClear_Test.py trae un `load_from = '/mnt/.../PixArt-XL-2-1024-MS.pth'`
    hardcodeado (ruta del entorno de los autores). Lo reescribimos para que apunte al
    PixArt local en models/DreamClear/, igual que hacemos con FaithDiff/CKPT_PTH.py."""
    cfg = DREAMCLEAR_DIR / CONFIG
    if not cfg.exists():
        return
    texto = cfg.read_text()
    nuevo = re.sub(
        r"load_from\s*=\s*['\"].*?['\"]",
        f"load_from = r'{PIXART_CKPT}'",
        texto,
        count=1,
    )
    if nuevo != texto:
        cfg.write_text(nuevo)


def mejorar(entrada, escala=4, cfg_scale=4.5, usar_llava=False, tiled=128):
    """Generador: cede log y devuelve la ruta de la imagen restaurada.

    usar_llava=False por defecto: LLaVA-13B suma ~26 GB y rara vez cabe junto al resto
    en una 4080. Si está descargado y hay VRAM de sobra, ponlo en True.
    tiled = tamaño del tile latente (--latent_tiled_size); bajarlo ahorra VRAM en
    imágenes grandes a costa de velocidad.
    """
    import hardware

    if not disponible():
        raise RuntimeError(
            "DreamClear no está instalado. Corre install/extras_dreamclear.sh (o .bat)."
        )
    entrada = Path(entrada)
    py = python_venv(".venv-dreamclear", "install/extras_dreamclear.sh")
    device = "cuda" if hardware.info_sistema()["cuda"] else "cpu"

    _parchear_config_pixart()

    tmp = Path(tempfile.mkdtemp(prefix="videoboost_dreamclear_"))
    in_dir, out_dir = tmp / "in", tmp / "out"
    in_dir.mkdir(), out_dir.mkdir()
    shutil.copy(entrada, in_dir / entrada.name)

    cmd = [
        py, "test.py", CONFIG,
        "--dreamclear_ckpt", DREAMCLEAR_CKPT,
        "--swinir_ckpt", SWINIR_CKPT,
        "--vae_ckpt", VAE_CKPT,
        "--t5_ckpt", T5_CKPT,
        "--lre",
        "--cfg_scale", cfg_scale,
        "--color_align", "wavelet",
        "--image_path", in_dir,
        "--save_dir", out_dir,
        "--mixed_precision", "fp16" if device == "cuda" else "no",
        "--upscale", int(escala),
        "--latent_tiled_size", int(tiled),
    ]
    if usar_llava and LLAVA_CKPT.exists():
        cmd += ["--llava_ckpt", LLAVA_CKPT]

    try:
        yield f"🚀 DreamClear · restauración real-world x{escala} · {device}"
        yield "⚠️ Motor MUY pesado: pide MUCHA VRAM y es LENTO. En la 4080 puede tardar."
        if not (usar_llava and LLAVA_CKPT.exists()):
            yield "ℹ️ Sin LLaVA (ahorra ~26 GB de VRAM); el caption va con prompt vacío."
        yield "ℹ️ La salida llega a <save_dir>/results/output/."
        yield from correr(cmd, cwd=DREAMCLEAR_DIR)

        # Preferimos results/output/, pero buscamos en todo el árbol por si cambió.
        preferida = out_dir / "results" / "output"
        candidatas = list(preferida.rglob("*")) if preferida.exists() else []
        if not candidatas:
            candidatas = list(out_dir.rglob("*"))
        resultados = [
            p for p in candidatas
            if p.is_file() and p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")
        ]
        if not resultados:
            raise RuntimeError("DreamClear terminó pero no generó ninguna imagen.")
        salida = SALIDAS / f"{entrada.stem}_dreamclear.png"
        shutil.copy(resultados[0], salida)
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
