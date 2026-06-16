"""ShadowFormer (GuoLanqing, MIT) — eliminación de SOMBRAS en imágenes con un
transformer de contexto global (AAAI 2023). Quita la sombra proyectada y nivela
la iluminación conservando la textura de fondo. Pesos ISTD / ISTD+ / SRD.

⚠️ REQUIERE MÁSCARA: el modelo recibe (imagen, máscara) y la máscara marca la
región de sombra (blanco = sombra). Como aquí trabajamos sobre una sola foto sin
máscara anotada, usamos una **máscara uniforme blanca** (toda la imagen tratada
como sombra) — funciona razonablemente para sombras suaves/globales; para sombras
duras muy localizadas lo ideal sería una máscara real pintada a mano. Lo dejamos
documentado para poder enchufar luego un detector de sombras automático.

CLI real (test.py, propio del repo, distinto de options.py):
    python test.py --input_dir <dir con test_A/test_B/test_C> --weights <pth>
                   --result_dir <dir> --save_images
El loader (get_validation_data → DataLoaderVal) exige las 3 subcarpetas PNG:
    test_A = imagen con sombra · test_B = máscara · test_C = ground-truth.
test_C solo se usa para métricas (--cal_metrics), que NO pedimos; pero la carpeta
debe existir y tener un PNG o el __init__ del dataset revienta → copiamos ahí la
propia entrada como relleno. La salida se guarda en result_dir/<nombre>.png.

Transformer ligero (no es difusión): corre en CPU/MPS y CUDA → plataforma ambas.
Pesos en Google Drive (los baja el instalador a models/ShadowFormer/).
NO PROBADO EN GPU REAL desde aquí: verificar flags en la 4080.
"""

import shutil
import tempfile
from pathlib import Path

from engines import MODELS, SALIDAS, VENDOR, correr, python_venv

SHADOWFORMER_DIR = VENDOR / "ShadowFormer"
CKPT_DIR = MODELS / "ShadowFormer"          # pesos descargados (model_*.pth)
PESO_DEFECTO = CKPT_DIR / "ISTD_model_best.pth"

# El modelo recibe una máscara de sombra. No tenemos una anotada → máscara
# uniforme. Lo señalamos para la UI / quien mantenga.
REQUIERE_MASCARA = True


def disponible() -> bool:
    return (SHADOWFORMER_DIR / "test.py").exists() and PESO_DEFECTO.exists()


def _peso() -> Path:
    """Primer .pth disponible en models/ShadowFormer (ISTD/ISTD+/SRD)."""
    if PESO_DEFECTO.exists():
        return PESO_DEFECTO
    candidatos = sorted(CKPT_DIR.glob("*.pth")) if CKPT_DIR.exists() else []
    if candidatos:
        return candidatos[0]
    return PESO_DEFECTO


def mejorar(entrada):
    """Generador: cede log y devuelve la ruta de la imagen sin sombra.

    Usa una máscara uniforme (toda la imagen marcada como sombra) porque
    trabajamos sobre una sola foto sin máscara anotada.
    """
    from PIL import Image

    if not disponible():
        raise RuntimeError(
            "ShadowFormer no está instalado (o faltan pesos). "
            "Corre install/extras_shadowformer.sh (o .bat)."
        )
    entrada = Path(entrada)
    py = python_venv(".venv-shadowformer", "install/extras_shadowformer.sh")

    # El loader del repo solo acepta PNG y exige las 3 subcarpetas.
    tmp = Path(tempfile.mkdtemp(prefix="videoboost_shadowformer_"))
    base = tmp / "test"
    dir_a, dir_b, dir_c = base / "test_A", base / "test_B", base / "test_C"
    for d in (dir_a, dir_b, dir_c):
        d.mkdir(parents=True)

    try:
        # Imagen con sombra → test_A (forzada a PNG RGB con nombre estable).
        img = Image.open(entrada).convert("RGB")
        nombre = entrada.stem + ".png"
        img.save(dir_a / nombre)

        # Máscara uniforme blanca (= toda la imagen es "sombra") → test_B.
        mascara = Image.new("L", img.size, 255)
        mascara.save(dir_b / nombre)

        # Ground-truth de relleno (no se usa sin --cal_metrics) → test_C.
        img.save(dir_c / nombre)

        out_dir = tmp / "out"
        out_dir.mkdir()

        cmd = [
            py, "test.py",
            "--input_dir", base,            # carpeta que contiene test_A/B/C
            "--weights", _peso(),
            "--result_dir", out_dir,
            "--save_images",
            "--win_size", 10,               # debe coincidir con el peso ISTD
        ]
        yield "🚀 ShadowFormer · eliminación de sombras (máscara uniforme)"
        yield "ℹ️ Sin máscara anotada se trata toda la imagen como sombra; ideal para sombras suaves/globales."
        yield from correr(cmd, cwd=SHADOWFORMER_DIR)

        resultados = [p for p in out_dir.rglob("*")
                      if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
        if not resultados:
            raise RuntimeError("ShadowFormer terminó pero no generó ninguna imagen.")
        salida = SALIDAS / f"{entrada.stem}_sinsombra.png"
        shutil.copy(resultados[0], salida)
        return str(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
