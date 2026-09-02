@echo off
setlocal enabledelayedexpansion
echo ============================================
echo   Video Variator - instalacao (Windows)
echo ============================================
echo.

where winget >nul 2>&1
if errorlevel 1 (
  echo O "winget" nao foi encontrado neste computador.
  echo Instala a "App Installer" na Microsoft Store e volta a correr este ficheiro:
  echo https://apps.microsoft.com/detail/9nblggh4nns1
  pause
  exit /b 1
)

set "NEEDS_RESTART=0"

echo A verificar o Git...
where git >nul 2>&1
if errorlevel 1 (
  echo   A instalar o Git...
  winget install --id Git.Git -e --silent --accept-source-agreements --accept-package-agreements
  set "NEEDS_RESTART=1"
) else (
  echo   Ja esta instalado.
)

echo A verificar o Python...
where python >nul 2>&1
if errorlevel 1 (
  echo   A instalar o Python...
  winget install --id Python.Python.3.12 -e --silent --accept-source-agreements --accept-package-agreements
  set "NEEDS_RESTART=1"
) else (
  echo   Ja esta instalado.
)

echo A verificar o Node.js...
where npm >nul 2>&1
if errorlevel 1 (
  echo   A instalar o Node.js...
  winget install --id OpenJS.NodeJS.LTS -e --silent --accept-source-agreements --accept-package-agreements
  set "NEEDS_RESTART=1"
) else (
  echo   Ja esta instalado.
)

echo A verificar o ffmpeg...
where ffmpeg >nul 2>&1
if errorlevel 1 (
  echo   A instalar o ffmpeg...
  winget install --id Gyan.FFmpeg -e --silent --accept-source-agreements --accept-package-agreements
  set "NEEDS_RESTART=1"
) else (
  echo   Ja esta instalado.
)

if "!NEEDS_RESTART!"=="1" (
  echo.
  echo ============================================
  echo IMPORTANTE: acabei de instalar programas novos.
  echo Fecha esta janela e volta a fazer duplo-clique
  echo neste mesmo ficheiro (bootstrap.bat) outra vez,
  echo para o Windows os reconhecer.
  echo ============================================
  pause
  exit /b 0
)

set "DEST=%USERPROFILE%\Desktop\api-jotform"

if not exist "%DEST%" (
  echo A descarregar o codigo da app...
  git clone --branch claude/video-variations-editing-j58hmi https://github.com/2entyy/api-jotform.git "%DEST%"
) else (
  echo A atualizar o codigo da app...
  pushd "%DEST%"
  git pull
  popd
)

cd /d "%DEST%"

echo A preparar o motor (Python)...
python -m venv .venv
call .venv\Scripts\activate.bat
pip install -r requirements.txt -r backend\requirements.txt

echo A preparar a interface (Node)...
pushd frontend
call npm install
popd

echo A criar atalho no Ambiente de Trabalho...
set "SHORTCUT_VBS=%TEMP%\cs.vbs"
> "%SHORTCUT_VBS%" echo Set oWS = WScript.CreateObject("WScript.Shell")
>> "%SHORTCUT_VBS%" echo sLinkFile = "%USERPROFILE%\Desktop\Abrir Video Variator.lnk"
>> "%SHORTCUT_VBS%" echo Set oLink = oWS.CreateShortcut(sLinkFile)
>> "%SHORTCUT_VBS%" echo oLink.TargetPath = "%DEST%\windows\iniciar.bat"
>> "%SHORTCUT_VBS%" echo oLink.WorkingDirectory = "%DEST%\windows"
>> "%SHORTCUT_VBS%" echo oLink.IconLocation = "shell32.dll, 220"
>> "%SHORTCUT_VBS%" echo oLink.Save
cscript /nologo "%SHORTCUT_VBS%"
del "%SHORTCUT_VBS%"

echo.
echo Tudo pronto! Criei um atalho "Abrir Video Variator" no Ambiente de
echo Trabalho. Da proxima vez usa so esse atalho. A abrir a app agora...
echo.

call "%DEST%\windows\iniciar.bat"

endlocal
