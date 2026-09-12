@echo off
setlocal
cd /d "%~dp0"
python "..\tools\FinalRegressionCockpit.py"
if errorlevel 1 (
  echo.
  echo Final Regression Cockpit failed to start. Make sure Python 3.11+ and project requirements are installed.
  pause
)
endlocal
