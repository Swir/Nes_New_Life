@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Guided_Regression_Playtest.ps1" %*
exit /b %errorlevel%
