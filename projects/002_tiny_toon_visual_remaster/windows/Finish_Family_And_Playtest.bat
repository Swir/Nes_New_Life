@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Finish_Family_And_Playtest.ps1"
if errorlevel 1 (
  echo.
  echo Family art commit / QA / playtest failed. No release claim was made.
  pause
  exit /b 1
)
echo.
echo Family art committed, QA passed, and verified fullscreen playtest launched.
pause
endlocal
