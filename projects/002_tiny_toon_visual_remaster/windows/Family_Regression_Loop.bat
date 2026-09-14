@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Family_Regression_Loop.ps1" %*
exit /b %errorlevel%
