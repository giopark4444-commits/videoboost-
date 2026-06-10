"""Rutas compartidas y ejecución de subprocesos con log en vivo."""

import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BIN = RAIZ / "bin"
VENDOR = RAIZ / "vendor"
MODELS = RAIZ / "models"
SALIDAS = RAIZ / "salidas"

SALIDAS.mkdir(exist_ok=True)


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
    for linea in proc.stdout:
        linea = linea.rstrip()
        if linea:
            yield linea
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(
            f"El comando falló (código {proc.returncode}): {' '.join(cmd[:6])}…"
        )
