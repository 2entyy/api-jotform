@echo off
setlocal
cd /d "%~dp0.."

if not exist ".venv\Scripts\activate.bat" (
  echo A preparar o motor pela primeira vez, aguarda...
  python -m venv .venv
  call .venv\Scripts\activate.bat
  pip install -r requirements.txt -r backend\requirements.txt
) else (
  call .venv\Scripts\activate.bat
)

if not exist "frontend\node_modules" (
  echo A preparar a interface pela primeira vez, aguarda...
  pushd frontend
  call npm install
  popd
)

start "Video Variator - motor" cmd /k "cd /d "%CD%" && call .venv\Scripts\activate.bat && python -m uvicorn backend.app.main:app --port 8000"

pushd frontend
start "Video Variator - interface" cmd /k "npm run dev"
popd

echo A abrir o browser em alguns segundos...
timeout /t 6 /nobreak >nul
start "" "http://localhost:5173"

endlocal
