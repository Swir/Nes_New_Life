@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Full_Capture_To_HD_Autopilot.ps1" %*
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo.
  echo Project #002 HD Autopilot exited with code %RC%.
  pause
)
exit /b %RC%
