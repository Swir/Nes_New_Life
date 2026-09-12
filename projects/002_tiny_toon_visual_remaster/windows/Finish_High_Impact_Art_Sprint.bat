@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0High_Impact_Art_Sprint.ps1" -Finish -Overwrite
if errorlevel 1 (
  echo.
  echo High-Impact Art Sprint finish failed. No release claim was made.
  pause
  exit /b 1
)
echo.
echo High-impact edits imported, candidate pack composed, and Pixel QA completed.
pause
endlocal
