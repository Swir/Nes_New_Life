param(
    [string]$ProjectRoot,
    [string]$RuntimePack,
    [string]$RomPath,
    [switch]$Overwrite,
    [switch]$PrepareOnly,
    [switch]$NoOpen
)

$ErrorActionPreference = 'Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $ProjectRoot) { $ProjectRoot = Split-Path -Parent $Here }
$Tool = Join-Path $ProjectRoot 'tools\regression_repair_sprint.py'
$Launcher = Join-Path $Here 'launch_remaster.ps1'
$RepairKit = Join-Path $ProjectRoot 'Artwork\CurrentRepairSprint'
$RepairPack = Join-Path $ProjectRoot 'Build\RegressionRepairCandidate'
$Dashboard = Join-Path $ProjectRoot 'Reports\RegressionRepairSprint\REGRESSION_REPAIR_SPRINT.html'
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
    if ($LASTEXITCODE -ne 0) { throw (($raw -join "`n") + "`nPython command failed with exit code $LASTEXITCODE") }
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

if (-not $RuntimePack) {
    $candidate = Join-Path $ProjectRoot 'Build\HighImpactCandidate'
    $playtest = Join-Path $ProjectRoot 'ModernizedPack\playtest_current'
    if (Test-Path (Join-Path $candidate 'hires.txt')) { $RuntimePack = $candidate }
    elseif (Test-Path (Join-Path $playtest 'hires.txt')) { $RuntimePack = $playtest }
    else { $RuntimePack = Pick-Folder 'Select exact runtime HD pack containing the authoritative FAIL' }
}
if (-not $RuntimePack) { exit 2 }
$RuntimePack = (Resolve-Path $RuntimePack).Path
if (-not (Test-Path (Join-Path $RuntimePack 'hires.txt'))) { throw 'Runtime pack must contain hires.txt.' }

$prepareArgs = @($Tool, 'prepare', $ProjectRoot, $RuntimePack)
if ($Overwrite) { $prepareArgs += '--overwrite' }
Write-Host ''
Write-Host '=== PROJECT #002 — FAILED REGRESSION → MINIMAL REPAIR → SAME-CASE RETEST ===' -ForegroundColor Cyan
$prepared = Invoke-PythonJson $prepareArgs
if ($prepared.status -ne 'REPAIR_SPRINT_READY') {
    Write-Host ('Repair sprint not created: {0}' -f $prepared.status) -ForegroundColor Yellow
    Write-Host $prepared.next_action -ForegroundColor Yellow
    Write-Host ('Recommended launcher: {0}' -f $prepared.launcher)
    if (-not $NoOpen -and (Test-Path $Dashboard)) { Start-Process $Dashboard }
    exit 4
}

Write-Host ('Failed case: {0} / {1}' -f $prepared.failed_case.key, $prepared.failed_case.category) -ForegroundColor Red
Write-Host ('Minimal repair items: {0}' -f $prepared.repair_items) -ForegroundColor Cyan
$board = Join-Path $RepairKit $prepared.local_board
$editable = Join-Path $RepairKit 'editable'
if (-not $NoOpen) {
    if (Test-Path $board) { Start-Process $board }
    if (Test-Path $editable) { Start-Process explorer.exe $editable }
}
if ($PrepareOnly) {
    Write-Host 'Repair sprint prepared. Finish later by rerunning without -PrepareOnly.' -ForegroundColor Green
    exit 0
}

$answer = (Read-Host 'Edit ONLY CurrentRepairSprint\editable. Press ENTER when the repair is ready for transactional QA, or Q to stop').Trim().ToUpperInvariant()
if ($answer -eq 'Q') { exit 0 }

$finished = Invoke-PythonJson @($Tool, 'finish', $ProjectRoot, $RuntimePack, '--output-pack', $RepairPack)
if ($finished.status -ne 'REPAIR_COMMITTED_RETEST_REQUIRED') {
    Write-Host ('Repair QA blocked: {0}' -f $finished.status) -ForegroundColor Red
    Write-Host $finished.next_action -ForegroundColor Yellow
    if (-not $NoOpen -and (Test-Path $Dashboard)) { Start-Process $Dashboard }
    exit 5
}
Write-Host 'TRANSACTIONAL REPAIR COMMITTED.' -ForegroundColor Green
Write-Host ('Repaired fingerprint: {0}' -f $finished.repaired_runtime_fingerprint) -ForegroundColor DarkGray
Write-Host ('RETEST SAME CASE: {0}' -f $finished.failed_case.label) -ForegroundColor Cyan
Write-Host ('ROUTE: {0}' -f $finished.retest_route)
foreach ($cue in @($finished.retest_cues)) { Write-Host ('  - {0}' -f $cue) }

if (-not $RomPath -and (Test-Path $StatePath)) {
    try {
        $state = Get-Content -Raw $StatePath | ConvertFrom-Json
        if ($state.rom_path -and (Test-Path $state.rom_path)) { $RomPath = $state.rom_path }
    } catch {}
}
if (-not $RomPath) { $RomPath = Pick-Rom }
if (-not $RomPath) { exit 2 }
$RomPath = (Resolve-Path $RomPath).Path

Write-Host 'Launching repaired exact build in verified-fullscreen MesenCE...' -ForegroundColor Yellow
& $Launcher -RomPath $RomPath -PackDir $RepairPack -EvidencePath $FullscreenEvidence
if ($LASTEXITCODE -ne 0) { throw 'Verified fullscreen launch failed; repair retest evidence was not recorded.' }
[void](Read-Host 'Perform ONLY the SAME failed case above. Return here and press ENTER when observation is complete')
$choice = ''
while ($choice -notin @('P','F')) {
    $choice = (Read-Host 'P = repaired case PASS; F = defect still visible').Trim().ToUpperInvariant()
}
if ($choice -eq 'P') {
    $note = Read-Host 'Optional repair PASS notes (ENTER for none)'
    $result = Invoke-PythonJson @($Tool, 'retest', $ProjectRoot, $RepairPack, 'PASS', '--notes', $note)
    Write-Host 'REPAIR RETEST PASS recorded for the exact repaired fingerprint.' -ForegroundColor Green
} else {
    $categories = @('MISSING_HD','WRONG_PALETTE','ANIMATION_SEAM','TRANSPARENCY','MAPPING','SCALE_OR_FILTER','CAPTURE_GAP','OTHER')
    for ($i=0; $i -lt $categories.Count; $i++) { Write-Host ('  {0}. {1}' -f ($i+1), $categories[$i]) }
    $number = 0
    while ($number -lt 1 -or $number -gt $categories.Count) {
        [void][int]::TryParse((Read-Host 'Choose current failure category number'), [ref]$number)
    }
    $category = $categories[$number-1]
    $failure = Read-Host 'Describe what is still wrong'
    $note = Read-Host 'Optional notes (ENTER for none)'
    $result = Invoke-PythonJson @($Tool, 'retest', $ProjectRoot, $RepairPack, 'FAIL', '--category', $category, '--failure-notes', $failure, '--notes', $note)
    Write-Host ('REPAIR RETEST FAIL: {0}' -f $category) -ForegroundColor Red
}
Write-Host $result.next_action -ForegroundColor Yellow
if ($result.next_authoritative_case) {
    Write-Host ('Next authoritative cockpit case: {0} [{1}]' -f $result.next_authoritative_case.label, $result.next_authoritative_case.state) -ForegroundColor Cyan
}
if (-not $NoOpen -and (Test-Path $Dashboard)) { Start-Process $Dashboard }
