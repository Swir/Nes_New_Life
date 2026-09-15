param(
    [string]$ProjectRoot,
    [string]$RuntimePack,
    [switch]$PlanOnly,
    [switch]$NoOpen
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms

$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $ProjectRoot) { $ProjectRoot = Split-Path -Parent $Here }
$ProjectRoot = (Resolve-Path $ProjectRoot).Path
$Tool = Join-Path $ProjectRoot 'tools\regression_failure_router.py'
$SessionTool = Join-Path $ProjectRoot 'tools\regression_recovery_session.py'
$Manifest = Join-Path $ProjectRoot 'FINAL_REGRESSION.json'
$Output = Join-Path $ProjectRoot 'Reports\RegressionFailureRouter'
$Dashboard = Join-Path $Output 'REGRESSION_FAILURE_ROUTER.html'
$RecoveryOutput = Join-Path $ProjectRoot 'Reports\RegressionRecoverySession'
$RecoveryState = Join-Path $env:LOCALAPPDATA 'Swir\TinyToonVisualRemaster\regression-recovery-session.json'
$RecoveryLauncher = Join-Path $Here 'Resume_Regression_Recovery.ps1'

function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) { return @('py','-3') }
    if (Get-Command python -ErrorAction SilentlyContinue) { return @('python') }
    throw 'Python 3 was not found in PATH.'
}
function Pick-Folder([string]$Description) {
    $d = New-Object System.Windows.Forms.FolderBrowserDialog
    $d.Description = $Description
    if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { return $d.SelectedPath }
    return $null
}
function Invoke-PythonJson([string[]]$Arguments) {
    $p = Get-PythonCommand
    $exe = $p[0]
    $all = @()
    if ($p.Count -gt 1) { $all += $p[1..($p.Count-1)] }
    $all += $Arguments
    $raw = & $exe @all
    if ($LASTEXITCODE -ne 0) { throw "Python command failed with exit code $LASTEXITCODE" }
    return (($raw -join "`n") | ConvertFrom-Json)
}

if (-not $RuntimePack) {
    $candidates = @(
        (Join-Path $ProjectRoot 'Build\CaptureGapRecoveredCandidate'),
        (Join-Path $ProjectRoot 'Build\RegressionRepairCandidate'),
        (Join-Path $ProjectRoot 'Build\HighImpactCandidate'),
        (Join-Path $ProjectRoot 'ModernizedPack\playtest_current')
    )
    foreach ($candidate in $candidates) {
        if (Test-Path (Join-Path $candidate 'hires.txt')) { $RuntimePack = $candidate; break }
    }
}
if (-not $RuntimePack) { $RuntimePack = Pick-Folder 'Select the exact runtime HD pack for Final Regression' }
if (-not $RuntimePack) { exit 2 }
$RuntimePack = (Resolve-Path $RuntimePack).Path
if (-not (Test-Path (Join-Path $RuntimePack 'hires.txt'))) { throw 'Runtime pack must contain hires.txt.' }

New-Item -ItemType Directory -Force -Path $RecoveryOutput | Out-Null
$recovery = Invoke-PythonJson @($SessionTool, 'sync', $Manifest, $RuntimePack, $RecoveryState, '--output', $RecoveryOutput)
if ($recovery.phase -eq 'RETEST_REQUIRED') {
    Write-Host ''
    Write-Host 'RECOVERY LOCK ACTIVE — same-case retest has priority over normal regression ordering.' -ForegroundColor Magenta
    Write-Host ('Remembered case: {0} — {1}' -f $recovery.failed_case.key, $recovery.failed_case.label) -ForegroundColor Yellow
    Write-Host ('Current repaired fingerprint: {0}' -f $recovery.current_fingerprint) -ForegroundColor DarkGray
    if ($PlanOnly) {
        Write-Host 'DO THIS NEXT: Resume_Regression_Recovery.bat' -ForegroundColor Yellow
        exit 0
    }
    & $RecoveryLauncher -ProjectRoot $ProjectRoot -RuntimePack $RuntimePack -NoOpen:$NoOpen
    exit $LASTEXITCODE
}
if ($recovery.phase -eq 'BLOCKED') {
    Write-Host ('Recovery state conflict: {0}' -f $recovery.next_action) -ForegroundColor Red
    if ($PlanOnly) { exit 3 }
    & $RecoveryLauncher -ProjectRoot $ProjectRoot -RuntimePack $RuntimePack -NoOpen:$NoOpen
    exit $LASTEXITCODE
}

New-Item -ItemType Directory -Force -Path $Output | Out-Null
$route = Invoke-PythonJson @($Tool, $ProjectRoot, $RuntimePack, '--output', $Output)

Write-Host ''
Write-Host '=== PROJECT #002 — UNIFIED REGRESSION FAILURE ROUTER ===' -ForegroundColor Cyan
Write-Host ('State: {0}' -f $route.state) -ForegroundColor Yellow
Write-Host ('Exact runtime: {0}' -f $route.pack_fingerprint) -ForegroundColor DarkGray
if ($route.failed_case) {
    Write-Host ('FAIL: {0} / {1} — {2}' -f $route.failed_case.key, $route.failed_case.category, $route.failed_case.label) -ForegroundColor Red
    if ($route.failed_case.failure_notes) { Write-Host ('Observed: {0}' -f $route.failed_case.failure_notes) }
    Write-Host ('Recovery session: {0}' -f $recovery.session_id) -ForegroundColor DarkGray
}
Write-Host ('Route: {0}' -f $route.launcher) -ForegroundColor Magenta
if ($route.reason) { Write-Host $route.reason }
Write-Host ('DO THIS NEXT: {0}' -f $route.next_action) -ForegroundColor Yellow

if (-not $NoOpen -and (Test-Path $Dashboard)) { Start-Process $Dashboard }
if ($PlanOnly) { exit 0 }

$launcher = Join-Path $Here $route.launcher
if (-not (Test-Path $launcher)) { throw "Routed launcher does not exist: $launcher" }

Write-Host ''
Write-Host ('Dispatching authoritative route: {0}' -f $route.launcher) -ForegroundColor Cyan
switch ($route.state) {
    'ROUTE_CAPTURE_GAP_RECOVERY' {
        & $launcher -ProjectRoot $ProjectRoot -RuntimePack $RuntimePack -NoOpen:$NoOpen
    }
    'ROUTE_MAPPING_REPAIR' {
        & $launcher -ProjectRoot $ProjectRoot -RuntimePack $RuntimePack -NoOpen:$NoOpen
    }
    'ROUTE_ART_REPAIR' {
        & $launcher -ProjectRoot $ProjectRoot -RuntimePack $RuntimePack -NoOpen:$NoOpen
    }
    'ROUTE_RUNTIME_REPAIR' {
        & $launcher
    }
    'ROUTE_GUIDED_REGRESSION' {
        & $launcher -ProjectRoot $ProjectRoot -RuntimePack $RuntimePack -NoOpen:$NoOpen
    }
    'REGRESSION_COMPLETE' {
        & $launcher
    }
    default { throw ('Unsupported router state: ' + $route.state) }
}
$code = $LASTEXITCODE
if ($code -ne 0) {
    Write-Host ('Routed workflow exited with code {0}; regression evidence remains blocking.' -f $code) -ForegroundColor Red
    exit $code
}
Write-Host 'Routed workflow completed. Re-run this router or Resume_Regression_Recovery.bat to continue the exact remembered case.' -ForegroundColor Green
exit 0
