@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Gate_A_Review_Attestation.ps1" %*
exit /b %ERRORLEVEL%
