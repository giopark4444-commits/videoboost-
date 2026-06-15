"""FlashVSR (OpenImagingLab, Apache-2.0) — super-resolución de video casi en
tiempo real. EXPERIMENTAL y solo NVIDIA: usa kernels CUDA de atención dispersa,
no funciona en Mac.

Es el "modo rápido" para material largo / metraje real donde SeedVR2 7B sería
demasiado lento. Se instala con install/extras_flashvsr.(sh|bat) en su venv.

Los scripts oficiales (examples/WanVSR/infer_flashvsr_v1.1_*.py) NO usan argparse:
traen una lista `inputs = [...]` y `RESULT_ROOT = "./results"` hardcodeadas. Por
eso generamos una copia del script con TU video y nuestra carpeta de salida, la
ejecutamos y recogemos el mp4 resultante. NO PROBADO EN GPU REAL desde aquí:
verificar en la 4080 (ver CLAUDE.md).
"""

import re
import tempfile
from pathlib import Path

from engines import SALIDAS, VENDOR, correr, python_venv

FLASHVSR_DIR = VENDOR / "FlashVSR"
_WANVSR = FLASHVSR_DIR / "examples" / "WanVSR"

# v1.1 primero (recomendada por los autores); fallback a nombres antiguos.
_ENTRYPOINTS = [
    _WANVSR / "infer_flashvsr_v1.1_full.py",
    _WANVSR / "infer_flashvsr_v1.1_tiny.py",
    _WANVSR / "infer_flashvsr_full.py",
    _WANVSR / "infer_flashvsr_tiny.py",
]


def disponible() -> bool:
    return FLASHVSR_DIR.exists() and any(e.exists() for e in _ENTRYPOINTS)


def mejorar(entrada):
    """Generador: cede log y devuelve la ruta del video mejorado."""
    entrada = Path(entrada).resolve()
    py = python_venv(".venv-flashvsr", "install/extras_flashvsr.sh")
    base = next((e for e in _ENTRYPOINTS if e.exists()), None)
    if base is None:
        raise RuntimeError(
            "No se encontró el script de inferencia de FlashVSR. Revisa el README "
            "de vendor/FlashVSR y actualiza _ENTRYPOINTS en engines/flashvsr.py."
        )

    out_dir = Path(tempfile.mkdtemp(prefix="videoboost_flashvsr_"))
    # Parchear el script: lista de entrada = tu video; RESULT_ROOT = out_dir.
    texto = base.read_text()
    texto = re.sub(r"inputs\s*=\s*\[.*?\]", f"inputs = [{repr(str(entrada))}]",
                   texto, count=1, flags=re.S)
    texto = re.sub(r"RESULT_ROOT\s*=\s*[\"'].*?[\"']",
                   f"RESULT_ROOT = {repr(str(out_dir))}", texto, count=1)
    # El script temporal vive junto al original para que sus imports relativos
    # y la carpeta de pesos (./FlashVSR-v1.1) resuelvan con cwd=examples/WanVSR.
    temp = base.with_name("_vb_" + base.name)
    temp.write_text(texto)
    try:
        yield f"🚀 FlashVSR (experimental) · {base.name}"
        yield "ℹ️ Primera vez: descarga los pesos. Si falla, SeedVR2 cubre lo mismo."
        yield from correr([py, temp], cwd=_WANVSR)
        salidas = sorted(out_dir.rglob("*.mp4"), key=lambda p: p.stat().st_mtime,
                         reverse=True)
        if not salidas:
            raise RuntimeError("FlashVSR terminó pero no generó ningún video.")
        final = SALIDAS / f"{entrada.stem}_flashvsr.mp4"
        import shutil
        shutil.move(str(salidas[0]), str(final))
        return str(final)
    finally:
        temp.unlink(missing_ok=True)
        import shutil
        shutil.rmtree(out_dir, ignore_errors=True)
