"""BiRefNet (ZhengPeng7, MIT) — matting de ALTA RESOLUCIÓN: recorta el sujeto y
deja un PNG con canal alpha suave (pelo, bordes finos), mejor en detalle que un
matting binario corriente.

No depende de la CLI del repo (su `inference.py` produce máscaras binarias de
segmentación). En su lugar cargamos los pesos de matting de HuggingFace
`ZhengPeng7/BiRefNet-matting` con `transformers.AutoModelForImageSegmentation`
(trust_remote_code) y escribimos un script puente que: normaliza la entrada a
1024×1024 (mean/std de ImageNet), corre el modelo, toma `sigmoid()` de la última
salida como alpha y la pega como canal alpha de la imagen original a tamaño
completo. Resultado: PIL RGBA → PNG.

Es PyTorch puro, así que corre en NVIDIA (CUDA) y en Apple Silicon (MPS), igual
que InSPyReNet (a diferencia de los motores de difusión). Vive en .venv-birefnet
y se instala con install/extras_birefnet.(sh|bat). Licencia MIT.

Los pesos se auto-descargan a la caché de HuggingFace en el primer uso.
NO PROBADO EN GPU REAL desde aquí: verificar la forma de la salida del modelo en
la 4080 (índice [-1] de la tupla de predicciones).
"""

import os
import shutil
import tempfile
import textwrap
from pathlib import Path

from engines import SALIDAS, correr, python_venv

# Repo de pesos en HuggingFace. El de matting da alpha suave (pelo/bordes);
# existe también ZhengPeng7/BiRefNet (segmentación) y _HR-matting (más resolución).
HF_MODELO = "ZhengPeng7/BiRefNet-matting"


def disponible() -> bool:
    """Hay matting si transformers está importable en su venv propio."""
    try:
        py = python_venv(".venv-birefnet", "install/extras_birefnet.sh")
    except RuntimeError:
        return False
    import subprocess

    r = subprocess.run(
        [py, "-c", "import torch, transformers"],
        capture_output=True, text=True,
    )
    return r.returncode == 0


def mejorar(entrada):
    """Generador: cede log y devuelve la ruta del PNG con fondo transparente.

    Como la salida del modelo (forma de la tupla de predicciones) puede variar
    por versión, escribimos un script puente que llama al modelo de HuggingFace y
    guarda un PIL RGBA con el alpha de matting.
    """
    import hardware

    if not disponible():
        raise RuntimeError(
            "BiRefNet no está instalado. Corre install/extras_birefnet.sh (o .bat)."
        )
    entrada = Path(entrada)
    py = python_venv(".venv-birefnet", "install/extras_birefnet.sh")

    info = hardware.info_sistema()
    if info["cuda"]:
        device = "cuda"
    elif info["es_mac"]:
        device = "mps"
    else:
        device = "cpu"

    tmp = Path(tempfile.mkdtemp(prefix="videoboost_birefnet_"))
    salida = SALIDAS / f"{entrada.stem}_sinfondo_birefnet.png"
    puente = tmp / "_vb_birefnet.py"

    # Script puente: carga la imagen RGB, la normaliza a 1024×1024, corre el
    # modelo, usa sigmoid de la última predicción como alpha y la pega a tamaño
    # original. half() solo en CUDA (en MPS/CPU usamos fp32 por estabilidad).
    puente.write_text(textwrap.dedent(f"""
        import torch
        from PIL import Image
        from torchvision import transforms
        from transformers import AutoModelForImageSegmentation

        device = {device!r}
        modelo = AutoModelForImageSegmentation.from_pretrained(
            {HF_MODELO!r}, trust_remote_code=True
        )
        if device == "cuda":
            torch.set_float32_matmul_precision("high")
            modelo = modelo.half()
        modelo = modelo.to(device).eval()

        img = Image.open({str(entrada)!r}).convert("RGB")
        tam = (1024, 1024)
        tf = transforms.Compose([
            transforms.Resize(tam),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])
        x = tf(img).unsqueeze(0).to(device)
        if device == "cuda":
            x = x.half()

        with torch.no_grad():
            preds = modelo(x)[-1].sigmoid().cpu()
        alpha = preds[0].squeeze().float()
        mask = transforms.ToPILImage()(alpha).resize(img.size)

        out = img.convert("RGBA")
        out.putalpha(mask)
        out.save({str(salida)!r})
        print("OK", {str(salida)!r})
    """).strip())

    # Fallback de MPS por si alguna op del modelo no está implementada en Metal.
    env = dict(os.environ)
    env["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

    try:
        yield f"✂️ BiRefNet · matting alta-res · {device}"
        yield "ℹ️ La primera vez descarga los pesos de HuggingFace (ZhengPeng7/BiRefNet-matting)."
        yield from correr([py, str(puente)], cwd=tmp, env=env)
        if not salida.exists():
            raise RuntimeError("BiRefNet terminó pero no generó el PNG de salida.")
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
