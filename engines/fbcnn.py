"""FBCNN (Jiang et al., ICCV 2021 · Apache-2.0) — eliminación de artefactos de
compresión JPEG (bloques, "mosquito", banding) con Factor de Calidad ajustable.

Es una CNN ligera (no difusión), así que corre bien tanto en **Mac (MPS)** como
en **NVIDIA (CUDA)**; por eso es plataforma "ambas". Limpia JPEGs reales: en modo
CIEGO (calidad=None) la red estima sola el QF; o puedes fijar un QF 1-100 para
controlar el balance entre quitar artefactos y conservar detalle (QF bajo = limpia
más/suaviza; QF alto = conserva más textura).

El repo oficial (jiaxi-jiang/FBCNN) NO trae CLI con argparse: sus scripts
`main_test_fbcnn_color*.py` tienen rutas y QF hardcodeados y miden PSNR contra un
ground-truth. Así que escribimos un pequeño script de inferencia dentro del repo
(necesita sus imports relativos: models.network_fbcnn + utils.utils_image), basado
en `main_test_fbcnn_color_real.py`. Los pesos (fbcnn_color.pth) se auto-descargan
de los releases del repo al `model_zoo/` en el primer uso. Vive en .venv-fbcnn.

NO PROBADO con inferencia desde aquí (Mac sin el venv montado al escribirlo): solo
verificada la sintaxis/imports. Verificar API model(img, qf_input) en GPU/MPS real.
"""

import shutil
import tempfile
from pathlib import Path

from engines import VENDOR, SALIDAS, correr, python_venv

FBCNN_DIR = VENDOR / "FBCNN"
PESOS = FBCNN_DIR / "model_zoo" / "fbcnn_color.pth"

# Script de inferencia que vive DENTRO del repo (usa sus imports relativos).
# Basado en main_test_fbcnn_color_real.py: lee el JPEG real (sin recomprimir),
# corre modo ciego o con QF fijo, y guarda el PNG restaurado en --out_dir.
_INFER = r'''
import os, sys, argparse, torch
sys.path.append('.')
from models.network_fbcnn import FBCNN as net
from utils import utils_image as util

ap = argparse.ArgumentParser()
ap.add_argument('--input', required=True)         # ruta a la imagen de entrada
ap.add_argument('--out_dir', required=True)
ap.add_argument('--model_path', required=True)    # model_zoo/fbcnn_color.pth
ap.add_argument('--qf', type=int, default=-1)     # -1 = ciego; 1..100 = QF fijo
a = ap.parse_args()

dev = 'cuda' if torch.cuda.is_available() else (
    'mps' if getattr(torch.backends, 'mps', None) and torch.backends.mps.is_available()
    else 'cpu')

n_channels = 3
model = net(in_nc=n_channels, out_nc=n_channels, nc=[64, 128, 256, 512], nb=4, act_mode='R')
model.load_state_dict(torch.load(a.model_path, map_location='cpu', weights_only=True), strict=True)
model.eval()
for _, v in model.named_parameters():
    v.requires_grad = False
model = model.to(dev)

img_L = util.imread_uint(a.input, n_channels=n_channels)
img_L = util.uint2tensor4(img_L).to(dev)

with torch.no_grad():
    if a.qf and a.qf > 0:
        # QF fijo: la red recibe (1 - qf/100) como en el script real oficial.
        qf_input = torch.tensor([[1.0 - a.qf / 100.0]]).to(dev)
        img_E, QF = model(img_L, qf_input)
    else:
        # Modo ciego: la red estima el QF sola.
        img_E, QF = model(img_L)

img_E = util.single2uint(util.tensor2single(img_E))
os.makedirs(a.out_dir, exist_ok=True)
stem = os.path.splitext(os.path.basename(a.input))[0]
out = os.path.join(a.out_dir, stem + '_fbcnn.png')
util.imsave(img_E, out)
print('QF estimado: %d' % round(float((1.0 - QF) * 100)), flush=True)
print('OK ' + out, flush=True)
'''


def disponible() -> bool:
    return (FBCNN_DIR / "models" / "network_fbcnn.py").exists() and PESOS.exists()


def mejorar(entrada, calidad=None):
    """Generador: cede log y devuelve la ruta de la imagen sin artefactos JPEG.

    calidad=None → modo CIEGO (la red estima el factor de calidad sola).
    calidad=1..100 → fija el factor de calidad (bajo = limpia más; alto = conserva
    más detalle).
    """
    if not disponible():
        raise RuntimeError(
            "FBCNN no está instalado. Corre install/extras_fbcnn.sh (o .bat)."
        )
    entrada = Path(entrada)
    py = python_venv(".venv-fbcnn", "install/extras_fbcnn.sh")
    qf = int(calidad) if calidad else -1

    tmp = Path(tempfile.mkdtemp(prefix="videoboost_fbcnn_"))
    out_dir = tmp / "out"
    out_dir.mkdir()

    # Script de inferencia dentro del repo (necesita sus imports relativos).
    infer = FBCNN_DIR / "_vb_infer.py"
    infer.write_text(_INFER)

    cmd = [
        py, "_vb_infer.py",
        "--input", str(entrada),
        "--out_dir", str(out_dir),
        "--model_path", str(PESOS),
        "--qf", qf,
    ]
    try:
        modo = "ciego" if qf < 0 else f"QF {qf}"
        yield f"🧽 FBCNN · quitando artefactos JPEG · {modo}"
        yield from correr(cmd, cwd=FBCNN_DIR)
        resultados = [p for p in out_dir.rglob("*")
                      if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
        if not resultados:
            raise RuntimeError("FBCNN terminó pero no generó ninguna imagen.")
        salida = SALIDAS / f"{entrada.stem}_fbcnn.png"
        shutil.copy(resultados[0], salida)
        return str(salida)
    finally:
        infer.unlink(missing_ok=True)
        shutil.rmtree(tmp, ignore_errors=True)
