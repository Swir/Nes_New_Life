@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Evidence_Bound_Art_Handoff.ps1" %*
exit /b %errorlevel%
