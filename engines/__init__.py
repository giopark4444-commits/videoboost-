"""Rutas compartidas y ejecución de subprocesos con log en vivo."""

import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BIN = RAIZ / "bin"
VENDOR = RAIZ / "vendor"
MODELS = RAIZ / "models"
SALIDAS = RAIZ / "salidas"

SALIDAS.mkdir(exist_ok=True)


def python_venv(nombre: str, instalador: str) -> str:
    """Ruta al python del venv `nombre` (ej. ".venv-caras"), o RuntimeError
    indicando qué instalador correr."""
    venv = RAIZ / nombre
    for rel in ("bin/python", "Scripts/python.exe"):
        p = venv / rel
        if p.exists():
            return str(p)
    raise RuntimeError(f"No existe el entorno {nombre}. Corre {instalador} (o .bat).")


def correr(cmd, cwd=None, env=None):
    """Ejecuta un comando y va cediendo cada línea de salida (generador).

    Lanza RuntimeError si el comando termina con código distinto de 0.
    """
    cmd = [str(c) for c in cmd]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        cwd=str(cwd) if cwd else None,
        env=env,
    )
    try:
        for linea in proc.stdout:
            linea = linea.rstrip()
            if linea:
                yield linea
        proc.wait()
        if proc.returncode != 0:
            raise RuntimeError(
                f"El comando falló (código {proc.returncode}): {' '.join(cmd[:6])}…"
            )
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
