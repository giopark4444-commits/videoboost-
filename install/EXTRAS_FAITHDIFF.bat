@echo off
REM VideoBoost - FaithDiff: restauracion fiel de imagenes (MIT, uso comercial libre).
REM SOLO NVIDIA/CUDA. Construido sobre SDXL. No descarga LLaVA (no hace falta).
cd /d "%~dp0\.."

where nvidia-smi >nul 2>nul
if errorlevel 1 (
  echo ERROR: FaithDiff requiere GPU NVIDIA/CUDA. En Mac usa HYPIR o SeedVR2.
  pause
  exit /b 1
)

echo == FaithDiff (restauracion de imagenes, MIT) ==
python -m venv .venv-faithdiff
call .venv-faithdiff\Scripts\activate.bat
python -m pip install --upgrade pip
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
if not exist vendor mkdir vendor
if not exist models\FaithDiff mkdir models\FaithDiff
if not exist vendor\FaithDiff git clone --depth 1 https://github.com/JyChen9811/FaithDiff.git vendor\FaithDiff
pip install -r vendor\FaithDiff\requirements.txt
pip install "huggingface_hub[cli]"

echo Descargando pesos (SDXL RealVisXL ~7 GB, VAE, FaithDiff). Sin LLaVA.
python -c "from huggingface_hub import snapshot_download; snapshot_download('jychen9811/FaithDiff', local_dir='models/FaithDiff'); snapshot_download('SG161222/RealVisXL_V4.0', local_dir='models/FaithDiff/Real_4_SDXL'); snapshot_download('madebyollin/sdxl-vae-fp16-fix', local_dir='models/FaithDiff/VAE_FP16')"
call .venv-faithdiff\Scripts\deactivate.bat
echo FaithDiff listo.
pause
