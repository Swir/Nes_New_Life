@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Capture_To_Art_Pipeline.ps1" %*
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" pause
exit /b %RC%
