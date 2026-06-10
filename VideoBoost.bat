@echo off
REM VideoBoost - lanzador de doble clic para Windows (PC con GPU NVIDIA).
REM Primera vez: instala todo y descarga los modelos. Despues: solo abre la app.
REM Hazle doble clic. (Si Windows SmartScreen avisa: "Mas informacion" > "Ejecutar de todas formas".)

title VideoBoost
cd /d "%~dp0"
cls
echo ============================================
echo    VideoBoost
echo ============================================
echo.

REM 1. Esta Python?
where python >nul 2>nul
if errorlevel 1 (
  echo No encuentro Python ^(solo hace falta instalarlo una vez^).
  echo Se abrira la pagina de descarga. IMPORTANTE: marca "Add Python to PATH".
  echo Instalalo y vuelve a abrir VideoBoost.
  start https://www.python.org/downloads/windows/
  echo.
  pause
  exit /b 1
)

REM 2. Primera vez: instalacion automatica
if not exist .venv (
  echo Es la primera vez. Voy a instalar VideoBoost y descargar los modelos.
  echo Puede tardar un buen rato ^(varios GB^). Dejalo trabajando con calma.
  echo.
  call install\INSTALAR_NVIDIA.bat
  if not exist .venv (
    echo.
    echo La instalacion no se completo. Lee los mensajes de arriba.
    pause
    exit /b 1
  )
)

REM 3. Arrancar (app.py abre el navegador solo)
echo Abriendo VideoBoost en tu navegador...
echo Para cerrar la app: cierra esta ventana.
echo.
call .venv\Scripts\activate.bat
python app.py
pause
