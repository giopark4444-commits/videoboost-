"""Descarga los binarios ncnn-Vulkan (Real-ESRGAN, Real-CUGAN, waifu2x, RIFE)
para el sistema operativo actual y los deja en bin/<motor>/.

En Windows también descarga FFmpeg si no está en el PATH.
Se ejecuta solo con la librería estándar (sin pip).
"""

import os
import shutil
import stat
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BIN = RAIZ / "bin"

if sys.platform == "win32":
    OS_KEY = "windows"
elif sys.platform == "darwin":
    OS_KEY = "macos"
else:
    OS_KEY = "ubuntu"

MOTORES = {
    "realesrgan": (
        "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/"
        f"realesrgan-ncnn-vulkan-20220424-{OS_KEY}.zip"
    ),
    "realcugan": (
        "https://github.com/nihui/realcugan-ncnn-vulkan/releases/download/20220728/"
        f"realcugan-ncnn-vulkan-20220728-{OS_KEY}.zip"
    ),
    "waifu2x": (
        "https://github.com/nihui/waifu2x-ncnn-vulkan/releases/download/20220728/"
        f"waifu2x-ncnn-vulkan-20220728-{OS_KEY}.zip"
    ),
    "rife": (
        "https://github.com/nihui/rife-ncnn-vulkan/releases/download/20221029/"
        f"rife-ncnn-vulkan-20221029-{OS_KEY}.zip"
    ),
}

FFMPEG_WIN = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"


def descargar(url: str, destino: Path):
    print(f"  ↓ {url}")

    def progreso(bloques, tam_bloque, total):
        if total > 0:
            pct = min(100, bloques * tam_bloque * 100 // total)
            print(f"\r    {pct}%", end="", flush=True)

    urllib.request.urlretrieve(url, destino, reporthook=progreso)
    print()


def instalar_motor(nombre: str, url: str):
    destino = BIN / nombre
    if destino.exists() and any(destino.rglob(f"{nombre}-ncnn-vulkan*")):
        print(f"✅ {nombre}: ya instalado")
        return
    print(f"📦 {nombre}…")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        zip_path = tmp / "m.zip"
        descargar(url, zip_path)
        extract = tmp / "x"
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(extract)
        # El zip puede traer los archivos en la raíz o dentro de una carpeta.
        exes = list(extract.rglob(f"{nombre}-ncnn-vulkan*"))
        exes = [e for e in exes if e.is_file() and e.suffix in ("", ".exe")]
        if not exes:
            raise RuntimeError(f"No se encontró el ejecutable de {nombre} en el zip.")
        origen = exes[0].parent
        destino.parent.mkdir(parents=True, exist_ok=True)
        if destino.exists():
            shutil.rmtree(destino)
        shutil.copytree(origen, destino)
    if OS_KEY != "windows":
        for f in destino.rglob("*-ncnn-vulkan"):
            f.chmod(f.stat().st_mode | stat.S_IEXEC)
        if OS_KEY == "macos":
            # Quitar la cuarentena de Gatekeeper para que macOS deje ejecutarlos.
            os.system(f'xattr -dr com.apple.quarantine "{destino}" 2>/dev/null')
    print(f"✅ {nombre} listo en bin/{nombre}/")


def instalar_ffmpeg_windows():
    if shutil.which("ffmpeg"):
        print("✅ ffmpeg: ya está en el PATH")
        return
    destino = BIN / "ffmpeg"
    if destino.exists() and any(destino.rglob("ffmpeg.exe")):
        print("✅ ffmpeg: ya instalado en bin/ffmpeg")
        return
    print("📦 ffmpeg (Windows)…")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        zip_path = tmp / "ffmpeg.zip"
        descargar(FFMPEG_WIN, zip_path)
        extract = tmp / "x"
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(extract)
        destino.mkdir(parents=True, exist_ok=True)
        for nombre in ("ffmpeg.exe", "ffprobe.exe"):
            encontrado = next(extract.rglob(nombre), None)
            if encontrado:
                shutil.copy(encontrado, destino / nombre)
    print("✅ ffmpeg listo en bin/ffmpeg/")


if __name__ == "__main__":
    print(f"== PixelBooster · binarios Vulkan para {OS_KEY} ==")
    BIN.mkdir(exist_ok=True)
    for nombre, url in MOTORES.items():
        instalar_motor(nombre, url)
    if OS_KEY == "windows":
        instalar_ffmpeg_windows()
    print("🎉 Binarios Vulkan instalados.")
