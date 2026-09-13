param(
    [string]$RomPath,
    [string]$CurrentCapture,
    [string]$PreviousCapture,
    [switch]$NoGitHubPrompt
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Guided = Join-Path $PSScriptRoot 'Guided_Capture_Marathon.ps1'
$RoutePlan = Join-Path $ProjectRoot 'Reports\RouteCaptureSequencer\ROUTE_CAPTURE_SESSION_PLAN.json'
$NextTool = Join-Path $ProjectRoot 'tools\next_capture_action.py'
$NextReports = Join-Path $ProjectRoot 'Reports\NextCaptureAction'
$NextDashboard = Join-Path $NextReports 'NEXT_CAPTURE_ACTION.html'

function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) { return @('py', '-3') }
    if (Get-Command python -ErrorAction SilentlyContinue) { return @('python') }
    throw 'Python 3 was not found in PATH.'
}

$guidedArgs = @{}
if ($RomPath) { $guidedArgs['RomPath'] = $RomPath }
if ($CurrentCapture) { $guidedArgs['CurrentCapture'] = $CurrentCapture }
if ($PreviousCapture) { $guidedArgs['PreviousCapture'] = $PreviousCapture }
if ($NoGitHubPrompt) { $guidedArgs['NoGitHubPrompt'] = $true }

Write-Host ''
Write-Host '=== PROJECT #002 — NEXT-BEST CAPTURE LOOP ===' -ForegroundColor Cyan
Write-Host 'Runs the real route-aware fullscreen MesenCE capture workflow first.' -ForegroundColor Yellow
Write-Host 'When gameplay verification returns, the loop resolves the single highest-impact remaining capture pass.'
Write-Host 'No mission or ROADMAP checkbox is completed automatically.'
Write-Host ''

& $Guided @guidedArgs
if (-not $?) { throw 'Guided Capture Marathon failed.' }

if (-not (Test-Path $RoutePlan)) {
    Write-Host 'No route session plan was produced. Run Capture Coverage Acceptance to inspect the current blocker.' -ForegroundColor Yellow
    exit 0
}

$Python = Get-PythonCommand
New-Item -ItemType Directory -Force -Path $NextReports | Out-Null
$exe = $Python[0]
$args = @()
if ($Python.Count -gt 1) { $args += $Python[1..($Python.Count - 1)] }
$args += @($NextTool, $RoutePlan, '--output', $NextReports)
& $exe @args | Out-Host
if ($LASTEXITCODE -ne 0) { throw "Next capture action resolver failed with exit code $LASTEXITCODE" }

if (Test-Path $NextDashboard) {
    Start-Process $NextDashboard
    Write-Host ''
    Write-Host ("NEXT CAPTURE ACTION: {0}" -f $NextDashboard) -ForegroundColor Green
}
