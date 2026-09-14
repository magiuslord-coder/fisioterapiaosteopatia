@echo off
setlocal
title Fisio-Osteopatia - Crear EXE
echo.
echo ==========================================
echo   FISIO-OSTEOPATIA - CREAR EXE WINDOWS
echo ==========================================
echo.
where py >nul 2>nul
if errorlevel 1 (
  echo No se encuentra Python.
  echo Instala Python 3.11 o posterior desde https://www.python.org/downloads/windows/
  echo IMPORTANTE: marca "Add python.exe to PATH".
  pause
  exit /b 1
)
echo Instalando PyInstaller...
py -m pip install --upgrade pyinstaller
if errorlevel 1 (
  echo No se pudo instalar PyInstaller.
  pause
  exit /b 1
)
echo Creando ejecutable...
py -m PyInstaller --noconfirm --clean --onefile --windowed --name FisioOsteopatia FisioOsteopatia.py
if errorlevel 1 (
  echo Error al crear el EXE.
  pause
  exit /b 1
)
echo.
echo LISTO. El ejecutable esta en:
echo dist\FisioOsteopatia.exe
echo.
pause
