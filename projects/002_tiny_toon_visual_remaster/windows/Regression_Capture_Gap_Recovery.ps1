param(
    [string]$ProjectRoot,
    [string]$RuntimePack,
    [string]$CurrentCapture,
    [string]$PreviousCapture,
    [string]$RomPath,
    [switch]$NoOpen
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms

$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $ProjectRoot) { $ProjectRoot = Split-Path -Parent $Here }
$ProjectRoot = (Resolve-Path $ProjectRoot).Path

$Tool = Join-Path $ProjectRoot 'tools\regression_capture_gap_recovery.py'
$Marathon = Join-Path $Here 'Guided_Capture_Marathon.ps1'
$ArtHandoff = Join-Path $Here 'Evidence_Bound_Art_Handoff.ps1'
$Output = Join-Path $ProjectRoot 'Reports\RegressionCaptureGapRecovery'
$Token = Join-Path $Output 'REGRESSION_CAPTURE_GAP_TOKEN.json'
$Dashboard = Join-Path $Output 'REGRESSION_CAPTURE_GAP_RECOVERY.html'
$StatePath = Join-Path $env:LOCALAPPDATA 'Swir\TinyToonVisualRemaster\capture-session.json'

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
function Pick-Rom {
    $d = New-Object System.Windows.Forms.OpenFileDialog
    $d.Title = 'Select the local Tiny Toon NES ROM — remains local'
    $d.Filter = 'NES ROM (*.nes)|*.nes|All files (*.*)|*.*'
    if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { return $d.FileName }
    return $null
}
function Invoke-PythonJson([string[]]$Arguments) {
    $p = Get-PythonCommand
    $exe = $p[0]
    $all = @()
    if ($p.Count -gt 1) { $all += $p[1..($p.Count-1)] }
    $all += $Arguments
    $raw = & $exe @all
    $code = $LASTEXITCODE
    if ($code -ne 0 -and -not ($raw -join "`n").Trim()) { throw "Python command failed with exit code $code" }
    $text = ($raw -join "`n")
    if (-not $text.Trim()) { throw 'Python command returned no JSON.' }
    return ($text | ConvertFrom-Json)
}
function Load-State {
    if (-not (Test-Path $StatePath)) { return $null }
    try { return (Get-Content -Raw $StatePath | ConvertFrom-Json) } catch { return $null }
}

$Saved = Load-State
if (-not $CurrentCapture -and $Saved -and $Saved.current_capture -and (Test-Path $Saved.current_capture)) { $CurrentCapture = $Saved.current_capture }
if (-not $PreviousCapture -and $Saved -and $Saved.previous_capture -and (Test-Path $Saved.previous_capture)) { $PreviousCapture = $Saved.previous_capture }
if (-not $RomPath -and $Saved -and $Saved.rom_path -and (Test-Path $Saved.rom_path)) { $RomPath = $Saved.rom_path }

if (-not $RuntimePack) {
    $candidate = Join-Path $ProjectRoot 'Build\HighImpactCandidate'
    $playtest = Join-Path $ProjectRoot 'ModernizedPack\playtest_current'
    if (Test-Path (Join-Path $candidate 'hires.txt')) { $RuntimePack = $candidate }
    elseif (Test-Path (Join-Path $playtest 'hires.txt')) { $RuntimePack = $playtest }
    else { $RuntimePack = Pick-Folder 'Select the exact runtime HD pack that produced CAPTURE_GAP FAIL' }
}
if (-not $RuntimePack) { exit 2 }
$RuntimePack = (Resolve-Path $RuntimePack).Path
if (-not (Test-Path (Join-Path $RuntimePack 'hires.txt'))) { throw 'Runtime pack must contain hires.txt.' }

if (-not $CurrentCapture) { $CurrentCapture = Pick-Folder 'Select CURRENT MesenCE capture / HD pack folder' }
if (-not $CurrentCapture) { exit 2 }
$CurrentCapture = (Resolve-Path $CurrentCapture).Path
if (-not (Test-Path (Join-Path $CurrentCapture 'hires.txt'))) { throw 'Current capture must contain hires.txt.' }
if ($PreviousCapture) { $PreviousCapture = (Resolve-Path $PreviousCapture).Path }
if (-not $RomPath) { $RomPath = Pick-Rom }
if (-not $RomPath) { exit 2 }
$RomPath = (Resolve-Path $RomPath).Path

New-Item -ItemType Directory -Force -Path $Output | Out-Null

Write-Host ''
Write-Host '=== PROJECT #002 — REGRESSION CAPTURE_GAP RECOVERY LOOP ===' -ForegroundColor Cyan
Write-Host 'Exact regression FAIL -> targeted capture route -> capture verification -> evidence-bound HD art handoff.' -ForegroundColor Yellow
Write-Host 'No regression PASS, capture mission, art completion or ROADMAP checkbox is inferred automatically.' -ForegroundColor DarkGray

$planArgs = @($Tool, 'plan', $ProjectRoot, $RuntimePack, $CurrentCapture, '--output', $Output)
if ($PreviousCapture) { $planArgs += @('--previous-capture', $PreviousCapture) }
$Plan = Invoke-PythonJson $planArgs

Write-Host ''
Write-Host ('FAILED CASE: {0} — {1}' -f $Plan.failed_case.key, $Plan.failed_case.label) -ForegroundColor Red
if ($Plan.failed_case.failure_notes) { Write-Host ('Observed gap: {0}' -f $Plan.failed_case.failure_notes) -ForegroundColor Yellow }
Write-Host 'TARGET MISSIONS:' -ForegroundColor Cyan
foreach ($mission in @($Plan.target_missions)) {
    Write-Host ('  - {0} [{1}] — {2}' -f $mission.label, $mission.status, $mission.key)
}
if ($Plan.preferred_session) {
    Write-Host ''
    Write-Host ('PREFERRED CAPTURE PASS: {0}' -f $Plan.preferred_session.label) -ForegroundColor Magenta
    Write-Host ('Mode: {0} | key: {1}' -f $Plan.preferred_session.route_mode, $Plan.preferred_session.session_key) -ForegroundColor DarkGray
    foreach ($instruction in @($Plan.preferred_session.instructions)) { Write-Host ('  - {0}' -f $instruction) }
}
Write-Host ''
Write-Host 'Launching the existing route-aware Guided Capture Marathon.' -ForegroundColor Yellow
Write-Host 'Prioritize the preferred pass and explicitly VERIFY the listed mission(s) in real gameplay.' -ForegroundColor Yellow

$marathonArgs = @{
    RomPath = $RomPath
    CurrentCapture = $CurrentCapture
    NoGitHubPrompt = $true
}
if ($PreviousCapture) { $marathonArgs['PreviousCapture'] = $PreviousCapture }
& $Marathon @marathonArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Guided Capture Marathon did not finish cleanly. Recovery remains blocked.' -ForegroundColor Red
    if (-not $NoOpen -and (Test-Path $Dashboard)) { Start-Process $Dashboard }
    exit $LASTEXITCODE
}

Write-Host ''
Write-Host 'Re-validating the refreshed capture against the original CAPTURE_GAP token...' -ForegroundColor Cyan
$verifyArgs = @($Tool, 'verify', $ProjectRoot, $CurrentCapture, $Token, '--output', $Output)
if ($PreviousCapture) { $verifyArgs += @('--previous-capture', $PreviousCapture) }
$Verify = Invoke-PythonJson $verifyArgs
if ($Verify.status -ne 'CAPTURE_RECOVERED_READY_FOR_HD_HANDOFF') {
    Write-Host 'CAPTURE RECOVERY BLOCKED.' -ForegroundColor Red
    foreach ($blocker in @($Verify.blockers)) { Write-Host ('  - {0}' -f $blocker) -ForegroundColor Red }
    Write-Host $Verify.next_action -ForegroundColor Yellow
    if (-not $NoOpen -and (Test-Path $Dashboard)) { Start-Process $Dashboard }
    exit 3
}

Write-Host 'CAPTURE RECOVERY VERIFIED.' -ForegroundColor Green
Write-Host ('New capture fingerprint: {0}' -f $Verify.current_capture_fingerprint) -ForegroundColor DarkGray
Write-Host 'The regression case is STILL FAIL until new/affected 4x art is built and the same case is re-tested.' -ForegroundColor Yellow

Write-Host ''
Write-Host 'Starting evidence-bound HD art handoff from the refreshed capture...' -ForegroundColor Cyan
$handoffArgs = @{
    ProjectRoot = $ProjectRoot
    CurrentCapture = $CurrentCapture
    NoOpen = $NoOpen
}
if ($PreviousCapture) { $handoffArgs['PreviousCapture'] = $PreviousCapture }
& $ArtHandoff @handoffArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Capture is recovered, but HD art handoff is blocked by its own safety/evidence gate.' -ForegroundColor Yellow
    Write-Host 'Fix that blocker without clearing the original regression FAIL.' -ForegroundColor Yellow
    if (-not $NoOpen -and (Test-Path $Dashboard)) { Start-Process $Dashboard }
    exit $LASTEXITCODE
}

Write-Host ''
Write-Host 'CAPTURE -> ART HANDOFF READY.' -ForegroundColor Green
Write-Host 'Complete the exact affected/new 4x family through transactional QA, then re-run the SAME failed regression case.' -ForegroundColor Green
if (-not $NoOpen -and (Test-Path $Dashboard)) { Start-Process $Dashboard }
exit 0
