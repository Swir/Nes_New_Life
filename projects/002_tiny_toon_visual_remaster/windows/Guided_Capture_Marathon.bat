@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Guided_Capture_Marathon.ps1"
if errorlevel 1 pause
endlocal
