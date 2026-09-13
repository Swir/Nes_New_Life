@echo off
setlocal
cd /d "%~dp0.."
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 tools\AuthoritativeProductionStudio.py
) else (
  python tools\AuthoritativeProductionStudio.py
)
if errorlevel 1 (
  echo.
  echo Authoritative Production Studio exited with an error.
  pause
)
endlocal
