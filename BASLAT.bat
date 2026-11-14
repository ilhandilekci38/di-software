@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>&1
if %errorlevel%==0 (set "PY=py -3") else (set "PY=python")
%PY% -c "import flask" >nul 2>&1
if errorlevel 1 (
  echo Flask kuruluyor...
  %PY% -m pip install -r requirements.txt
  if errorlevel 1 (echo Flask kurulumu basarisiz. & pause & exit /b 1)
)
echo Site baslatiliyor: http://127.0.0.1:5080
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:5080'"
%PY% app.py
if errorlevel 1 pause
