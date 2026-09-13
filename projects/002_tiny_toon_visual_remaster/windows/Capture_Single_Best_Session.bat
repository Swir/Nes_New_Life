@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Capture_Single_Best_Session.ps1" %*
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" echo.
exit /b %RC%
