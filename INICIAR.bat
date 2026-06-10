@echo off
REM Lanza VideoBoost (Windows).
cd /d "%~dp0"
if not exist .venv (
  echo ERROR: Falta el entorno. Corre primero install\INSTALAR_NVIDIA.bat
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
python app.py
pause
