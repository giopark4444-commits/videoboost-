"""Retinexformer (caiyuanhao1998, MIT) — realce de imágenes con POCA LUZ.

Transformer de una etapa basado en la teoría Retinex: aclara fotos oscuras /
nocturnas y recupera sombras sin amplificar el ruido. Es un modelo de imagen
(no video). Está construido sobre BasicSR.

Interfaz documentada del repo:
    python3 Enhancement/test_from_dataset.py --opt <yaml> --weights <ckpt>
        --dataset <nombre> --output_dir <carpeta>

Particularidad importante: `test_from_dataset.py` NO lee las imágenes desde un
flag de entrada, sino desde el YAML (`datasets.val.dataroot_lq`), y además carga
SIEMPRE el ground-truth (`dataroot_gt`) para calcular PSNR/SSIM aunque no se use.
Por eso, para procesar una sola imagen del usuario:
  1) copiamos la imagen a una carpeta temporal `lq/`,
  2) usamos esa MISMA carpeta como `gt/` (la métrica sale absurda pero no truena),
  3) escribimos una copia temporal del YAML con esas dos rutas parcheadas,
  4) pasamos `--output_dir` a una carpeta temporal y recogemos el PNG.

Usamos por defecto el modelo **LOL_v2_real** (captura real de poca luz, el de
mejor generalización al mundo real según el README). Vive en .venv-retinexformer.

⚠️ NO PROBADO EN GPU REAL desde este Mac (sin CUDA). Es difusión/transformer
pesado pensado para NVIDIA; verificar flags, ruta de pesos y nombres del YAML en
la RTX 4080 al estrenarlo. La descarga del peso (Google Drive) puede requerir
ajuste manual: ver install/extras_retinexformer.sh.
"""

import re
import shutil
import tempfile
from pathlib import Path

from engines import VENDOR, SALIDAS, correr, python_venv

RETINEXFORMER_DIR = VENDOR / "Retinexformer"

# Modelo por defecto: poca luz real. (config, peso, nombre de dataset).
CONFIG = "Options/RetinexFormer_LOL_v2_real.yml"
PESO = "pretrained_weights/LOL_v2_real.pth"
DATASET = "LOL_v2_real"


def disponible() -> bool:
    """Hay repo clonado + script de inferencia + peso descargado."""
    return (
        (RETINEXFORMER_DIR / "Enhancement" / "test_from_dataset.py").exists()
        and (RETINEXFORMER_DIR / PESO).exists()
    )


def _parchear_yaml(origen: Path, lq_dir: Path, gt_dir: Path, destino: Path):
    """Reescribe dataroot_lq/dataroot_gt del YAML apuntando a carpetas temporales.

    Sustituye la línea completa conservando su indentación (son hermanas bajo
    `val:`), para no depender de la ruta original que trae el repo.
    """
    texto = origen.read_text(encoding="utf-8")
    texto = re.sub(
        r"(?m)^(\s*dataroot_lq\s*:).*$", rf"\1 {lq_dir.as_posix()}", texto
    )
    texto = re.sub(
        r"(?m)^(\s*dataroot_gt\s*:).*$", rf"\1 {gt_dir.as_posix()}", texto
    )
    destino.write_text(texto, encoding="utf-8")


def mejorar(entrada):
    """Generador: cede log y devuelve la ruta de la imagen aclarada."""
    import hardware

    if not disponible():
        raise RuntimeError(
            "Retinexformer no está instalado. Corre install/extras_retinexformer.sh "
            "(o .bat)."
        )
    entrada = Path(entrada)
    py = python_venv(".venv-retinexformer", "install/extras_retinexformer.sh")
    device = "cuda" if hardware.info_sistema()["cuda"] else "cpu"

    tmp = Path(tempfile.mkdtemp(prefix="videoboost_retinexformer_"))
    lq_dir, gt_dir, out_dir = tmp / "lq", tmp / "gt", tmp / "out"
    for d in (lq_dir, gt_dir, out_dir):
        d.mkdir()
    # La imagen va como entrada (lq) y como "gt" para que la carga de GT no falle.
    shutil.copy(entrada, lq_dir / entrada.name)
    shutil.copy(entrada, gt_dir / entrada.name)

    # Copia parcheada del YAML dentro del repo (rutas relativas a su cwd).
    yaml_origen = RETINEXFORMER_DIR / CONFIG
    yaml_tmp = tmp / "config.yml"
    _parchear_yaml(yaml_origen, lq_dir, gt_dir, yaml_tmp)

    cmd = [
        py, "Enhancement/test_from_dataset.py",
        "--opt", yaml_tmp,
        "--weights", PESO,
        "--dataset", DATASET,
        "--output_dir", out_dir,
        # El CLI lee --gpus como string; "0" en CUDA. En CPU igual lo acepta,
        # el modelo cae a CPU si no hay GPU visible (lentísimo, solo de respaldo).
        "--gpus", "0" if device == "cuda" else "-1",
    ]
    try:
        yield f"🌙 Retinexformer · poca luz (LOL_v2_real) · {device}"
        if device != "cuda":
            yield "⚠️ Sin CUDA: corre por CPU y es MUY lento. Pensado para NVIDIA."
        yield from correr(cmd, cwd=RETINEXFORMER_DIR)
        resultados = [
            p for p in out_dir.rglob("*")
            if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")
        ]
        if not resultados:
            raise RuntimeError("Retinexformer terminó pero no generó ninguna imagen.")
        salida = SALIDAS / f"{entrada.stem}_retinexformer.png"
        shutil.copy(resultados[0], salida)
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
