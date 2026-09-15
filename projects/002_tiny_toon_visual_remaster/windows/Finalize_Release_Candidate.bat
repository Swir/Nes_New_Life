@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Finalize_Release_Candidate.ps1" %*
exit /b %errorlevel%
