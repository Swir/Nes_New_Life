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
echo High-Impact Art Sprint is ready.
choice /C YN /N /M "Apply automatic Studio-Grade Art Pass to untouched sprint masters now? [Y/N] "
if errorlevel 2 goto :manual
call "%~dp0Studio_Grade_Art_Pass.bat"
if errorlevel 1 (
  echo.
  echo Studio-Grade Art Pass failed. The original sprint remains available for manual editing.
  pause
  exit /b 1
)
echo.
echo Studio-Grade baseline is ready. Review Artwork\CurrentImpactSprint\editable, then run Finish + Pixel QA.
pause
exit /b 0

:manual
echo.
echo Automatic polish skipped. Edit Artwork\CurrentImpactSprint\editable manually, then run Finish + Pixel QA.
pause
endlocal
