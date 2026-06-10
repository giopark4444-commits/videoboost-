"""FlashVSR (Shanghai AI Lab, CVPR 2026) — super-resolución de video casi en
tiempo real. EXPERIMENTAL y solo NVIDIA: usa kernels CUDA de atención dispersa,
no funciona en Mac.

Es el "modo rápido" para material largo donde SeedVR2 7B sería demasiado lento.
Se instala con install/extras_flashvsr.(sh|bat) en su propio venv.

NOTA: el script de inferencia de FlashVSR ha cambiado de nombre entre
versiones; aquí se prueban los nombres conocidos. Si el repo cambia, ajustar
_ENTRYPOINTS (ver CLAUDE.md).
"""

from pathlib import Path

from engines import RAIZ, SALIDAS, VENDOR, correr

FLASHVSR_DIR = VENDOR / "FlashVSR"

_ENTRYPOINTS = [
    "examples/WanVSR/infer_flashvsr_full.py",
    "examples/WanVSR/infer_flashvsr_tiny.py",
    "inference.py",
    "infer.py",
]


def _python_venv() -> str:
    venv = RAIZ / ".venv-flashvsr"
    for rel in ("bin/python", "Scripts/python.exe"):
        p = venv / rel
        if p.exists():
            return str(p)
    raise RuntimeError("No existe .venv-flashvsr. Corre install/extras_flashvsr.sh (o .bat).")


def disponible() -> bool:
    return FLASHVSR_DIR.exists() and any((FLASHVSR_DIR / e).exists() for e in _ENTRYPOINTS)


def mejorar(entrada):
    entrada = Path(entrada)
    py = _python_venv()
    entrypoint = next((FLASHVSR_DIR / e for e in _ENTRYPOINTS if (FLASHVSR_DIR / e).exists()), None)
    if entrypoint is None:
        raise RuntimeError(
            "No se encontró el script de inferencia de FlashVSR. Revisa el README "
            "de vendor/FlashVSR y actualiza _ENTRYPOINTS en engines/flashvsr.py."
        )
    salida = SALIDAS / f"{entrada.stem}_flashvsr.mp4"
    yield f"🚀 FlashVSR (experimental) · {entrypoint.relative_to(FLASHVSR_DIR)}"
    yield "⚠️ Si los argumentos no coinciden con tu versión del repo, revisa su README."
    yield from correr(
        [py, entrypoint, "--input", entrada, "--output", salida],
        cwd=FLASHVSR_DIR,
    )
    return str(salida)
