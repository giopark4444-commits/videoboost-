"""RestoreFormer++ (wzhouxiff, Apache-2.0) — restauración de CARAS con un
transformer de prior multi-cabeza. Reemplazo comercial-limpio de CodeFormer
(que es NO comercial): aquí la licencia es Apache 2.0, apta para vender.

Restaura caras en imágenes completas (detecta+alinea+restaura+pega) o en caras
ya alineadas. Buen detalle natural en piel, ojos y pelo, top en su categoría.

CLI: inference.py -i <carpeta_in> -o <carpeta_out> -v RestoreFormer++ -s <escala>
[--aligned] [--bg_upsampler {realesrgan,None}] --save. Los pesos
(RestoreFormer++.ckpt) se auto-descargan de los releases de GitHub del repo en
el primer uso; el fondo opcional usa RealESRGAN_x2plus. Vive en .venv-restoreformerpp.

PyTorch: en NVIDIA usa CUDA; en Mac Apple Silicon corre por CPU/MPS (el script
cae a CPU si no hay CUDA — más lento pero funciona). En Mac desactivamos el
upsampler de fondo (realesrgan exige CUDA) pasando --bg_upsampler None, así solo
restaura las caras. NO PROBADO EN GPU REAL desde aquí: verificar flags al estrenar.
"""

import shutil
import tempfile
from pathlib import Path

from engines import SALIDAS, VENDOR, correr, python_venv

RF_DIR = VENDOR / "RestoreFormerPlusPlus"


def disponible() -> bool:
    return (RF_DIR / "inference.py").exists()


def mejorar(entrada, escala=2, alineada=False):
    """Generador: cede log y devuelve la ruta de la imagen con caras restauradas.

    - `escala`: factor de ampliación (-s). 2 por defecto.
    - `alineada`: True si la entrada ya es una cara cuadrada y alineada (--aligned).
    """
    import hardware

    if not disponible():
        raise RuntimeError(
            "RestoreFormer++ no está instalado. Corre install/extras_restoreformerpp.sh (o .bat)."
        )
    entrada = Path(entrada)
    py = python_venv(".venv-restoreformerpp", "install/extras_restoreformerpp.sh")
    cuda = hardware.info_sistema()["cuda"]

    tmp = Path(tempfile.mkdtemp(prefix="videoboost_restoreformerpp_"))
    in_dir, out_dir = tmp / "in", tmp / "out"
    in_dir.mkdir(), out_dir.mkdir()
    shutil.copy(entrada, in_dir / entrada.name)

    cmd = [
        py, "inference.py",
        "-i", in_dir,
        "-o", out_dir,
        "-v", "RestoreFormer++",
        "-s", int(escala),
        # En Mac (sin CUDA) el upsampler de fondo RealESRGAN no es práctico:
        # lo desactivamos y solo restauramos caras. En NVIDIA sí lo usamos.
        "--bg_upsampler", "realesrgan" if cuda else "None",
        "--save",
    ]
    if alineada:
        cmd.append("--aligned")
    try:
        modo = "cara alineada" if alineada else "imagen completa"
        yield f"🚀 RestoreFormer++ · {modo} · x{escala} · {'cuda' if cuda else 'cpu'}"
        yield "ℹ️ La primera vez descarga los pesos (RestoreFormer++.ckpt) de los releases de GitHub."
        if not cuda:
            yield "ℹ️ Sin CUDA: corre por CPU (más lento) y sin mejorar el fondo (solo caras)."
        yield from correr(cmd, cwd=RF_DIR)
        # Salidas posibles del script: restored_imgs/ (imagen completa repuesta),
        # restored_faces/ (caras recortadas restauradas), cropped_faces/.
        # Preferimos la imagen completa repuesta; si no hay (modo --aligned),
        # tomamos la cara restaurada.
        candidatas = []
        for sub in ("restored_imgs", "restored_faces", "cropped_faces"):
            d = out_dir / sub
            if d.exists():
                candidatas += [p for p in d.rglob("*")
                               if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
        if not candidatas:
            candidatas = [p for p in out_dir.rglob("*")
                          if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
        if not candidatas:
            raise RuntimeError("RestoreFormer++ terminó pero no generó ninguna imagen.")
        salida = SALIDAS / f"{entrada.stem}_restoreformerpp.png"
        shutil.copy(candidatas[0], salida)
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
