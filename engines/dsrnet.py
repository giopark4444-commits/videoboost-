"""DSRNet (mingcv, Apache-2.0) — eliminación de REFLEJOS en una sola imagen
(single image reflection removal): separa la foto en capa de transmisión (la
escena limpia, sin el reflejo del cristal/ventana) y capa de reflejo, y nos
quedamos con la transmisión. Útil para fotos tomadas a través de vidrio.

CLI del repo (no es input/output directo, va por "dataset"): se le pasa una
carpeta con las imágenes en `--base_dir` (el RealDataset lee los archivos
directamente de esa carpeta) y los resultados caen en
`./checkpoints/{name}/{timestamp}/test/{nombre_imagen}/{name}_l.png` (la capa
limpia "_l"; "_r" es el reflejo y "_rr" la reconstrucción). Pesos del repo en
Google Drive → carpeta weights/ (dsrnet_l_epoch18.pt). Vive en .venv-dsrnet.

Funciona en ambas plataformas: es una red convolucional (no difusión), corre en
CUDA y también en CPU con `--gpu_ids -1` (en Mac no hay flag MPS en el CLI, así
que usamos CPU; razonablemente rápido para una sola imagen). NO PROBADO EN GPU
REAL desde aquí: verificar flags/salida en la 4080.
"""

import shutil
import tempfile
from pathlib import Path

from engines import MODELS, SALIDAS, VENDOR, correr, python_venv

DSRNET_DIR = VENDOR / "DSRNet"
PESOS = MODELS / "DSRNet"

# Nombre del experimento: define el prefijo del archivo de salida ({name}_l.png).
NOMBRE = "vb_dsrnet"

# Variante grande (mejor calidad) + su peso. Si solo existiera la pequeña, se
# podría cambiar a ("dsrnet_s", "dsrnet_s_epoch16.pt").
INET = "dsrnet_l"
PESO_ARCHIVO = "dsrnet_l_epoch18.pt"


def disponible() -> bool:
    """Hay repo Y existe el peso descargado (sin pesos el CLI no arranca)."""
    return (DSRNET_DIR / "test_sirs.py").exists() and (PESOS / PESO_ARCHIVO).exists()


def mejorar(entrada):
    """Generador: cede log y devuelve la ruta de la imagen sin reflejos."""
    import hardware

    if not (DSRNET_DIR / "test_sirs.py").exists():
        raise RuntimeError(
            "DSRNet no está instalado. Corre install/extras_dsrnet.sh (o .bat)."
        )
    peso = PESOS / PESO_ARCHIVO
    if not peso.exists():
        raise RuntimeError(
            f"Falta el peso de DSRNet ({PESO_ARCHIVO}). Está en Google Drive; "
            "colócalo en models/DSRNet/ o reejecuta el instalador con DSRNET_GDRIVE."
        )

    entrada = Path(entrada)
    py = python_venv(".venv-dsrnet", "install/extras_dsrnet.sh")
    cuda = hardware.info_sistema()["cuda"]
    # gpu_ids "0" en NVIDIA; "-1" = CPU (Mac Apple Silicon: el CLI no expone MPS).
    gpu_ids = "0" if cuda else "-1"

    tmp = Path(tempfile.mkdtemp(prefix="videoboost_dsrnet_"))
    in_dir = tmp / "in"
    in_dir.mkdir()
    # RealDataset lee los archivos directamente de base_dir.
    shutil.copy(entrada, in_dir / entrada.name)

    # Aislamos las salidas en checkpoints/{NOMBRE}/ dentro del tmp para
    # localizarlas sin pelear con el timestamp que el repo añade.
    ckpt_dir = tmp / "checkpoints"

    cmd = [
        py, "test_sirs.py",
        "--inet", INET,
        "--model", "dsrnet_model_sirs",
        "--dataset", "sirs_dataset",
        "--name", NOMBRE,
        "--hyper",
        "--if_align",
        "--resume",
        "--weight_path", str(peso),
        "--base_dir", str(in_dir),
        "--checkpoints_dir", str(ckpt_dir),
        "--gpu_ids", gpu_ids,
        "--nThreads", "0",   # evita workers (más estable en subprocess/CPU)
        "--no-log",
    ]
    try:
        yield f"🚀 DSRNet · quitar reflejos · {INET} · {'cuda' if cuda else 'cpu'}"
        if not cuda:
            yield "ℹ️ Sin GPU NVIDIA: corre en CPU (lento pero funciona para una imagen)."
        yield from correr(cmd, cwd=DSRNET_DIR)

        # Salida = capa de transmisión limpia: .../test/{stem_imagen}/{NOMBRE}_l.png
        # El repo crea una subcarpeta por imagen usando el nombre del archivo.
        candidatos = sorted(ckpt_dir.rglob(f"{NOMBRE}_l.png"))
        if not candidatos:
            # Plan B: cualquier "_l.png" generado (por si cambió el prefijo).
            candidatos = sorted(ckpt_dir.rglob("*_l.png"))
        if not candidatos:
            raise RuntimeError("DSRNet terminó pero no se encontró la imagen limpia (_l.png).")

        salida = SALIDAS / f"{entrada.stem}_sinreflejo.png"
        shutil.copy(candidatos[0], salida)
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
