"""DUT (Annbless/DUTCode, MIT) — estabilización de VIDEO por IA (deep unsupervised
trajectory). Aprende y suaviza la trayectoria de la cámara con una malla de
movimiento (RFDet + PWCNet + propagación de movimiento + smoother), recortando el
temblor para dejar un plano fluido tipo gimbal.

El repo NO trae CLI de video: su `scripts/DUTStabilizer.py` espera los frames del
clip ya recortados como `0.jpg`, `1.jpg`, … en una carpeta `--InputBasePath`, y
escribe un `DUT_stable.mp4` en `--OutputBasePath`. Por eso aquí extraemos los
frames con FFmpeg numerados desde 0, llamamos al script y devolvemos el mp4.

El script hace `model.cuda()` y `x.cuda()` SIN alternativa → en la práctica solo
NVIDIA (CUDA). Además PWCNet usa `cupy` (CUDA). En Mac no corre tal cual: queda
declarado plataforma "ambas" porque el repo es portable en teoría, pero NO se ha
probado en MPS desde aquí. Pesos: 4 .pth (smoother/RFDet/PWCNet/MotionPro) que el
instalador baja de Google Drive a vendor/DUTCode/ckpt/.

⚠️ El archivo LICENSE del repo es MIT (Copyright 2025 Yufei Xu), pero el README aún
dice "for research purpose only, contact us for commercial use": ver incertidumbres.

NO PROBADO EN GPU REAL desde aquí: verificar flags/salida en la 4080.
"""

import shutil
import tempfile
from pathlib import Path

from engines import SALIDAS, VENDOR, correr, python_venv
from engines import ffmpeg_utils as ff

DUT_DIR = VENDOR / "DUTCode"
CKPT = DUT_DIR / "ckpt"


def disponible() -> bool:
    # El script y, al menos, el smoother + el detector de features descargados.
    return ((DUT_DIR / "scripts" / "DUTStabilizer.py").exists()
            and (CKPT / "smoother.pth").exists()
            and (CKPT / "RFDet_640.pth.tar").exists())


def estabilizar(video):
    """Generador: cede log y devuelve la ruta del video estabilizado (mp4).

    Extrae los frames del clip numerados `0.jpg, 1.jpg, …` (lo que espera
    DUTStabilizer.py), corre el modelo DUT y copia el `DUT_stable.mp4` a SALIDAS.
    """
    if not disponible():
        raise RuntimeError(
            "DUT no está instalado. Corre install/extras_dut_stab.sh (o .bat)."
        )
    video = Path(video)
    py = python_venv(".venv-dut", "install/extras_dut_stab.sh")

    tmp = Path(tempfile.mkdtemp(prefix="videoboost_dut_"))
    in_dir, out_dir = tmp / "in", tmp / "out"
    in_dir.mkdir(), out_dir.mkdir()

    try:
        yield "🚀 DUT · estabilización de video por IA (requiere NVIDIA/CUDA)"
        yield "ℹ️ Extrayendo frames (numerados desde 0, como espera DUTStabilizer)…"
        # FFmpeg escribe 0.jpg, 1.jpg, … directamente con -start_number 0 y %d.jpg.
        yield from correr([
            ff.ffmpeg(), "-y", "-i", str(video),
            "-start_number", "0", "-qscale:v", "2",
            str(in_dir / "%d.jpg"),
        ])
        if not any(in_dir.glob("*.jpg")):
            raise RuntimeError("No se pudieron extraer frames del video.")

        # Rutas a los 4 pesos (van como flags al script).
        cmd = [
            py, "scripts/DUTStabilizer.py",
            f"--SmootherPath={CKPT / 'smoother.pth'}",
            f"--RFDetPath={CKPT / 'RFDet_640.pth.tar'}",
            f"--PWCNetPath={CKPT / 'network-default.pytorch'}",
            f"--MotionPro={CKPT / 'MotionPro.pth'}",
            f"--InputBasePath={in_dir}/",
            f"--OutputBasePath={out_dir}/",
        ]
        yield "ℹ️ Estabilizando (primera vez carga RFDet/PWCNet/MotionPro/smoother)…"
        yield from correr(cmd, cwd=DUT_DIR)

        # El script escribe '<prefijo>DUT_stable.mp4'; sin prefijo, 'DUT_stable.mp4'.
        producidos = sorted(out_dir.glob("*DUT_stable.mp4")) or sorted(out_dir.glob("*.mp4"))
        if not producidos:
            raise RuntimeError("DUT terminó pero no generó ningún video.")
        salida = SALIDAS / f"{video.stem}_dut_estable.mp4"
        shutil.copy(producidos[0], salida)
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
