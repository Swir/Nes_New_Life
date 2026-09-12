@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Studio_Grade_Art_Pass.ps1"
if errorlevel 1 pause
endlocal
