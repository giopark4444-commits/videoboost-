"""SCUNet (cszn, Apache-2.0) — denoise CIEGO de fotos reales con red Swin-Conv-UNet.
Una sola pasada determinista (NO es difusión): limpia ruido real de cámara/compresión
sin inventar textura nueva. Hay dos pesos "real": PSNR (más fiel, sin alucinar) y GAN
(más nítido/agresivo). También trae variantes por nivel de ruido fijo (15/25/50) en
color y gris, útiles para ruido conocido.

CLI estándar del repo: main_test_scunet_real_application.py --model_name <modelo>
--testset_name <set> --model_zoo <dir-pesos> --testsets <dir-entrada> --results <dir-sal>.
El script lee las imágenes de testsets/{testset_name}/ y guarda los PNG en
results/{testset_name}_{model_name}/, conservando el nombre del archivo. Los pesos NO
se autodescargan: el instalador los baja del release v1.0 de KAIR a model_zoo/.

Device: el script usa `cuda` si está disponible y si no `cpu` (no tiene rama MPS). Al
ser una CNN ligera (no SD), en Mac corre por CPU de forma práctica (más lento pero
usable), por eso lo damos como AMBAS plataformas. Vive en .venv-scunet. NO PROBADO EN
GPU REAL desde aquí (este Mac no tiene CUDA): verificar flags en la 4080.
"""

import shutil
import tempfile
from pathlib import Path

from engines import MODELS, SALIDAS, VENDOR, correr, python_venv

SCUNET_DIR = VENDOR / "SCUNet"
# Carpeta de pesos compartida del proyecto (el instalador baja aquí los .pth).
PESOS_DIR = MODELS / "SCUNet"

# Modelos expuestos. Los dos "real" son el caso de uso principal (denoise ciego real);
# las variantes por sigma quedan disponibles para ruido conocido. El sufijo del .pth
# coincide con el nombre del modelo.
MODELOS = [
    "scunet_color_real_psnr",   # real, fiel (recomendado: no alucina textura)
    "scunet_color_real_gan",    # real, más nítido/agresivo (puede inventar detalle)
    "scunet_color_15",
    "scunet_color_25",
    "scunet_color_50",
    "scunet_gray_15",
    "scunet_gray_25",
    "scunet_gray_50",
]


def disponible() -> bool:
    """Hay SCUNet si existe el script de inferencia y al menos un .pth descargado."""
    if not (SCUNET_DIR / "main_test_scunet_real_application.py").exists():
        return False
    return any((PESOS_DIR / f"{m}.pth").exists() for m in MODELOS)


def mejorar(entrada, modelo="scunet_color_real_psnr"):
    """Generador: cede log y devuelve la ruta de la imagen sin ruido."""
    if not disponible():
        raise RuntimeError(
            "SCUNet no está instalado. Corre install/extras_scunet.sh (o .bat)."
        )
    if modelo not in MODELOS:
        raise RuntimeError(f"Modelo SCUNet desconocido: {modelo}. Usa uno de {MODELOS}.")
    if not (PESOS_DIR / f"{modelo}.pth").exists():
        raise RuntimeError(
            f"Faltan los pesos de '{modelo}' ({modelo}.pth). Vuelve a correr el "
            "instalador para descargarlos del release v1.0 de KAIR."
        )

    entrada = Path(entrada)
    py = python_venv(".venv-scunet", "install/extras_scunet.sh")

    # El script trabaja por carpetas fijas testsets/{set}/ y results/{set}_{modelo}/.
    # Montamos un testset temporal con un nombre único y le pasamos --testsets y
    # --results apuntando a directorios propios, para no ensuciar el repo.
    tmp = Path(tempfile.mkdtemp(prefix="videoboost_scunet_"))
    set_name = "vb"
    testsets, results = tmp / "testsets", tmp / "results"
    in_dir = testsets / set_name
    in_dir.mkdir(parents=True)
    results.mkdir()
    shutil.copy(entrada, in_dir / entrada.name)

    cmd = [
        py, "main_test_scunet_real_application.py",
        "--model_name", modelo,
        "--testset_name", set_name,
        "--model_zoo", PESOS_DIR,    # pesos compartidos del proyecto
        "--testsets", testsets,
        "--results", results,
    ]
    try:
        yield f"🚀 SCUNet · {modelo} · denoise ciego"
        yield from correr(cmd, cwd=SCUNET_DIR)
        # Salida en results/{set}_{modelo}/{stem}.png (nombre conservado, forzado PNG).
        resultados = [p for p in results.rglob("*")
                      if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
        if not resultados:
            raise RuntimeError("SCUNet terminó pero no generó ninguna imagen.")
        salida = SALIDAS / f"{entrada.stem}_scunet.png"
        shutil.copy(resultados[0], salida)
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
