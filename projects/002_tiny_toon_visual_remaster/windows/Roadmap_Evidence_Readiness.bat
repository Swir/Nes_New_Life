@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Roadmap_Evidence_Readiness.ps1"
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" pause
exit /b %RC%
