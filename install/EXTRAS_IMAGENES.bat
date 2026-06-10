@echo off
REM VideoBoost - Motores de imagenes: HYPIR (siempre) y SUPIR (pasar --supir).
REM Licencia: HYPIR y SUPIR son de uso NO comercial sin permiso de sus autores.
cd /d "%~dp0\.."

echo == HYPIR (restauracion de imagenes, SIGGRAPH 2025) ==
python -m venv .venv-imagenes
call .venv-imagenes\Scripts\activate.bat
python -m pip install --upgrade pip
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
if not exist vendor mkdir vendor
if not exist models mkdir models
if not exist vendor\HYPIR git clone --depth 1 https://github.com/XPixelGroup/HYPIR.git vendor\HYPIR
pip install -r vendor\HYPIR\requirements.txt
pip install huggingface_hub
echo Descargando pesos HYPIR_sd2.pth...
python -c "from huggingface_hub import hf_hub_download; hf_hub_download('lxq007/HYPIR','HYPIR_sd2.pth', local_dir='models/HYPIR')"
call .venv-imagenes\Scripts\deactivate.bat
echo HYPIR listo.

if "%1"=="--supir" (
  echo.
  echo == SUPIR - maximo detalle, pesado, ideal RTX 4080 ==
  python -m venv .venv-supir
  call .venv-supir\Scripts\activate.bat
  python -m pip install --upgrade pip
  pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
  if not exist vendor\SUPIR git clone --depth 1 https://github.com/Fanghua-Yu/SUPIR.git vendor\SUPIR
  pip install -r vendor\SUPIR\requirements.txt
  echo ATENCION: SUPIR necesita configurar sus pesos a mano. Lee el README de vendor\SUPIR.
)
pause
