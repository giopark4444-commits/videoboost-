@echo off
REM VideoBoost - CodeFormer: restauracion de caras (el "face model" tipo HitPaw).
cd /d "%~dp0\.."

echo == CodeFormer (restauracion de caras) ==
python -m venv .venv-caras
call .venv-caras\Scripts\activate.bat
python -m pip install --upgrade pip
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
if not exist vendor mkdir vendor
if not exist vendor\CodeFormer git clone --depth 1 https://github.com/sczhou/CodeFormer.git vendor\CodeFormer
pip install -r vendor\CodeFormer\requirements.txt
cd vendor\CodeFormer
python basicsr\setup.py develop
python scripts\download_pretrained_models.py facelib
python scripts\download_pretrained_models.py CodeFormer
cd ..\..
echo CodeFormer listo.
pause
