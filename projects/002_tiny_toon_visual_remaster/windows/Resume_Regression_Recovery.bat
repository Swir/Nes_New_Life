@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Resume_Regression_Recovery.ps1" %*
exit /b %errorlevel%
