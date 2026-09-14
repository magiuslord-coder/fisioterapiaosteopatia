@echo off
setlocal
title Fisio-Osteopatia - Generador de instalador
echo.
echo ==================================================
echo   FISIO-OSTEOPATIA - GENERAR INSTALADOR WINDOWS
echo ==================================================
echo.
echo Este asistente necesita Internet SOLO durante esta
echo primera preparacion para descargar las herramientas
echo de compilacion.
echo.
where py >nul 2>nul
if errorlevel 1 (
  echo.
  echo NO SE ENCUENTRA PYTHON.
  echo.
  echo Para una instalacion final sin Python en el PC del usuario,
  echo hay que compilar el instalador en un equipo Windows.
  echo.
  echo Si quieres evitar instalar Python incluso en este PC,
  echo usa la opcion GitHub Actions incluida en esta carpeta.
  echo.
  pause
  exit /b 1
)
call "%~dp0CREAR_EXE_WINDOWS.bat"
if errorlevel 1 exit /b 1
if not exist "%~dp0installer" mkdir "%~dp0installer"
where ISCC.exe >nul 2>nul
if errorlevel 1 (
  echo.
  echo PyInstaller ha creado el EXE correctamente:
  echo %~dp0dist\FisioOsteopatia.exe
  echo.
  echo Para generar el instalador MSI/EXE con asistente de instalacion,
  echo instala Inno Setup y abre INSTALADOR_INNO_SETUP.iss.
  pause
  exit /b 0
)
ISCC.exe "%~dp0INSTALADOR_INNO_SETUP.iss"
echo.
echo Instalador creado en la carpeta installer.
pause
