@echo off
setlocal EnableExtensions
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -STA -File "%~dp0Local_Capture_Bridge.ps1"
set "RC=%ERRORLEVEL%"

echo.
if "%RC%"=="0" (
  echo LOCAL CAPTURE BRIDGE: PASS
) else if "%RC%"=="2" (
  echo LOCAL CAPTURE BRIDGE: SAFE EVIDENCE CREATED, BUT CAPTURE REGRESSION IS PRESENT
) else (
  echo LOCAL CAPTURE BRIDGE: FAILED
)
echo.
pause
exit /b %RC%
