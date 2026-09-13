@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Capture_Review_Director.ps1" %*
set rc=%ERRORLEVEL%
endlocal & exit /b %rc%
