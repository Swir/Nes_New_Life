@echo off
setlocal
cd /d "%~dp0.."
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 tools\AuthoritativeRemasterStudio.py
) else (
  python tools\AuthoritativeRemasterStudio.py
)
if errorlevel 1 (
  echo.
  echo Authoritative Remaster Studio exited with an error.
  pause
)
endlocal
