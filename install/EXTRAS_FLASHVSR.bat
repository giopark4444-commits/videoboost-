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

echo Descargando pesos FlashVSR v1.1 (recomendada por los autores)...
python -c "from huggingface_hub import snapshot_download; snapshot_download('JunhaoZhuang/FlashVSR-v1.1', local_dir='vendor/FlashVSR/examples/WanVSR/FlashVSR-v1.1')"
call .venv-flashvsr\Scripts\deactivate.bat

echo.
echo FlashVSR listo (v1.1). Si su README cambia la ruta de pesos, ajustarla ahi:
echo https://github.com/OpenImagingLab/FlashVSR#readme
pause
