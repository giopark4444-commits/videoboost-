"""Retinexformer (caiyuanhao1998, MIT) — realce de imágenes con POCA LUZ.

Transformer de una etapa basado en la teoría Retinex: aclara fotos oscuras /
nocturnas y recupera sombras sin amplificar el ruido. Es un modelo de imagen
(no video). Está construido sobre una versión REESTRUCTURADA de BasicSR que el
repo trae embebida (con la arquitectura RetinexFormer registrada por escaneo de
*_arch.py). Usamos por defecto el modelo **LOL_v2_real** (captura real de poca
luz, el de mejor generalización al mundo real según el README).

Dos cosas del repo oficial obligan a este engine a NO usar su `test.py`:

  1) El paquete `basicsr` embebido NO trae `__init__.py` de nivel superior: el
     repo depende de `python setup.py develop` para registrarlo, y ese build
     editable FALLA en Python 3.12. El instalador lo suple creando un
     `basicsr/__init__.py` mínimo + un `.pth` que pone el repo en sys.path, así
     `import basicsr` resuelve a ESTE basicsr y no al genérico de pip (que carece
     de la arquitectura y rompe al importar torchvision.functional_tensor).

  2) `Enhancement/test_from_dataset.py` está CLAVADO a CUDA (`.cuda()` directos,
     `torch.cuda.empty_cache()`), lee las imágenes desde el YAML y exige
     ground-truth para calcular PSNR/SSIM. Inútil para "aclara ESTA imagen" y no
     corre en Mac.

Por eso, igual que DehazeFormer/FaithDiff/FlashVSR en este proyecto, el engine
ESCRIBE un script de inferencia mínimo (`_vb_infer.py`) dentro de Enhancement/
(para que `import utils` y `import basicsr` resuelvan) que:
  · construye la red con el `create_model(opt).net_g` del repo, forzando
    `num_gpu=0` para que el `model_to_device` interno NO llame a `.cuda()`,
  · carga el .pth (clave 'params'; tolera el prefijo 'module.' de DataParallel),
  · elige device cuda/mps/cpu y mueve la red a mano (corre en Mac),
  · rellena la entrada a múltiplo de 4 (reflect) y recorta al final,
  · procesa una carpeta de imágenes con UNA sola carga del modelo.

⚠️ En Mac (sin CUDA) corre por MPS o CPU: funciona, pero es un Transformer pesado
y es lento; en la 4080 (CUDA) es donde rinde. La poca luz también está cubierta
por HVI-CIDNet y DarkIR. Vive en .venv-retinexformer.
"""

import shutil
import tempfile
from pathlib import Path

from engines import VENDOR, SALIDAS, correr, python_venv

RETINEXFORMER_DIR = VENDOR / "Retinexformer"

# Modelo por defecto: poca luz real. (config del repo, peso).
CONFIG = "Options/RetinexFormer_LOL_v2_real.yml"
PESO = "pretrained_weights/LOL_v2_real.pth"

# Script de inferencia que se inyecta en Enhancement/ (reusa SU utils y SU
# create_model). Device-agnóstico (cuda/mps/cpu), padding a múltiplo de 4, sin
# ground-truth ni métricas. Procesa toda la carpeta --input_dir con una carga.
_INFER = r'''
import os, sys, glob, argparse
import numpy as np
import torch
import torch.nn.functional as F

import utils                              # Enhancement/utils.py (load_img RGB)
from basicsr.models import create_model
from basicsr.utils.options import parse

p = argparse.ArgumentParser()
p.add_argument("--opt", required=True)        # YAML del repo (define network_g)
p.add_argument("--weight", required=True)     # .pth
p.add_argument("--input_dir", required=True)  # carpeta de imágenes de entrada
p.add_argument("--output_dir", required=True) # carpeta de salida (png)
p.add_argument("--device", default="cpu")     # cuda / mps / cpu
a = p.parse_args()

# Construir la red SIN tocar CUDA: num_gpu=0 evita el .cuda() de model_to_device.
opt = parse(a.opt, is_train=False)
opt["dist"] = False
opt["num_gpu"] = 0
net = create_model(opt).net_g

# Cargar pesos (clave 'params'; tolera prefijo 'module.' de DataParallel).
# weights_only=True: solo tensores (los .pth oficiales no traen objetos pickle);
# evita ejecución arbitraria al deserializar. Si una versión vieja de torch no
# soporta el flag, se reintenta sin él (mismo comportamiento que upstream).
try:
    ckpt = torch.load(a.weight, map_location="cpu", weights_only=True)
except TypeError:
    ckpt = torch.load(a.weight, map_location="cpu")
state = ckpt.get("params", ckpt) if isinstance(ckpt, dict) else ckpt
try:
    net.load_state_dict(state)
except Exception:
    net.load_state_dict({("module." + k): v for k, v in state.items()})

dev = torch.device(a.device)
net = net.to(dev).eval()

factor = 4
os.makedirs(a.output_dir, exist_ok=True)
exts = ("*.png", "*.jpg", "*.jpeg", "*.webp", "*.bmp")
paths = sorted(q for e in exts for q in glob.glob(os.path.join(a.input_dir, e)))
if not paths:
    print("NO_INPUT"); sys.exit(2)

with torch.inference_mode():
    for inp in paths:
        img = np.float32(utils.load_img(inp)) / 255.0       # HWC RGB en [0,1]
        x = torch.from_numpy(img).permute(2, 0, 1).unsqueeze(0).to(dev)
        _, _, h, w = x.shape
        H = ((h + factor) // factor) * factor
        W = ((w + factor) // factor) * factor
        padh = H - h if h % factor != 0 else 0
        padw = W - w if w % factor != 0 else 0
        x = F.pad(x, (0, padw, 0, padh), "reflect")
        y = net(x)[:, :, :h, :w]                            # recorta el padding
        y = torch.clamp(y, 0, 1).detach().cpu().permute(0, 2, 3, 1).squeeze(0).numpy()
        out = os.path.join(a.output_dir,
                           os.path.splitext(os.path.basename(inp))[0] + ".png")
        utils.save_img(out, (y * 255.0).round().astype(np.uint8))
        print("OK -> " + out)
'''


def disponible() -> bool:
    """Hay repo clonado + script de inferencia del repo + peso descargado."""
    return (
        (RETINEXFORMER_DIR / "Enhancement" / "test_from_dataset.py").exists()
        and (RETINEXFORMER_DIR / PESO).exists()
    )


def _device():
    import hardware

    info = hardware.info_sistema()
    if info["cuda"]:
        return "cuda"
    if info.get("mps"):
        return "mps"
    return "cpu"


def _correr_infer(in_dir: Path, out_dir: Path):
    """Inyecta _vb_infer.py en Enhancement/ y lo ejecuta sobre in_dir -> out_dir.
    Generador: cede log. Borra el script al terminar.
    """
    py = python_venv(".venv-retinexformer", "install/extras_retinexformer.sh")
    device = _device()
    infer_py = RETINEXFORMER_DIR / "Enhancement" / "_vb_infer.py"
    infer_py.write_text(_INFER)
    cmd = [
        py, "Enhancement/_vb_infer.py",
        "--opt", RETINEXFORMER_DIR / CONFIG,
        "--weight", RETINEXFORMER_DIR / PESO,
        "--input_dir", in_dir,
        "--output_dir", out_dir,
        "--device", device,
    ]
    try:
        yield f"🌙 Retinexformer · poca luz (LOL_v2_real) · {device}"
        if device == "cpu":
            yield "⚠️ Sin GPU/MPS: corre por CPU y es lento (Transformer pesado)."
        elif device == "mps":
            yield "ℹ️ Mac (MPS): funciona, pero es lento; en NVIDIA rinde mejor."
        yield from correr(cmd, cwd=RETINEXFORMER_DIR)
    finally:
        infer_py.unlink(missing_ok=True)


def mejorar(entrada):
    """Generador: cede log y devuelve la ruta de la imagen aclarada."""
    if not disponible():
        raise RuntimeError(
            "Retinexformer no está instalado. Corre install/extras_retinexformer.sh "
            "(o .bat)."
        )
    entrada = Path(entrada)
    tmp = Path(tempfile.mkdtemp(prefix="videoboost_retinexformer_"))
    in_dir, out_dir = tmp / "in", tmp / "out"
    in_dir.mkdir()
    out_dir.mkdir()
    shutil.copy(entrada, in_dir / entrada.name)
    try:
        yield from _correr_infer(in_dir, out_dir)
        resultados = [
            p for p in out_dir.rglob("*")
            if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")
        ]
        if not resultados:
            raise RuntimeError("Retinexformer terminó pero no generó ninguna imagen.")
        salida = SALIDAS / f"{entrada.stem}_retinexformer.png"
        shutil.copy(resultados[0], salida)
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def procesar_carpeta(in_dir, out_dir):
    """Procesa TODA una carpeta de imágenes (frames de un video) con UNA carga del
    modelo. Los resultados (mismos nombres, .png) quedan en `out_dir`.
    Generador: log.
    """
    if not disponible():
        raise RuntimeError(
            "Retinexformer no está instalado. Corre install/extras_retinexformer.sh."
        )
    in_dir, out_dir = Path(in_dir), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    yield from _correr_infer(in_dir, out_dir)
