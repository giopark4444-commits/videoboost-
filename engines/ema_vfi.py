"""EMA-VFI (MCG-NJU, Apache-2.0) — interpolación de frames de calidad SOTA con
tiempo arbitrario (cualquier factor). Inventa fotogramas intermedios muy limpios.

PyTorch; el repo usa `.cuda()` en su demo → en la práctica solo NVIDIA (4080).
No trae CLI de video (solo `demo_Nx.py` entre dos imágenes), así que escribimos un
pequeño script por LOTES en el repo: carga el modelo una vez, recorre los frames del
video y genera `n-1` intermedios por cada par; luego reensamblamos con FFmpeg.

NO PROBADO desde aquí (sin CUDA): verificar en la 4080 (API Model.multi_inference,
ckpt y reensamblado).
"""

import shutil
import tempfile
from pathlib import Path

from engines import SALIDAS, VENDOR, correr, python_venv
from engines import ffmpeg_utils as ff

EMA_DIR = VENDOR / "EMA-VFI"

# Script por lotes que vive dentro del repo (necesita sus imports relativos).
# Basado en demo_Nx.py: model.multi_inference(...) devuelve n-1 frames entre I0 e I2.
_BATCH = r'''
import os, sys, glob, argparse, cv2, torch, numpy as np
sys.path.append('.')
import config as cfg
from Trainer import Model
from benchmark.utils.padder import InputPadder

ap = argparse.ArgumentParser()
ap.add_argument('--in_dir', required=True)
ap.add_argument('--out_dir', required=True)
ap.add_argument('--n', type=int, default=2)
a = ap.parse_args()

dev = 'cuda' if torch.cuda.is_available() else (
    'mps' if getattr(torch.backends, 'mps', None) and torch.backends.mps.is_available() else 'cpu')

TTA = True
cfg.MODEL_CONFIG['LOGNAME'] = 'ours_t'
cfg.MODEL_CONFIG['MODEL_ARCH'] = cfg.init_model_config(F=32, depth=[2, 2, 2, 4, 4])
model = Model(-1)
model.load_model(); model.eval(); model.device()

frames = sorted(glob.glob(os.path.join(a.in_dir, '*.png')))
os.makedirs(a.out_dir, exist_ok=True)
idx = 0
def save(img):
    global idx
    cv2.imwrite(os.path.join(a.out_dir, 'f_%08d.png' % idx), img); idx += 1

n = a.n
for i in range(len(frames) - 1):
    I0 = cv2.imread(frames[i]); I2 = cv2.imread(frames[i + 1])
    save(I0)
    I0_ = (torch.tensor(I0.transpose(2, 0, 1)).to(dev) / 255.).unsqueeze(0)
    I2_ = (torch.tensor(I2.transpose(2, 0, 1)).to(dev) / 255.).unsqueeze(0)
    padder = InputPadder(I0_.shape, divisor=32)
    I0p, I2p = padder.pad(I0_, I2_)
    preds = model.multi_inference(
        I0p, I2p, TTA=TTA,
        time_list=[(j + 1) * (1. / n) for j in range(n - 1)], fast_TTA=TTA)
    for pred in preds:
        out = (padder.unpad(pred).detach().cpu().numpy().transpose(1, 2, 0) * 255.).astype(np.uint8)
        save(out)
    print('par %d/%d' % (i + 1, len(frames) - 1), flush=True)
save(cv2.imread(frames[-1]))
print('done', flush=True)
'''


def disponible() -> bool:
    return ((EMA_DIR / "demo_Nx.py").exists()
            and (EMA_DIR / "ckpt").exists())


def interpolar(video, mult=2):
    """Generador: cede log y devuelve la ruta del video interpolado (slow-mo).

    Extrae frames, genera mult-1 intermedios por par y reensambla a los fps
    ORIGINALES → cámara lenta real (duración ×mult).
    """
    if not disponible():
        raise RuntimeError("EMA-VFI no está instalado. Corre install/extras_ema_vfi.sh.")
    video = Path(video)
    py = python_venv(".venv-emavfi", "install/extras_ema_vfi.sh")
    mult = max(2, int(mult))
    fps_orig = ff.info_video(video).get("fps") or 30.0

    tmp = Path(tempfile.mkdtemp(prefix="videoboost_emavfi_"))
    in_dir, out_dir = tmp / "in", tmp / "out"
    in_dir.mkdir(), out_dir.mkdir()

    # Escribimos el script por lotes dentro del repo (necesita sus imports).
    batch = EMA_DIR / "_vb_batch.py"
    batch.write_text(_BATCH)

    try:
        yield f"🚀 EMA-VFI · x{mult} (interpolación SOTA / slow-mo)"
        yield "📊 Paso 1/3 · Extrayendo frames…"
        yield from correr(ff.cmd_extraer_frames(video, in_dir))
        yield "📊 Paso 2/3 · Interpolando (primera vez carga el modelo; requiere NVIDIA)…"
        yield from correr([py, "_vb_batch.py", "--in_dir", str(in_dir),
                           "--out_dir", str(out_dir), "--n", int(mult)],
                          cwd=EMA_DIR)
        if not any(out_dir.glob("*.png")):
            raise RuntimeError("EMA-VFI terminó pero no generó frames.")
        yield "📊 Paso 3/3 · Reensamblando a los fps originales (cámara lenta)…"
        salida = SALIDAS / f"{video.stem}_emavfi_x{mult}.mp4"
        yield from correr(ff.cmd_reensamblar(out_dir, "f_%08d.png",
                                             f"{fps_orig:.5f}", video, salida))
        return str(salida)
    finally:
        batch.unlink(missing_ok=True)
        shutil.rmtree(tmp, ignore_errors=True)
