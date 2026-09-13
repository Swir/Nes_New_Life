@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Capture_Coverage_Acceptance.ps1" %*
set EXITCODE=%ERRORLEVEL%
if not "%EXITCODE%"=="0" if not "%EXITCODE%"=="2" pause
exit /b %EXITCODE%
