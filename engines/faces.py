"""Restauración de caras: CodeFormer (por defecto) y GFPGAN.

Es la pieza que distingue a HitPaw/Topaz: los upscalers generales reconstruyen
texturas pero "resbalan" en los rostros; estos modelos están entrenados solo en
caras y recuperan ojos, dientes y piel de forma realista.

Funciona en CUDA (NVIDIA) y MPS (Mac con chip M). Vive en su propio venv
(.venv-caras) porque basicsr/facexlib chocan con diffusers de FaithDiff/SeedVR2.
Se instala con install/extras_caras.(sh|bat). Licencia: CodeFormer NTU S-Lab
(no comercial); GFPGAN Apache 2.0.

Pensado para imágenes y, opcionalmente, como pasada de caras sobre los frames
de un video ya escalado.
"""

import shutil
import tempfile
from pathlib import Path

from engines import RAIZ, SALIDAS, VENDOR, correr

CODEFORMER_DIR = VENDOR / "CodeFormer"


def _python_venv() -> str:
    venv = RAIZ / ".venv-caras"
    for rel in ("bin/python", "Scripts/python.exe"):
        p = venv / rel
        if p.exists():
            return str(p)
    raise RuntimeError(
        "No existe el entorno .venv-caras. Corre install/extras_caras.sh (o .bat)."
    )


def disponible() -> bool:
    return (CODEFORMER_DIR / "inference_codeformer.py").exists()


def restaurar_caras(entrada, fidelidad=0.7, escala=2, upsample_caras=True):
    """CodeFormer sobre una imagen.

    fidelidad (w): 0 = máxima calidad/menos fiel, 1 = más fiel al original.
    0.7 es un buen equilibrio por defecto.
    """
    if not disponible():
        raise RuntimeError(
            "CodeFormer no está instalado. Corre install/extras_caras.sh (o .bat)."
        )
    entrada = Path(entrada)
    py = _python_venv()

    tmp = Path(tempfile.mkdtemp(prefix="videoboost_caras_"))
    in_dir, out_dir = tmp / "in", tmp / "out"
    in_dir.mkdir(), out_dir.mkdir()
    shutil.copy(entrada, in_dir / entrada.name)

    cmd = [
        py, "inference_codeformer.py",
        "-w", fidelidad,
        "--input_path", in_dir,
        "--output_path", out_dir,
        "--upscale", escala,
        "--bg_upsampler", "realesrgan",  # escala también el fondo, no solo la cara
    ]
    if upsample_caras:
        cmd.append("--face_upsample")

    try:
        yield f"🚀 CodeFormer · fidelidad {fidelidad} · x{escala}"
        yield "ℹ️ La primera vez descarga los pesos (CodeFormer + detector de caras)."
        yield from correr(cmd, cwd=CODEFORMER_DIR)
        # CodeFormer deja el resultado final en output_path/final_results/.
        resultados = [p for p in out_dir.rglob("*")
                      if p.suffix.lower() in (".png", ".jpg", ".jpeg")
                      and "final_results" in str(p)]
        if not resultados:  # algunas versiones lo dejan en la raíz de salida
            resultados = [p for p in out_dir.rglob("*")
                          if p.suffix.lower() in (".png", ".jpg", ".jpeg")]
        if not resultados:
            raise RuntimeError("CodeFormer terminó pero no generó ninguna imagen.")
        salida = SALIDAS / f"{entrada.stem}_caras_codeformer.png"
        shutil.copy(resultados[0], salida)
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
