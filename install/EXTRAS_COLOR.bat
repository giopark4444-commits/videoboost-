@echo off
REM PixelBooster - DDColor: colorizacion de imagenes B/N (el "colorize model" tipo HitPaw).
cd /d "%~dp0\.."

echo == DDColor (colorizacion de imagenes) ==
python -m venv .venv-color
call .venv-color\Scripts\activate.bat
python -m pip install --upgrade pip
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
if not exist vendor mkdir vendor
if not exist models mkdir models
if not exist vendor\DDColor git clone --depth 1 https://github.com/piddnad/DDColor.git vendor\DDColor
pip install -r vendor\DDColor\requirements.txt
pip install huggingface_hub timm
echo Descargando pesos de DDColor...
python -c "from huggingface_hub import hf_hub_download; import shutil,os; os.makedirs('models/DDColor',exist_ok=True); shutil.copy(hf_hub_download('piddnad/ddcolor_modelscope','pytorch_model.pt'),'models/DDColor/pytorch_model.pt')"
call .venv-color\Scripts\deactivate.bat
echo DDColor listo.
pause
