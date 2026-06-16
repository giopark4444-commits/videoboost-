"""InSPyReNet / transparent-background (plemeri, MIT) — quita el FONDO de una
imagen (matting de alta calidad) y devuelve un PNG con canal alpha.

A diferencia de los motores de difusión, esto es un paquete pip puro
(`transparent-background`) con API Python: `Remover().process(img, type="rgba")`
recibe una imagen PIL RGB y devuelve otra PIL RGBA con el sujeto recortado y el
fondo transparente. Soporta CUDA (NVIDIA) y MPS (Apple Silicon), así que corre
bien en este Mac (a diferencia de los motores SD). Vive en .venv-inspyrenet y se
instala con install/extras_inspyrenet.(sh|bat). Licencia MIT.

Los pesos del modelo se auto-descargan a ~/.transparent-background el primer uso.
"""

import shutil
import tempfile
import textwrap
from pathlib import Path

from engines import SALIDAS, correr, python_venv


def disponible() -> bool:
    """Hay matting si el venv tiene el marcador .ok del instalador."""
    from engines import RAIZ
    try:
        python_venv(".venv-inspyrenet", "install/extras_inspyrenet.sh")
    except RuntimeError:
        return False
    return (RAIZ / ".venv-inspyrenet" / ".ok").exists()


def mejorar(entrada, modo="base"):
    """Generador: cede log y devuelve la ruta del PNG con fondo transparente.

    `modo` es 'base' (calidad) o 'fast' (rápido). Como la API es Python pura
    (no hay CLI cómodo que conserve el alpha de forma garantizada por versión),
    escribimos un script puente que llama a Remover().process(img, type="rgba").
    """
    import hardware

    if not disponible():
        raise RuntimeError(
            "InSPyReNet (transparent-background) no está instalado. "
            "Corre install/extras_inspyrenet.sh (o .bat)."
        )
    entrada = Path(entrada)
    py = python_venv(".venv-inspyrenet", "install/extras_inspyrenet.sh")

    info = hardware.info_sistema()
    if info["cuda"]:
        device = "cuda:0"
    elif info["es_mac"]:
        device = "mps"
    else:
        device = "cpu"

    tmp = Path(tempfile.mkdtemp(prefix="videoboost_inspyrenet_"))
    salida = SALIDAS / f"{entrada.stem}_sinfondo.png"
    puente = tmp / "_vb_matting.py"

    # Script puente: carga la imagen como RGB, recorta el fondo y guarda RGBA.
    # PYTORCH_ENABLE_MPS_FALLBACK lo pone el engine en el entorno (ver abajo)
    # por si alguna op no está implementada en MPS.
    puente.write_text(textwrap.dedent(f"""
        import sys
        from PIL import Image
        from transparent_background import Remover

        remover = Remover(mode={modo!r}, device={device!r})
        img = Image.open({str(entrada)!r}).convert("RGB")
        out = remover.process(img, type="rgba")   # PIL RGBA con alpha
        out.save({str(salida)!r})
        print("OK", {str(salida)!r})
    """).strip())

    import os

    env = dict(os.environ)
    env["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

    try:
        yield f"✂️ InSPyReNet · matting · modo {modo} · {device}"
        yield "ℹ️ La primera vez descarga los pesos del modelo (~/.transparent-background)."
        yield from correr([py, str(puente)], cwd=tmp, env=env)
        if not salida.exists():
            raise RuntimeError("InSPyReNet terminó pero no generó el PNG de salida.")
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
