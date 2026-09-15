param(
    [string]$ProjectRoot,
    [string]$RuntimePack,
    [string]$RomPath,
    [switch]$PlanOnly,
    [switch]$NoOpen
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms

$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $ProjectRoot) { $ProjectRoot = Split-Path -Parent $Here }
$ProjectRoot = (Resolve-Path $ProjectRoot).Path
$Tool = Join-Path $ProjectRoot 'tools\regression_auto_continue.py'
$Manifest = Join-Path $ProjectRoot 'FINAL_REGRESSION.json'
$Output = Join-Path $ProjectRoot 'Reports\FinalRegressionAutoContinue'
$Dashboard = Join-Path $Output 'FINAL_REGRESSION_AUTO_CONTINUE.html'
$RecoveryState = Join-Path $env:LOCALAPPDATA 'Swir\TinyToonVisualRemaster\regression-recovery-session.json'
$Guided = Join-Path $Here 'Guided_Regression_Playtest.ps1'
$Resume = Join-Path $Here 'Resume_Regression_Recovery.ps1'
$Release = Join-Path $Here 'Final_Release_Gate.bat'

function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) { return @('py','-3') }
    if (Get-Command python -ErrorAction SilentlyContinue) { return @('python') }
    throw 'Python 3 was not found in PATH.'
}
function Invoke-PythonJson([string[]]$Arguments) {
    $p = Get-PythonCommand
    $exe = $p[0]
    $all = @()
    if ($p.Count -gt 1) { $all += $p[1..($p.Count-1)] }
    $all += $Arguments
    $raw = & $exe @all
    if ($LASTEXITCODE -ne 0) { throw (($raw -join "`n") + "`nPython command failed with exit code $LASTEXITCODE") }
    return (($raw -join "`n") | ConvertFrom-Json)
}
function Pick-Folder([string]$Description) {
    $d = New-Object System.Windows.Forms.FolderBrowserDialog
    $d.Description = $Description
    if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { return $d.SelectedPath }
    return $null
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
if (-not $RuntimePack) { $RuntimePack = Pick-Folder 'Select the exact runtime HD pack for final regression' }
if (-not $RuntimePack) { exit 2 }
$RuntimePack = (Resolve-Path $RuntimePack).Path
if (-not (Test-Path (Join-Path $RuntimePack 'hires.txt'))) { throw 'Runtime pack must contain hires.txt.' }

New-Item -ItemType Directory -Force -Path $Output | Out-Null
Write-Host ''
Write-Host '=== PROJECT #002 — FINAL REGRESSION AUTO-CONTINUE ===' -ForegroundColor Cyan
Write-Host 'This loop sequences work only. Every PASS/FAIL still requires a real exact-build MesenCE observation.' -ForegroundColor Yellow

$iteration = 0
while ($iteration -lt 30) {
    $iteration++
    $plan = Invoke-PythonJson @($Tool, $Manifest, $RuntimePack, $RecoveryState, '--output', $Output)
    Write-Host ''
    Write-Host ('Iteration {0} | State: {1}' -f $iteration, $plan.state) -ForegroundColor Cyan
    Write-Host ('Exact runtime: {0}' -f $plan.pack_fingerprint) -ForegroundColor DarkGray
    if ($plan.case) { Write-Host ('Case: {0}/10 — {1}' -f $plan.case.order, $plan.case.label) -ForegroundColor Magenta }
    Write-Host ('DO THIS NEXT: {0}' -f $plan.next_action) -ForegroundColor Yellow

    if (-not $NoOpen -and (Test-Path $Dashboard)) { Start-Process $Dashboard }
    if ($PlanOnly) { exit 0 }

    switch ($plan.state) {
        'PLAYTEST_CASE_REQUIRED' {
            $args = @('-ProjectRoot', $ProjectRoot, '-RuntimePack', $RuntimePack)
            if ($RomPath) { $args += @('-RomPath', $RomPath) }
            if ($NoOpen) { $args += '-NoOpen' }
            & $Guided @args
            if ($LASTEXITCODE -ne 0) { throw ('Guided regression exited with code ' + $LASTEXITCODE) }
            continue
        }
        'SAME_CASE_RETEST_REQUIRED' {
            $args = @('-ProjectRoot', $ProjectRoot, '-RuntimePack', $RuntimePack)
            if ($RomPath) { $args += @('-RomPath', $RomPath) }
            if ($NoOpen) { $args += '-NoOpen' }
            & $Resume @args
            if ($LASTEXITCODE -ne 0) { throw ('Same-case recovery retest exited with code ' + $LASTEXITCODE) }
            continue
        }
        'RECOVERY_REPAIR_REQUIRED' {
            Write-Host 'A real repair is required before auto-continue can safely resume.' -ForegroundColor Red
            $args = @('-ProjectRoot', $ProjectRoot, '-RuntimePack', $RuntimePack)
            if ($RomPath) { $args += @('-RomPath', $RomPath) }
            if ($NoOpen) { $args += '-NoOpen' }
            & $Resume @args
            $code = $LASTEXITCODE
            Write-Host 'Auto-continue is intentionally stopping at the repair boundary. Re-run this launcher after the repair changes the runtime or completes the required mapping/capture/runtime work.' -ForegroundColor Yellow
            exit $code
        }
        'RECOVERY_BLOCKED' {
            throw 'Persistent regression recovery is BLOCKED. Inspect the recovery dashboard and FINAL_REGRESSION.json; no evidence was altered.'
        }
        'REGRESSION_COMPLETE' {
            Write-Host 'FINAL REGRESSION: 10/10 PASS on one exact runtime fingerprint.' -ForegroundColor Green
            Write-Host 'Dispatching Final Release Gate...' -ForegroundColor Green
            & $Release
            exit $LASTEXITCODE
        }
        default {
            throw ('Unsupported auto-continue state: ' + $plan.state)
        }
    }
}

throw 'Safety stop: final regression auto-continue exceeded 30 orchestration iterations without reaching release or a repair boundary.'
