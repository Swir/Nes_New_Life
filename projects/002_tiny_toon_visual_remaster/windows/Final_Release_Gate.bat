@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Final_Release_Gate.ps1"
if errorlevel 1 (
  echo.
  echo Final Release Gate is blocked or failed. Review the dashboard and message above.
  pause
)
endlocal
