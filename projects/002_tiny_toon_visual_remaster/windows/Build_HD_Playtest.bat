@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Build_HD_Playtest.ps1"
if errorlevel 1 (
  echo.
  echo HD Playtest build failed. Review the error above.
  pause
)
endlocal
