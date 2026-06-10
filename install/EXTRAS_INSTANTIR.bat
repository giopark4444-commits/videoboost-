@echo off
REM VideoBoost - InstantIR: restauracion de imagenes instantanea (Apache 2.0).
REM SOLO NVIDIA/CUDA. Construido sobre SDXL + DINOv2.
cd /d "%~dp0\.."

where nvidia-smi >nul 2>nul
if errorlevel 1 (
  echo ERROR: InstantIR requiere GPU NVIDIA/CUDA. En Mac usa SeedVR2.
  pause
  exit /b 1
)

echo == InstantIR (restauracion de imagenes, Apache 2.0) ==
python -m venv .venv-instantir
call .venv-instantir\Scripts\activate.bat
python -m pip install --upgrade pip
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
if not exist vendor mkdir vendor
if not exist models mkdir models
if not exist vendor\InstantIR git clone --depth 1 https://github.com/instantX-research/InstantIR.git vendor\InstantIR
pip install -r vendor\InstantIR\requirements.txt
pip install "huggingface_hub[cli]"

echo Descargando modelos (SDXL ~7 GB, DINOv2, pesos InstantIR)...
python -c "from huggingface_hub import snapshot_download; snapshot_download('stabilityai/stable-diffusion-xl-base-1.0', local_dir='models/sdxl-base-1.0'); snapshot_download('facebook/dinov2-large', local_dir='models/dinov2-large'); snapshot_download('InstantX/InstantIR', local_dir='models/InstantIR')"
call .venv-instantir\Scripts\deactivate.bat
echo InstantIR listo.
pause
