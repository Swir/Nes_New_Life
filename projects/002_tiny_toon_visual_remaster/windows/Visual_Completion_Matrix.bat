@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Visual_Completion_Matrix.ps1"
if errorlevel 1 (
  echo.
  echo Visual Completion Matrix failed.
  pause
  exit /b 1
)
endlocal
