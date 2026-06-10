"""Detección de hardware: decide qué motores y qué nivel puede ofrecer la app.

Niveles:
  3 · Máximo     — NVIDIA con 16 GB+ de VRAM (ej. RTX 4080): SeedVR2 7B + FlashVSR.
  2 · Pro        — NVIDIA 8-12 GB o Mac con chip M y 16 GB+ de RAM unificada: SeedVR2.
  1 · Compatible — cualquier GPU con Vulkan (GTX 1660, AMD, Intel, Mac): Real-ESRGAN etc.
"""

import platform
import shutil
import subprocess
import sys
from functools import lru_cache

from engines import BIN, VENDOR


def es_mac() -> bool:
    return sys.platform == "darwin"


def es_apple_silicon() -> bool:
    return es_mac() and platform.machine() == "arm64"


def _cuda_via_torch():
    try:
        import torch

        if torch.cuda.is_available():
            props = torch.cuda.get_device_properties(0)
            return True, props.name, props.total_memory / 1024**3
    except Exception:
        pass
    return None


def _cuda_via_nvidia_smi():
    if not shutil.which("nvidia-smi"):
        return False, "", 0.0
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10,
        ).stdout.strip().splitlines()
        if out:
            nombre, mem = out[0].rsplit(",", 1)
            return True, nombre.strip(), float(mem) / 1024
    except Exception:
        pass
    return False, "", 0.0


def detectar_cuda():
    """-> (disponible, nombre_gpu, vram_gb). Usa torch si está, si no nvidia-smi."""
    res = _cuda_via_torch()
    if res is not None:
        return res
    return _cuda_via_nvidia_smi()


def detectar_mps() -> bool:
    if not es_apple_silicon():
        return False
    try:
        import torch

        return torch.backends.mps.is_available()
    except Exception:
        # Sin torch instalado aún: en Apple Silicon moderno MPS existe.
        return True


def ram_total_gb() -> float:
    try:
        if es_mac():
            out = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True)
            return int(out.stdout.strip()) / 1024**3
        with open("/proc/meminfo") as f:
            for linea in f:
                if linea.startswith("MemTotal"):
                    return int(linea.split()[1]) / 1024**2
    except Exception:
        pass
    return 0.0


def vulkan_disponible() -> bool:
    """Hay binarios ncnn-Vulkan descargados (al menos Real-ESRGAN)."""
    return any((BIN / "realesrgan").rglob("realesrgan-ncnn-vulkan*")) if (BIN / "realesrgan").exists() else False


def _recomendar_seedvr2(cuda, vram, mps, ram):
    """Modelo DiT, batch_size (regla 4n+1) y bloques a swapear según memoria."""
    if cuda:
        if vram >= 24:
            return "seedvr2_ema_7b_fp16.safetensors", 21, 0
        if vram >= 14:  # RTX 4080 16 GB
            return "seedvr2_ema_7b_fp8_e4m3fn.safetensors", 13, 0
        if vram >= 10:
            return "seedvr2_ema_7b-Q4_K_M.gguf", 5, 16
        return "seedvr2_ema_3b-Q8_0.gguf", 5, 24
    if mps:
        # En Apple Silicon la memoria es unificada: sin BlockSwap (no aplica) y sin fp8.
        if ram >= 48:
            return "seedvr2_ema_7b_fp16.safetensors", 9, 0
        if ram >= 24:
            return "seedvr2_ema_3b_fp16.safetensors", 5, 0
        return "seedvr2_ema_3b_fp16.safetensors", 1, 0
    return "seedvr2_ema_3b-Q4_K_M.gguf", 1, 32


@lru_cache(maxsize=1)
def info_sistema() -> dict:
    cuda, gpu_nombre, vram = detectar_cuda()
    mps = detectar_mps()
    ram = ram_total_gb()

    seedvr2_instalado = (VENDOR / "seedvr2" / "inference_cli.py").exists()
    modelo, batch, swap = _recomendar_seedvr2(cuda, vram, mps, ram)

    if cuda and vram >= 16:
        nivel = 3
    elif (cuda and vram >= 8) or (mps and ram >= 16):
        nivel = 2
    else:
        nivel = 1

    return {
        "so": platform.system(),
        "es_mac": es_mac(),
        "apple_silicon": es_apple_silicon(),
        "cuda": cuda,
        "gpu": gpu_nombre,
        "vram_gb": round(vram, 1),
        "mps": mps,
        "ram_gb": round(ram, 1),
        "vulkan": vulkan_disponible(),
        "ffmpeg": shutil.which("ffmpeg") is not None or any(BIN.rglob("ffmpeg*")) if BIN.exists() else shutil.which("ffmpeg") is not None,
        "seedvr2": seedvr2_instalado and (cuda or mps),
        "flashvsr": (VENDOR / "FlashVSR").exists() and cuda,
        "nivel": nivel,
        "seedvr2_modelo": modelo,
        "seedvr2_batch": batch,
        "seedvr2_swap": swap,
    }


def resumen() -> str:
    hw = info_sistema()
    if hw["cuda"]:
        gpu = f"NVIDIA {hw['gpu']} · {hw['vram_gb']} GB VRAM (CUDA)"
    elif hw["mps"]:
        gpu = f"Apple Silicon · {hw['ram_gb']} GB de memoria unificada (Metal/MPS)"
    else:
        gpu = "GPU genérica (solo motores Vulkan)"
    nombres = {3: "Máximo", 2: "Pro", 1: "Compatible"}
    return f"**{gpu}** — Nivel **{hw['nivel']} · {nombres[hw['nivel']]}**"


if __name__ == "__main__":
    import json

    print(json.dumps(info_sistema(), indent=2, ensure_ascii=False))
