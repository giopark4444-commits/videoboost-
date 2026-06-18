"""SeedVR2 (ByteDance) — restauración de video/imagen por difusión en un paso.

Consistencia temporal nativa (sin parpadeo). Es el motor "nivel Topaz" del
proyecto. Usa el CLI standalone de la integración de numz
(vendor/seedvr2/inference_cli.py), que descarga los modelos de HuggingFace a
models/SEEDVR2 en el primer uso.

Funciona con CUDA (NVIDIA) y con MPS (Mac con chip M). En Mac no se usa
BlockSwap: con memoria unificada no tiene sentido y el CLI lo desactiva.
"""

import sys
from pathlib import Path

from engines import MODELS, SALIDAS, VENDOR, correr
from engines import ffmpeg_utils as ff

CLI = VENDOR / "seedvr2" / "inference_cli.py"

MODELOS = [
    "seedvr2_ema_7b_fp16.safetensors",        # máxima calidad (24 GB VRAM / Mac 48 GB+)
    "seedvr2_ema_7b_fp8_e4m3fn.safetensors",  # RTX 4080 16 GB (solo CUDA)
    "seedvr2_ema_7b-Q4_K_M.gguf",             # 10-14 GB VRAM
    "seedvr2_ema_3b_fp16.safetensors",        # Mac con 16-32 GB
    "seedvr2_ema_3b_fp8_e4m3fn.safetensors",
    "seedvr2_ema_3b-Q8_0.gguf",               # 8 GB VRAM
    "seedvr2_ema_3b-Q4_K_M.gguf",             # 6 GB VRAM (lento)
]

BATCHES = [1, 5, 9, 13, 21, 33]  # regla 4n+1 del modelo


def disponible() -> bool:
    return CLI.exists()


def mejorar(entrada, resolucion=1080, modelo=None, batch_size=None, es_video=True):
    """Generador: cede log y devuelve la ruta de salida."""
    import hardware

    if not disponible():
        raise RuntimeError(
            "SeedVR2 no está instalado. Corre el instalador de tu plataforma "
            "(install/instalar_mac.sh o install/INSTALAR_NVIDIA.bat)."
        )
    hw = hardware.info_sistema()
    entrada = Path(entrada)
    modelo = modelo or hw["seedvr2_modelo"]
    batch = int(batch_size or hw["seedvr2_batch"])
    sufijo = entrada.suffix if not es_video else ".mp4"
    salida = SALIDAS / f"{entrada.stem}_seedvr2_{resolucion}p{sufijo}"

    cmd = [
        sys.executable, CLI, entrada,
        "--output", salida,
        "--resolution", resolucion,          # lado corto objetivo
        "--dit_model", modelo,
        "--model_dir", MODELS / "SEEDVR2",
        "--color_correction", "lab",
        "--attention_mode", "sdpa",          # el modo más compatible (CUDA y MPS)
    ]
    if es_video:
        cmd += ["--batch_size", batch, "--video_backend", "ffmpeg", "--temporal_overlap", 3]

    if hw["cuda"]:
        if hw["seedvr2_swap"] > 0:
            cmd += [
                "--blocks_to_swap", hw["seedvr2_swap"],
                "--dit_offload_device", "cpu",
                "--vae_offload_device", "cpu",
                "--vae_encode_tiled", "--vae_decode_tiled",
            ]
        elif resolucion >= 4320:
            # 8K output: activar tiling de VAE incluso con VRAM suficiente
            cmd += ["--vae_encode_tiled", "--vae_decode_tiled"]
    elif hw["mps"]:
        # Nada de BlockSwap/fp8 en Mac; el tiling de VAE sí ayuda con videos grandes.
        if resolucion >= 1440:
            cmd += ["--vae_encode_tiled", "--vae_decode_tiled"]

    yield f"🚀 SeedVR2 · modelo {modelo} · resolución {resolucion}p · batch {batch if es_video else '—'}"
    yield "ℹ️ La primera vez descargará el modelo de HuggingFace (puede tardar)."
    if es_video and hw.get("mps") and not hw.get("cuda"):
        yield (
            "🐢 OJO en Mac: SeedVR2 en PyTorch/MPS va MUY lento (≈25 s por frame), "
            "casi siempre demasiado para vídeo (un clip de pocos segundos puede "
            "tardar horas). NO está colgado, es la versión más lenta en Apple "
            "Silicon. Recomendado en Mac: usa «SeedVR2 (MLX)» (mismo modelo, ~5× "
            "más rápido) o «MetalFX»/«Real-ESRGAN» si solo quieres escalar rápido."
        )
    # El CLI exige `ffmpeg` en el PATH para --video_backend ffmpeg; garantizamos
    # que lo encuentre aunque solo tengamos el de imageio-ffmpeg o bin/.
    yield from correr(cmd, cwd=CLI.parent, env=ff.entorno_con_ffmpeg())
    return str(salida)
