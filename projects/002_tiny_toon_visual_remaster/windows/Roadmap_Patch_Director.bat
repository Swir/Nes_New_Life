@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Roadmap_Patch_Director.ps1" %*
set "RC=%ERRORLEVEL%"
endlocal & exit /b %RC%
