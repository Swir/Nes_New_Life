@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Continue_HD_Art_Session.ps1"
if errorlevel 1 (
  echo.
  echo Art session continuation blocked. Review Pixel QA / Visual Completion blockers before continuing.
  pause
  exit /b 1
)
echo.
echo Art session finished and the next exact high-impact batch is ready when work remains.
pause
endlocal
