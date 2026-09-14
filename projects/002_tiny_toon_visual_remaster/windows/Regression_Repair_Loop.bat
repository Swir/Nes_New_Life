@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Regression_Repair_Loop.ps1" %*
exit /b %errorlevel%
