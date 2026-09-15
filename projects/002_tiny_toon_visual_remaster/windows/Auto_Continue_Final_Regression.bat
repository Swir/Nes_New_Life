@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Auto_Continue_Final_Regression.ps1" %*
exit /b %errorlevel%
