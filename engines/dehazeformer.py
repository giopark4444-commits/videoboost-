"""DehazeFormer (IDKiro, MIT) — quita neblina/niebla atmosférica de una imagen con
un Transformer eficiente (variante de Swin adaptada a dehazing). No es difusión:
una sola pasada determinista, así que es rápido y no inventa textura. Recupera
contraste y color en fotos/frames con bruma, calima o neblina de paisaje.

Incluye un MODO RÁPIDO opcional con gUNet (mismo autor, MIT): una U-Net con bloques
"gated" muy ligera, pensada como red base veloz cuando no hace falta el Transformer.

El repo oficial (test.py) está cableado a CUDA, exige imágenes con ground-truth
(PairLoader) y calcula PSNR/SSIM: inútil para "quítale la neblina a ESTA imagen".
Por eso, igual que FaithDiff/FlashVSR en este proyecto, el engine ESCRIBE un script
de inferencia mínimo (`_vb_infer.py`) dentro del repo vendorizado que:
  · construye la red con el mismo factory `eval(modelo.replace('-','_'))()`,
  · carga el .pth con el `single()` del repo (quita el prefijo "module." de DataParallel),
  · elige device cuda/mps/cpu (NO está clavado a .cuda(), por eso corre en Mac),
  · rellena la entrada a múltiplo de 16 (los 4 stages de stride 2 lo exigen) y recorta,
  · procesa SOLO la imagen con neblina (sin ground-truth) reusando read_img/write_img.

Como es un Transformer/U-Net convolucional puro (sin SDXL), corre tanto en NVIDIA
como en Mac (MPS/CPU) → plataforma "ambas". Vive en .venv-dehazeformer. NO PROBADO
EN GPU/MPS REAL desde aquí: verificar pesos y el factory en la 4080 y en la M1 Max.
"""

import shutil
import tempfile
from pathlib import Path

from engines import SALIDAS, VENDOR, correr, python_venv

DEHAZEFORMER_DIR = VENDOR / "DehazeFormer"
GUNET_DIR = VENDOR / "gUNet"

# Variantes expuestas. Para cada una: (carpeta_repo, exp_por_defecto). El .pth vive
# en {repo}/saved_models/{exp}/{modelo}.pth (estructura oficial de ambos repos).
# Usamos "indoor" (RESIDE-IN): es el peso preentrenado que el repo publica y
# documenta como ejemplo (save_models/indoor/dehazeformer-b.pth), y el único con
# URL de descarga verificada. Generaliza razonablemente a neblina real.
MODELOS = {
    # DehazeFormer (Transformer, calidad): base (-b) y grande (-l).
    "dehazeformer-b": (DEHAZEFORMER_DIR, "indoor"),
    "dehazeformer-l": (DEHAZEFORMER_DIR, "indoor"),
    # gUNet (modo rápido, U-Net gated): base (_b).
    "gunet_b": (GUNET_DIR, "indoor"),
}

# Script de inferencia que se inyecta en el repo (reusa SUS utils y SU factory).
# Hazy-only, device-agnóstico, padding a múltiplo de 16. Sin dependencias extra.
_INFER = r'''
import os, sys, argparse
import numpy as np
import torch
import torch.nn.functional as F
from collections import OrderedDict

from utils import read_img, write_img, hwc_to_chw, chw_to_hwc
from models import *

p = argparse.ArgumentParser()
p.add_argument("--model", required=True)      # ej. dehazeformer-b / gunet_b
p.add_argument("--weight", required=True)     # ruta al .pth
p.add_argument("--input", required=True)      # imagen con neblina
p.add_argument("--output", required=True)     # ruta de salida (png)
p.add_argument("--device", default="cpu")     # cuda / mps / cpu
a = p.parse_args()

# Mismo factory que el test.py OFICIAL del repo: nombre -> función (guiones a
# guion bajo). El valor de --model NO es entrada del usuario: viene del dict fijo
# MODELOS del engine, así que el eval() no expone ejecución arbitraria (se replica
# tal cual la línea `eval(args.model.replace('-','_'))()` de upstream).
net = eval(a.model.replace("-", "_"))()  # noqa: S307 — factory controlado del repo

# Carga del checkpoint quitando el prefijo "module." (DataParallel), igual que
# la función single() del repo. Algunos pesos vienen bajo la clave 'state_dict'.
# weights_only=True: solo tensores (los .pth oficiales no traen objetos pickle);
# evita ejecución arbitraria al deserializar. Si una versión vieja de torch no
# soporta el flag, se reintenta sin él (mismo comportamiento que upstream).
try:
    ckpt = torch.load(a.weight, map_location="cpu", weights_only=True)
except TypeError:
    ckpt = torch.load(a.weight, map_location="cpu")
state = ckpt.get("state_dict", ckpt) if isinstance(ckpt, dict) else ckpt
clean = OrderedDict()
for k, v in state.items():
    clean[k[7:] if k.startswith("module.") else k] = v
net.load_state_dict(clean)

dev = torch.device(a.device)
net = net.to(dev).eval()

# read_img devuelve HWC en [0,1]; la red trabaja en [-1,1].
img = read_img(a.input)
x = torch.from_numpy(hwc_to_chw(img)).unsqueeze(0).to(dev) * 2 - 1

# Padding reflexivo a múltiplo de 16 (4 etapas de stride 2). Se recorta al final.
_, _, H, W = x.shape
factor = 16
ph = (factor - H % factor) % factor
pw = (factor - W % factor) % factor
x = F.pad(x, (0, pw, 0, ph), mode="reflect")

with torch.no_grad():
    y = net(x).clamp_(-1, 1)
y = y[:, :, :H, :W] * 0.5 + 0.5          # vuelve a [0,1] y recorta al tamaño real

out = chw_to_hwc(y.detach().cpu().squeeze(0).numpy())
os.makedirs(os.path.dirname(os.path.abspath(a.output)), exist_ok=True)
write_img(a.output, out)
print("OK -> " + a.output)
'''


def disponible() -> bool:
    """Hay DehazeFormer si está el repo y al menos un .pth de alguna variante."""
    if not (DEHAZEFORMER_DIR / "test.py").exists():
        return False
    return any(_ruta_peso(m).exists() for m in MODELOS)


def _ruta_peso(modelo: str) -> Path:
    repo, exp = MODELOS[modelo]
    return repo / "saved_models" / exp / f"{modelo}.pth"


def mejorar(entrada, modelo="dehazeformer-b"):
    """Generador: cede log y devuelve la ruta de la imagen sin neblina.

    modelo: "dehazeformer-b" (calidad, por defecto), "dehazeformer-l" (más grande)
    o "gunet_b" (modo rápido). Cada uno usa su .pth en saved_models/<exp>/.
    """
    import hardware

    if modelo not in MODELOS:
        raise RuntimeError(f"Modelo DehazeFormer desconocido: {modelo}. Usa {list(MODELOS)}.")
    repo, _exp = MODELOS[modelo]
    if not (repo / "test.py").exists():
        raise RuntimeError(
            "DehazeFormer/gUNet no está instalado. Corre install/extras_dehazeformer.sh (o .bat)."
        )
    peso = _ruta_peso(modelo)
    if not peso.exists():
        raise RuntimeError(
            f"Faltan los pesos de '{modelo}' ({peso}). Bájalos de Google Drive con el "
            "instalador (DEHAZEFORMER_GDRIVE / GUNET_GDRIVE) o colócalos a mano."
        )

    entrada = Path(entrada)
    py = python_venv(".venv-dehazeformer", "install/extras_dehazeformer.sh")

    # Device: CUDA en la 4080, MPS en el Mac con chip M, CPU como último recurso.
    info = hardware.info_sistema()
    if info["cuda"]:
        device = "cuda"
    elif info.get("mps"):
        device = "mps"
    else:
        device = "cpu"

    tmp = Path(tempfile.mkdtemp(prefix="videoboost_dehazeformer_"))
    salida_tmp = tmp / f"{entrada.stem}_dehaze.png"
    # El script de inferencia se escribe DENTRO del repo (necesita importar sus
    # utils/models con rutas relativas); se borra al terminar.
    infer_py = repo / "_vb_infer.py"
    infer_py.write_text(_INFER)

    cmd = [
        py, "_vb_infer.py",
        "--model", modelo,
        "--weight", peso,
        "--input", entrada,
        "--output", salida_tmp,
        "--device", device,
    ]
    try:
        yield f"🌫️ DehazeFormer · {modelo} · {device} (quitando neblina)"
        if device == "cpu":
            yield "ℹ️ Sin GPU/MPS: corre por CPU (lento pero funciona)."
        yield from correr(cmd, cwd=repo)
        if not salida_tmp.exists():
            raise RuntimeError("DehazeFormer terminó pero no generó la imagen.")
        salida = SALIDAS / f"{entrada.stem}_dehazeformer.png"
        shutil.copy(salida_tmp, salida)
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        infer_py.unlink(missing_ok=True)
