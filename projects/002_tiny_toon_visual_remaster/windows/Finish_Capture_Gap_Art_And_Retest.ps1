param(
    [string]$ProjectRoot,
    [string]$RecoveredCapture,
    [string]$RomPath,
    [string]$OutputPack,
    [switch]$NoOpen
)

$ErrorActionPreference = 'Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $ProjectRoot) { $ProjectRoot = Split-Path -Parent $Here }
$ProjectRoot = (Resolve-Path $ProjectRoot).Path

$Finish = Join-Path $Here 'High_Impact_Art_Sprint.ps1'
$Launcher = Join-Path $Here 'launch_remaster.ps1'
$Tool = Join-Path $ProjectRoot 'tools\regression_capture_gap_retest.py'
$RecoveryDir = Join-Path $ProjectRoot 'Reports\RegressionCaptureGapRecovery'
$RecoveryToken = Join-Path $RecoveryDir 'REGRESSION_CAPTURE_GAP_TOKEN.json'
$RecoveryReport = Join-Path $RecoveryDir 'REGRESSION_CAPTURE_GAP_RECOVERY.json'
$Output = Join-Path $ProjectRoot 'Reports\RegressionCaptureGapRetest'
$RetestToken = Join-Path $Output 'REGRESSION_CAPTURE_GAP_RETEST_TOKEN.json'
$Dashboard = Join-Path $Output 'REGRESSION_CAPTURE_GAP_RETEST.html'
$FullscreenEvidence = Join-Path $ProjectRoot 'Reports\FullscreenPlaytest\FULLSCREEN_PLAYTEST.json'
$StatePath = Join-Path $env:LOCALAPPDATA 'Swir\TinyToonVisualRemaster\capture-session.json'

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
    if ($LASTEXITCODE -ne 0) { throw "Python command failed with exit code $LASTEXITCODE" }
    return (($raw -join "`n") | ConvertFrom-Json)
}
function Pick-Folder([string]$Description) {
    Add-Type -AssemblyName System.Windows.Forms
    $d = New-Object System.Windows.Forms.FolderBrowserDialog
    $d.Description = $Description
    if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { return $d.SelectedPath }
    return $null
}
function Pick-Rom {
    Add-Type -AssemblyName System.Windows.Forms
    $d = New-Object System.Windows.Forms.OpenFileDialog
    $d.Title = 'Select the local Tiny Toon NES ROM — remains local'
    $d.Filter = 'NES ROM (*.nes)|*.nes|All files (*.*)|*.*'
    if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { return $d.FileName }
    return $null
}

if (-not (Test-Path $RecoveryToken)) { throw 'Regression capture-gap recovery token is missing. Run Regression_Capture_Gap_Recovery.bat first.' }
if (-not (Test-Path $RecoveryReport)) { throw 'Regression capture-gap recovery report is missing. Run Regression_Capture_Gap_Recovery.bat first.' }

if (-not $RecoveredCapture -and (Test-Path $StatePath)) {
    try {
        $state = Get-Content -Raw $StatePath | ConvertFrom-Json
        if ($state.current_capture -and (Test-Path $state.current_capture)) { $RecoveredCapture = $state.current_capture }
        if (-not $RomPath -and $state.rom_path -and (Test-Path $state.rom_path)) { $RomPath = $state.rom_path }
    } catch {}
}
if (-not $RecoveredCapture) { $RecoveredCapture = Pick-Folder 'Select the recovered MesenCE capture used for the HD art handoff' }
if (-not $RecoveredCapture) { exit 2 }
$RecoveredCapture = (Resolve-Path $RecoveredCapture).Path
if (-not (Test-Path (Join-Path $RecoveredCapture 'hires.txt'))) { throw 'Recovered capture must contain hires.txt.' }
if (-not $RomPath) { $RomPath = Pick-Rom }
if (-not $RomPath) { exit 2 }
$RomPath = (Resolve-Path $RomPath).Path
if (-not $OutputPack) { $OutputPack = Join-Path $ProjectRoot 'Build\CaptureGapRecoveredCandidate' }

Write-Host ''
Write-Host '=== PROJECT #002 — FINISH RECOVERED CAPTURE ART + SAME-CASE RETEST ===' -ForegroundColor Cyan
Write-Host 'Finishing the exact CurrentImpactSprint through transactional visual/family/Pixel QA...' -ForegroundColor Yellow

& $Finish -Pack $RecoveredCapture -Finish -OutputPack $OutputPack -Overwrite
if ($LASTEXITCODE -ne 0) { throw 'Recovered capture art failed transactional QA; regression retest is blocked.' }
if (-not (Test-Path (Join-Path $OutputPack 'hires.txt'))) { throw 'Transactional finish did not produce a candidate HD pack.' }

New-Item -ItemType Directory -Force -Path $Output | Out-Null
$prepared = Invoke-PythonJson @($Tool, 'prepare', $ProjectRoot, $OutputPack, $RecoveryToken, $RecoveryReport, '--output', $Output)
if ($prepared.status -ne 'SAME_CASE_RETEST_READY') { throw ('Same-case retest preparation failed: ' + $prepared.status) }

Write-Host ''
Write-Host ('RETEST CASE: {0} — {1}' -f $prepared.case.key, $prepared.case.label) -ForegroundColor Magenta
Write-Host ('ROUTE: {0}' -f $prepared.route)
foreach ($cue in @($prepared.cues)) { Write-Host ('  - {0}' -f $cue) }
Write-Host ('Exact repaired runtime fingerprint: {0}' -f $prepared.repaired_runtime_fingerprint) -ForegroundColor DarkGray
Write-Host ''
Write-Host 'Launching repaired build in verified-fullscreen MesenCE...' -ForegroundColor Yellow

& $Launcher -RomPath $RomPath -PackDir $OutputPack -EvidencePath $FullscreenEvidence
if ($LASTEXITCODE -ne 0) { throw 'Verified fullscreen MesenCE launch failed; no regression evidence was recorded.' }

[void](Read-Host 'Perform ONLY the SAME original CAPTURE_GAP case above. Return here and press ENTER when observation is complete')
$choice = ''
while ($choice -notin @('P','F')) {
    $choice = (Read-Host 'P = PASS after real visual verification; F = FAIL and classify remaining defect').Trim().ToUpperInvariant()
}

if ($choice -eq 'P') {
    $notes = Read-Host 'Optional PASS notes (ENTER for none)'
    $record = Invoke-PythonJson @($Tool, 'record', $ProjectRoot, $OutputPack, $RetestToken, 'PASS', '--notes', $notes, '--output', $Output)
    Write-Host ('SAME-CASE PASS RECORDED: {0}' -f $record.case.key) -ForegroundColor Green
} else {
    $categories = @('MISSING_HD','WRONG_PALETTE','ANIMATION_SEAM','TRANSPARENCY','MAPPING','SCALE_OR_FILTER','CAPTURE_GAP','OTHER')
    Write-Host 'Remaining failure categories:' -ForegroundColor Red
    for ($i=0; $i -lt $categories.Count; $i++) { Write-Host ('  {0}. {1}' -f ($i+1), $categories[$i]) }
    $number = 0
    while ($number -lt 1 -or $number -gt $categories.Count) {
        [void][int]::TryParse((Read-Host 'Choose failure category number'), [ref]$number)
    }
    $category = $categories[$number-1]
    $failure = Read-Host 'Describe the remaining visible defect / exact location or state'
    $notes = Read-Host 'Optional notes (ENTER for none)'
    $record = Invoke-PythonJson @($Tool, 'record', $ProjectRoot, $OutputPack, $RetestToken, 'FAIL', '--category', $category, '--failure-notes', $failure, '--notes', $notes, '--output', $Output)
    Write-Host ('SAME-CASE FAIL RECORDED: {0} / {1}' -f $record.case.key, $category) -ForegroundColor Red
}

Write-Host ''
Write-Host $record.next_action -ForegroundColor Yellow
Write-Host ('Current regression gate: {0}' -f $record.cockpit_gate) -ForegroundColor Cyan
if (-not $NoOpen -and (Test-Path $Dashboard)) { Start-Process $Dashboard }
