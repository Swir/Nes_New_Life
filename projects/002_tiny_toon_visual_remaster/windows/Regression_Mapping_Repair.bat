@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%Regression_Mapping_Repair.ps1" %*
exit /b %ERRORLEVEL%
