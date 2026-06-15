"""HAT (XPixelGroup, Apache-2.0) — Hybrid Attention Transformer: super-resolución
clásica (NO difusión) de última generación. Imagen muy nítida y con mucho detalle,
sin las "alucinaciones" típicas de los modelos de difusión. Ideal cuando se quiere
fidelidad alta y un resultado afilado en fotos del mundo real.

Está basado en BasicSR: la inferencia se hace con `python hat/test.py -opt <cfg>.yml`
desde la carpeta del repo. El .yml define el modelo, los pesos y la carpeta de
entrada/salida. Como cada ejecución usa una imagen distinta, generamos un .yml
temporal apuntando a una carpeta con tu imagen y a los pesos Real_HAT_GAN_SRx4
(la variante recomendada para fotos reales: mejor fidelidad que las bicúbicas).

Pesos: Real_HAT_GAN_SRx4.pth, descargados por el instalador a
vendor/HAT/experiments/pretrained_models/ (Google Drive oficial vía gdown).

Solo NVIDIA en la práctica (PyTorch/CUDA). El config admite `num_gpu: 0` (CPU) pero
es lentísimo. NO PROBADO EN GPU REAL desde aquí: verificar config/pesos en la 4080.
"""

import shutil
import tempfile
from pathlib import Path

from engines import SALIDAS, VENDOR, correr, python_venv

HAT_DIR = VENDOR / "HAT"
TEST_PY = HAT_DIR / "hat" / "test.py"
PESOS = HAT_DIR / "experiments" / "pretrained_models" / "Real_HAT_GAN_SRx4.pth"

# Nombre del experimento dentro del .yml; BasicSR escribe la salida en
# results/<NOMBRE_EXP>/visualization/<dataset>/<archivo>.png
NOMBRE_EXP = "videoboost_hat_real"

# Plantilla del config de prueba para fotos reales. La estructura sale del
# config oficial options/test/HAT_GAN_Real_SRx4.yml (modelo HATModel, escala 4,
# SingleImageDataset sin ground-truth, pesos Real_HAT_GAN_SRx4, param_key params_ema).
# Los placeholders {dataroot} y {pesos} se rellenan en cada ejecución.
PLANTILLA_YML = """\
name: {nombre}
model_type: HATModel
scale: 4
num_gpu: {num_gpu}  # 0 = CPU
manual_seed: 0

tile:
  tile_size: 512  # baja este valor si falta VRAM
  tile_pad: 32

datasets:
  test_1:
    name: custom
    type: SingleImageDataset
    dataroot_lq: {dataroot}
    io_backend:
      type: disk

network_g:
  type: HAT
  upscale: 4
  in_chans: 3
  img_size: 64
  window_size: 16
  compress_ratio: 3
  squeeze_factor: 30
  conv_scale: 0.01
  overlap_ratio: 0.5
  img_range: 1.
  depths: [6, 6, 6, 6, 6, 6]
  embed_dim: 180
  num_heads: [6, 6, 6, 6, 6, 6]
  mlp_ratio: 2
  upsampler: 'pixelshuffle'
  resi_connection: '1conv'

path:
  pretrain_network_g: {pesos}
  strict_load_g: true
  param_key_g: 'params_ema'

val:
  save_img: true
  suffix: ~
"""


def disponible() -> bool:
    return TEST_PY.exists() and PESOS.exists()


def mejorar(entrada, escala=4):
    """Generador: cede log y devuelve la ruta de la imagen mejorada.

    Nota: los pesos Real_HAT_GAN son de x4; el parámetro `escala` se acepta por
    consistencia con los demás motores pero el modelo siempre escala x4.
    """
    import hardware

    if not disponible():
        raise RuntimeError(
            "HAT no está instalado. Corre install/extras_hat.sh (o .bat)."
        )
    entrada = Path(entrada).resolve()
    py = python_venv(".venv-hat", "install/extras_hat.sh")
    num_gpu = 1 if hardware.info_sistema()["cuda"] else 0

    tmp = Path(tempfile.mkdtemp(prefix="videoboost_hat_"))
    in_dir = tmp / "in"
    in_dir.mkdir()
    shutil.copy(entrada, in_dir / entrada.name)

    # Config temporal apuntando a nuestra carpeta de entrada y a los pesos.
    cfg = tmp / "hat_test.yml"
    cfg.write_text(PLANTILLA_YML.format(
        nombre=NOMBRE_EXP,
        num_gpu=num_gpu,
        dataroot=str(in_dir),
        pesos=str(PESOS),
    ))

    # BasicSR vuelca los resultados en vendor/HAT/results/<NOMBRE_EXP>/...
    results_dir = HAT_DIR / "results" / NOMBRE_EXP
    shutil.rmtree(results_dir, ignore_errors=True)

    try:
        yield f"🚀 HAT (Real_HAT_GAN x4, nítido no-difusión) · {'cuda' if num_gpu else 'cpu'}"
        if num_gpu == 0:
            yield "⚠️ Sin CUDA: HAT correrá por CPU y será MUY lento."
        yield from correr([py, "hat/test.py", "-opt", str(cfg)], cwd=HAT_DIR)

        resultados = [p for p in results_dir.rglob("*")
                      if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
        if not resultados:
            raise RuntimeError("HAT terminó pero no generó ninguna imagen.")
        salida = SALIDAS / f"{entrada.stem}_hat.png"
        shutil.copy(resultados[0], salida)
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(results_dir, ignore_errors=True)
