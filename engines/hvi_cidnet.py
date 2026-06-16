"""HVI-CIDNet (Fediory, MIT) — realce de poca luz (low-light) ganador de NTIRE 2025
y publicado en CVPR 2025. Propone el espacio de color HVI y la red CIDNet (CNN
ligera, NO difusión), así que corre razonablemente tanto en NVIDIA como en Mac.

El CLI oficial `eval_hf.py` descarga los pesos de HuggingFace con from_pretrained
(config.json + model.safetensors) y guarda en ./output_hf conservando el nombre.
PERO fija `.cuda()` a fuego, por lo que NO arranca en Mac tal cual. Como CIDNet es
una CNN ligera, aquí escribimos un runner device-agnóstico `_vb_eval.py` dentro del
repo (mismo patrón que EMA-VFI/FlashVSR) que reusa `net.CIDNet` y la carga de pesos
de HuggingFace, eligiendo cuda → mps → cpu. Vive en .venv-hvi_cidnet.

Pesos por defecto: Fediory/HVI-CIDNet-Generalization (los de mayor generalización,
recomendados por el repo para imágenes "de la calle"). Solo se auto-descargan en el
primer uso. plataforma: ambas. NO PROBADO EN GPU REAL desde aquí: verificar en la
4080 que `.to(device)` y el forward no rompen y que el nombre del peso no cambió.
"""

import shutil
import tempfile
from pathlib import Path

from engines import SALIDAS, VENDOR, correr, python_venv

HVI_DIR = VENDOR / "HVI-CIDNet"
# Pesos de mayor generalización (recomendados por el repo para fotos cualquiera).
# Otras variantes válidas: Fediory/HVI-CIDNet-LOLv1-wperc, -LOLv2-real, etc.
HF_PESOS = "Fediory/HVI-CIDNet-Generalization"

# Runner device-agnóstico que escribimos en el repo. Reusa net.CIDNet y la lógica
# de carga de pesos de eval_hf.py, pero elige cuda → mps → cpu (el CLI oficial fija
# .cuda(), que no existe en Mac).
_RUNNER = '''import argparse, json, os
import torch, torch.nn.functional as F
import safetensors.torch as sf
import torchvision.transforms as transforms
from huggingface_hub import hf_hub_download
from PIL import Image
from net.CIDNet import CIDNet

p = argparse.ArgumentParser()
p.add_argument("--path", type=str, required=True)
p.add_argument("--input_img", type=str, required=True)
p.add_argument("--output_dir", type=str, required=True)
p.add_argument("--alpha_s", type=float, default=1.0)
p.add_argument("--alpha_i", type=float, default=1.0)
p.add_argument("--gamma", type=float, default=1.0)
el = p.parse_args()

if torch.cuda.is_available():
    dev = "cuda"
elif getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
    dev = "mps"
else:
    dev = "cpu"
print("HVI-CIDNet device:", dev, flush=True)

model = CIDNet().to(dev)
# Carga de pesos desde HuggingFace (config.json + model.safetensors), igual que eval_hf.py.
hf_hub_download(repo_id=el.path, filename="config.json", repo_type="model")
model_file = hf_hub_download(repo_id=el.path, filename="model.safetensors", repo_type="model")
model.load_state_dict(sf.load_file(model_file), strict=False)
model.eval()

img = Image.open(el.input_img).convert("RGB")
inp = transforms.ToTensor()(img)
factor = 8
h, w = inp.shape[1], inp.shape[2]
H, W = ((h + factor) // factor) * factor, ((w + factor) // factor) * factor
padh = H - h if h % factor != 0 else 0
padw = W - w if w % factor != 0 else 0
inp = F.pad(inp.unsqueeze(0), (0, padw, 0, padh), "reflect").to(dev)
with torch.no_grad():
    model.trans.alpha_s = el.alpha_s
    model.trans.alpha = el.alpha_i
    model.trans.gated = True
    model.trans.gated2 = True
    out = model(inp ** el.gamma)
out = torch.clamp(out, 0, 1)[:, :, :h, :w]
os.makedirs(el.output_dir, exist_ok=True)
name = os.path.basename(el.input_img)
transforms.ToPILImage()(out.squeeze(0).float().cpu()).save(os.path.join(el.output_dir, name))
print("OK:", name, flush=True)
'''


def disponible() -> bool:
    return (HVI_DIR / "eval_hf.py").exists()


def mejorar(entrada, alpha_s=1.0, alpha_i=1.0, gamma=1.0):
    """Generador: cede log y DEVUELVE la ruta de la imagen con luz realzada.

    alpha_s/alpha_i ajustan saturación/intensidad del color; gamma la curva de
    brillo (todo 1.0 = realce neutro recomendado).
    """
    if not disponible():
        raise RuntimeError(
            "HVI-CIDNet no está instalado. Corre install/extras_hvi_cidnet.sh (o .bat)."
        )
    entrada = Path(entrada)
    py = python_venv(".venv-hvi_cidnet", "install/extras_hvi_cidnet.sh")

    # Escribimos el runner device-agnóstico dentro del repo (lo necesita para
    # importar net.CIDNet con el cwd correcto).
    (HVI_DIR / "_vb_eval.py").write_text(_RUNNER)

    tmp = Path(tempfile.mkdtemp(prefix="videoboost_hvi_cidnet_"))
    out_dir = tmp / "out"
    out_dir.mkdir()

    cmd = [
        py, "_vb_eval.py",
        "--path", HF_PESOS,
        "--input_img", entrada,
        "--output_dir", out_dir,
        "--alpha_s", float(alpha_s),
        "--alpha_i", float(alpha_i),
        "--gamma", float(gamma),
    ]
    try:
        yield f"🚀 HVI-CIDNet · poca luz · αs={alpha_s} αi={alpha_i} γ={gamma}"
        yield "ℹ️ La primera vez descarga los pesos (CIDNet) de HuggingFace."
        yield from correr(cmd, cwd=HVI_DIR)
        resultados = [p for p in out_dir.rglob("*")
                      if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".bmp")]
        if not resultados:
            raise RuntimeError("HVI-CIDNet terminó pero no generó ninguna imagen.")
        salida = SALIDAS / f"{entrada.stem}_hvi_cidnet.png"
        shutil.copy(resultados[0], salida)
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
