@echo off
REM VideoBoost - Instalador para Windows con GPU NVIDIA (ej. RTX 4080).
REM Instala: entorno Python, PyTorch CUDA, SeedVR2, motores Vulkan y FFmpeg.
cd /d "%~dp0\.."

echo == VideoBoost - instalador para Windows + NVIDIA ==

where python >nul 2>nul
if errorlevel 1 (
  echo ERROR: No se encontro Python. Instalalo desde https://www.python.org/downloads/
  echo        y marca "Add Python to PATH" durante la instalacion.
  pause
  exit /b 1
)

echo Creando entorno .venv...
python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

if not exist vendor mkdir vendor
if not exist models mkdir models
if not exist vendor\seedvr2 (
  echo Clonando SeedVR2...
  git clone --depth 1 https://github.com/numz/ComfyUI-SeedVR2_VideoUpscaler.git vendor\seedvr2
)
pip install -r vendor\seedvr2\requirements.txt

python install\descargar_vulkan.py

echo.
echo Instalacion base completa. Ejecuta INICIAR.bat
echo Para los motores de imagenes: install\EXTRAS_FAITHDIFF.bat (recomendado) o EXTRAS_INSTANTIR.bat
echo Para FlashVSR (modo rapido experimental):   install\EXTRAS_FLASHVSR.bat
pause
