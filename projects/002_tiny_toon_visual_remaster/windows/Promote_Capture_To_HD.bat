@echo off
setlocal EnableExtensions
cd /d "%~dp0\.."

set "PROJECT_ROOT=%CD%"
set "TOOLS=%PROJECT_ROOT%\tools"

where py >nul 2>nul
if %errorlevel%==0 (
  set "PY=py -3"
) else (
  set "PY=python"
)

for /f "usebackq delims=" %%I in (`powershell -NoProfile -STA -Command "Add-Type -AssemblyName System.Windows.Forms; $d=New-Object System.Windows.Forms.FolderBrowserDialog; $d.Description='Select CURRENT MesenCE HD Pack capture'; if($d.ShowDialog() -eq 'OK'){$d.SelectedPath}"`) do set "CURRENT=%%I"
if not defined CURRENT (
  echo No current capture selected.
  pause
  exit /b 2
)

choice /C YN /N /M "Compare against a PREVIOUS capture before promotion? [Y/N] "
if errorlevel 2 goto :run_no_previous
for /f "usebackq delims=" %%I in (`powershell -NoProfile -STA -Command "Add-Type -AssemblyName System.Windows.Forms; $d=New-Object System.Windows.Forms.FolderBrowserDialog; $d.Description='Select PREVIOUS accepted MesenCE capture'; if($d.ShowDialog() -eq 'OK'){$d.SelectedPath}"`) do set "PREVIOUS=%%I"
if not defined PREVIOUS goto :run_no_previous

echo.
echo Regression-safe promotion: current vs previous
echo Current : %CURRENT%
echo Previous: %PREVIOUS%
echo.
%PY% "%TOOLS%\capture_promotion_director.py" "%PROJECT_ROOT%" "%CURRENT%" --previous-capture "%PREVIOUS%" --top 20 --create-sprint
goto :done

:run_no_previous
echo.
echo Promotion without previous-capture comparison.
echo Current: %CURRENT%
echo.
%PY% "%TOOLS%\capture_promotion_director.py" "%PROJECT_ROOT%" "%CURRENT%" --top 20 --create-sprint

:done
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
  echo PROMOTED: capture synced safely and the next HD art sprint is prepared.
) else if "%RC%"=="2" (
  echo BLOCKED: capture regression detected. Existing production workspace was NOT synchronized.
) else (
  echo FAILED: inspect the console and Reports\CapturePromotion.
)
echo Dashboard: %PROJECT_ROOT%\Reports\CapturePromotion\CAPTURE_PROMOTION.html
pause
exit /b %RC%
