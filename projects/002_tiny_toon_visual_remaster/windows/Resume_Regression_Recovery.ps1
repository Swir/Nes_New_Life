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
$Tool = Join-Path $ProjectRoot 'tools\regression_recovery_session.py'
$Manifest = Join-Path $ProjectRoot 'FINAL_REGRESSION.json'
$Output = Join-Path $ProjectRoot 'Reports\RegressionRecoverySession'
$Dashboard = Join-Path $Output 'REGRESSION_RECOVERY_SESSION.html'
$RecoveryState = Join-Path $env:LOCALAPPDATA 'Swir\TinyToonVisualRemaster\regression-recovery-session.json'
$CaptureState = Join-Path $env:LOCALAPPDATA 'Swir\TinyToonVisualRemaster\capture-session.json'
$FullscreenEvidence = Join-Path $ProjectRoot 'Reports\FullscreenPlaytest\FULLSCREEN_PLAYTEST.json'
$Launcher = Join-Path $Here 'launch_remaster.ps1'
$Router = Join-Path $Here 'Regression_Failure_Router.ps1'

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
function Pick-Rom {
    $d = New-Object System.Windows.Forms.OpenFileDialog
    $d.Title = 'Select the local Tiny Toon NES ROM — remains local'
    $d.Filter = 'NES ROM (*.nes)|*.nes|All files (*.*)|*.*'
    if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { return $d.FileName }
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
if (-not $RuntimePack) { $RuntimePack = Pick-Folder 'Select the exact repaired runtime HD pack' }
if (-not $RuntimePack) { exit 2 }
$RuntimePack = (Resolve-Path $RuntimePack).Path
if (-not (Test-Path (Join-Path $RuntimePack 'hires.txt'))) { throw 'Runtime pack must contain hires.txt.' }

New-Item -ItemType Directory -Force -Path $Output | Out-Null
$session = Invoke-PythonJson @($Tool, 'sync', $Manifest, $RuntimePack, $RecoveryState, '--output', $Output)

Write-Host ''
Write-Host '=== PROJECT #002 — REGRESSION RECOVERY SESSION ===' -ForegroundColor Cyan
Write-Host ('Phase: {0}' -f $session.phase) -ForegroundColor Yellow
if ($session.failed_case) {
    Write-Host ('Remembered case: {0} — {1}' -f $session.failed_case.key, $session.failed_case.label) -ForegroundColor Magenta
    Write-Host ('Original category: {0}' -f $session.failed_case.category) -ForegroundColor DarkGray
}
Write-Host ('Current fingerprint: {0}' -f $session.current_fingerprint) -ForegroundColor DarkGray
Write-Host ('DO THIS NEXT: {0}' -f $session.next_action) -ForegroundColor Yellow
if (-not $NoOpen -and (Test-Path $Dashboard)) { Start-Process $Dashboard }
if ($PlanOnly) { exit 0 }

switch ($session.phase) {
    'NO_ACTIVE_RECOVERY' {
        & $Router -ProjectRoot $ProjectRoot -RuntimePack $RuntimePack -NoOpen:$NoOpen
        exit $LASTEXITCODE
    }
    'COMPLETE' {
        Write-Host 'Remembered same-case retest is complete. Returning to the unified regression router.' -ForegroundColor Green
        & $Router -ProjectRoot $ProjectRoot -RuntimePack $RuntimePack -NoOpen:$NoOpen
        exit $LASTEXITCODE
    }
    'REPAIR_REQUIRED' {
        Write-Host ('Resuming remembered repair through {0}.' -f $session.route_launcher) -ForegroundColor Cyan
        & $Router -ProjectRoot $ProjectRoot -RuntimePack $RuntimePack -NoOpen:$NoOpen
        exit $LASTEXITCODE
    }
    'BLOCKED' {
        throw 'Recovery state conflict. Inspect FINAL_REGRESSION.json and the recovery dashboard before continuing.'
    }
    'RETEST_REQUIRED' { }
    default { throw ('Unsupported regression recovery phase: ' + $session.phase) }
}

$plan = Invoke-PythonJson @($Tool, 'plan-retest', $Manifest, $RuntimePack, $RecoveryState, '--output', $Output)
$case = $plan.case
Write-Host ''
Write-Host ('SAME-CASE RETEST — Case {0}/10: {1}' -f $case.order, $case.label) -ForegroundColor Cyan
Write-Host ('Key: {0}' -f $case.key) -ForegroundColor DarkGray
Write-Host ('Route: {0}' -f $case.route) -ForegroundColor White
foreach ($cue in @($case.cues)) { Write-Host ('  - {0}' -f $cue) }
Write-Host ''
Write-Host 'Normal regression ordering is PAUSED until this remembered case is explicitly re-tested.' -ForegroundColor Yellow

if (-not $RomPath -and (Test-Path $CaptureState)) {
    try {
        $capture = Get-Content -Raw $CaptureState | ConvertFrom-Json
        if ($capture.rom_path -and (Test-Path $capture.rom_path)) { $RomPath = $capture.rom_path }
    } catch {}
}
if (-not $RomPath) { $RomPath = Pick-Rom }
if (-not $RomPath) { exit 2 }
$RomPath = (Resolve-Path $RomPath).Path

Write-Host 'Launching the repaired exact build through verified-fullscreen MesenCE...' -ForegroundColor Yellow
& $Launcher -RomPath $RomPath -PackDir $RuntimePack -EvidencePath $FullscreenEvidence
if ($LASTEXITCODE -ne 0) { throw 'Verified fullscreen MesenCE launch failed; same-case retest evidence was not recorded.' }

[void](Read-Host 'Perform ONLY the remembered case above in MesenCE. Return here and press ENTER when observation is complete')
$choice = ''
while ($choice -notin @('P','F')) {
    $choice = (Read-Host 'P = PASS after real visual verification; F = FAIL and classify the remaining defect').Trim().ToUpperInvariant()
}

$notes = Read-Host 'Optional retest notes (ENTER for none)'
if ($choice -eq 'P') {
    $record = Invoke-PythonJson @($Tool, 'record', $Manifest, $RuntimePack, $RecoveryState, 'PASS', '--notes', $notes, '--output', $Output)
    Write-Host ('RECORDED SAME-CASE PASS: {0}' -f $case.key) -ForegroundColor Green
    Write-Host 'The recovery lock is complete; normal regression ordering may resume.' -ForegroundColor Green
} else {
    $categories = @('MISSING_HD','WRONG_PALETTE','ANIMATION_SEAM','TRANSPARENCY','MAPPING','SCALE_OR_FILTER','CAPTURE_GAP','OTHER')
    Write-Host 'Failure categories:' -ForegroundColor Red
    for ($i=0; $i -lt $categories.Count; $i++) { Write-Host ('  {0}. {1}' -f ($i+1), $categories[$i]) }
    $number = 0
    while ($number -lt 1 -or $number -gt $categories.Count) {
        [void][int]::TryParse((Read-Host 'Choose remaining failure category number'), [ref]$number)
    }
    $category = $categories[$number-1]
    $failure = Read-Host 'Describe the remaining visible defect / exact state'
    $record = Invoke-PythonJson @($Tool, 'record', $Manifest, $RuntimePack, $RecoveryState, 'FAIL', '--category', $category, '--failure-notes', $failure, '--notes', $notes, '--output', $Output)
    Write-Host ('SAME-CASE FAIL REMAINS: {0} / {1}' -f $case.key, $category) -ForegroundColor Red
    Write-Host ('Next repair route: {0}' -f $record.route_launcher) -ForegroundColor Yellow
}

if (-not $NoOpen -and (Test-Path $Dashboard)) { Start-Process $Dashboard }
exit 0
