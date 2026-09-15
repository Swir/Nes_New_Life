@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%Finish_Capture_Gap_Art_And_Retest.ps1" %*
set "CODE=%ERRORLEVEL%"
if not "%CODE%"=="0" (
  echo.
  echo Capture-gap art finish / same-case retest exited with code %CODE%.
)
exit /b %CODE%
