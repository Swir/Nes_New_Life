@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0High_Impact_Art_Sprint.ps1"
if errorlevel 1 (
  echo.
  echo High-Impact Art Sprint preparation failed.
  pause
  exit /b 1
)
echo.
echo High-Impact Art Sprint is ready. Edit Artwork\CurrentImpactSprint\editable.
pause
endlocal
