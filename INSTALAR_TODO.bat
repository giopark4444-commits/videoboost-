@echo off
REM PixelBooster - doble clic para instalar TODO de una vez (Windows + NVIDIA).
REM Instala la base y TODOS los motores: SeedVR2, Vulkan, FaithDiff, InstantIR,
REM FlashVSR, CodeFormer (caras) y DDColor (color). Si un motor falla, avisa y
REM sigue con los demas. Tarda un buen rato y baja decenas de GB.
title PixelBooster - Instalar todo
cd /d "%~dp0"
cls
echo ====================================================
echo    PixelBooster - instalacion completa (todo-en-uno)
echo ====================================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo No encuentro Python. Instalalo desde https://www.python.org/downloads/windows/
  echo y marca "Add Python to PATH". Luego vuelve a ejecutar este instalador.
  start https://www.python.org/downloads/windows/
  pause
  exit /b 1
)

set FALLIDOS=

echo [1/6] Base ^(app + SeedVR2 + Vulkan^)...
call install\INSTALAR_NVIDIA.bat
if not exist .venv (
  echo La instalacion base no se completo. Lee los mensajes de arriba.
  echo Sin la base no se puede continuar.
  pause
  exit /b 1
)
echo Base lista.
echo.

echo [2/6] FaithDiff ^(imagenes, MIT^)...
call install\EXTRAS_FAITHDIFF.bat
if not exist .venv-faithdiff set FALLIDOS=%FALLIDOS% FaithDiff
echo.

echo [3/6] InstantIR ^(imagenes, Apache 2.0^)...
call install\EXTRAS_INSTANTIR.bat
if not exist .venv-instantir set FALLIDOS=%FALLIDOS% InstantIR
echo.

echo [4/6] FlashVSR ^(video rapido, experimental^)...
call install\EXTRAS_FLASHVSR.bat
if not exist .venv-flashvsr set FALLIDOS=%FALLIDOS% FlashVSR
echo.

echo [5/6] CodeFormer ^(restaurar caras^)...
call install\EXTRAS_CARAS.bat
if not exist .venv-caras set FALLIDOS=%FALLIDOS% CodeFormer
echo.

echo [6/6] DDColor ^(colorizar^)...
call install\EXTRAS_COLOR.bat
if not exist .venv-color set FALLIDOS=%FALLIDOS% DDColor
echo.

echo ====================================================
if "%FALLIDOS%"=="" (
  echo Todo instalado correctamente.
) else (
  echo Instalacion terminada, con avisos.
  echo No se completaron:%FALLIDOS%
  echo Puedes reintentar cada uno con su EXTRAS_*.bat en install\.
)
echo Arranca la app con doble clic en PixelBooster.bat
echo ====================================================
pause
