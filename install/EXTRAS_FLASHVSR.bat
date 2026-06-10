@echo off
REM VideoBoost - FlashVSR (CVPR 2026), modo rapido EXPERIMENTAL. Solo NVIDIA.
cd /d "%~dp0\.."

where nvidia-smi >nul 2>nul
if errorlevel 1 (
  echo ERROR: FlashVSR requiere GPU NVIDIA con CUDA.
  pause
  exit /b 1
)

echo == FlashVSR (experimental) ==
python -m venv .venv-flashvsr
call .venv-flashvsr\Scripts\activate.bat
python -m pip install --upgrade pip
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
if not exist vendor mkdir vendor
if not exist vendor\FlashVSR git clone --depth 1 https://github.com/OpenImagingLab/FlashVSR.git vendor\FlashVSR
if exist vendor\FlashVSR\requirements.txt pip install -r vendor\FlashVSR\requirements.txt
pip install huggingface_hub

echo.
echo ATENCION: los pesos de FlashVSR se descargan segun su README (HuggingFace, Git LFS):
echo https://github.com/OpenImagingLab/FlashVSR#readme
pause
