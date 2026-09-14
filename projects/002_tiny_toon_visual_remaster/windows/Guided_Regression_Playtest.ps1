param(
    [string]$ProjectRoot,
    [string]$RuntimePack,
    [string]$RomPath,
    [switch]$RunAll,
    [switch]$NoOpen
)

$ErrorActionPreference = 'Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $ProjectRoot) { $ProjectRoot = Split-Path -Parent $Here }
$Tool = Join-Path $ProjectRoot 'tools\guided_regression_playtest.py'
$Launcher = Join-Path $Here 'launch_remaster.ps1'
$Manifest = Join-Path $ProjectRoot 'FINAL_REGRESSION.json'
$Output = Join-Path $ProjectRoot 'Reports\GuidedRegressionPlaytest'
$PlanJson = Join-Path $Output 'GUIDED_REGRESSION_PLAYTEST.json'
$Dashboard = Join-Path $Output 'GUIDED_REGRESSION_PLAYTEST.html'
$StatePath = Join-Path $env:LOCALAPPDATA 'Swir\TinyToonVisualRemaster\capture-session.json'
$FullscreenEvidence = Join-Path $ProjectRoot 'Reports\FullscreenPlaytest\FULLSCREEN_PLAYTEST.json'

function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) { return @('py','-3') }
    if (Get-Command python -ErrorAction SilentlyContinue) { return @('python') }
    throw 'Python 3 was not found in PATH.'
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
    $candidate = Join-Path $ProjectRoot 'Build\HighImpactCandidate'
    $playtest = Join-Path $ProjectRoot 'ModernizedPack\playtest_current'
    if (Test-Path (Join-Path $candidate 'hires.txt')) { $RuntimePack = $candidate }
    elseif (Test-Path (Join-Path $playtest 'hires.txt')) { $RuntimePack = $playtest }
    else { $RuntimePack = Pick-Folder 'Select exact runtime HD pack for final regression' }
}
if (-not $RuntimePack) { exit 2 }
$RuntimePack = (Resolve-Path $RuntimePack).Path
if (-not (Test-Path (Join-Path $RuntimePack 'hires.txt'))) { throw 'Runtime pack must contain hires.txt.' }

if (-not $RomPath -and (Test-Path $StatePath)) {
    try {
        $state = Get-Content -Raw $StatePath | ConvertFrom-Json
        if ($state.rom_path -and (Test-Path $state.rom_path)) { $RomPath = $state.rom_path }
    } catch {}
}
if (-not $RomPath) { $RomPath = Pick-Rom }
if (-not $RomPath) { exit 2 }
$RomPath = (Resolve-Path $RomPath).Path

New-Item -ItemType Directory -Force -Path $Output | Out-Null
Write-Host ''
Write-Host '=== PROJECT #002 — GUIDED EXACT-BUILD REGRESSION PLAYTEST ===' -ForegroundColor Cyan
Write-Host 'Every PASS/FAIL is manual evidence from the exact current runtime fingerprint.' -ForegroundColor Yellow
Write-Host 'No case can auto-PASS. FAIL is routed before any pending/stale case.'

while ($true) {
    $plan = Invoke-PythonJson @($Tool, 'plan', $Manifest, $RuntimePack, '--output', $Output)
    $session = $plan.session
    if ($session.state -eq 'REGRESSION_COMPLETE') {
        Write-Host ''
        Write-Host 'FINAL REGRESSION: 10/10 PASS for this exact build.' -ForegroundColor Green
        Write-Host 'DO THIS NEXT: Final Release Gate.' -ForegroundColor Green
        break
    }

    $case = $session.next_case
    Write-Host ''
    Write-Host ('CASE {0}/10 — {1}' -f $case.order, $case.label) -ForegroundColor Cyan
    Write-Host ('Key: {0} | prior state: {1}' -f $case.key, $case.prior_state) -ForegroundColor DarkGray
    if ($case.prior_state -eq 'FAIL') {
        Write-Host ('Existing defect: {0} — {1}' -f $case.failure_category, $case.failure_notes) -ForegroundColor Red
        Write-Host $session.next_action -ForegroundColor Yellow
        Write-Host 'Repair/rebuild first. The guided runner will not overwrite a known FAIL with an unverified result.' -ForegroundColor Yellow
        if (-not $NoOpen -and (Test-Path $Dashboard)) { Start-Process $Dashboard }
        break
    }
    Write-Host ('ROUTE: {0}' -f $case.route) -ForegroundColor White
    foreach ($cue in @($case.cues)) { Write-Host ('  - {0}' -f $cue) }
    Write-Host ''
    Write-Host 'Launching this exact build through verified-fullscreen MesenCE...' -ForegroundColor Yellow
    & $Launcher -RomPath $RomPath -PackDir $RuntimePack -EvidencePath $FullscreenEvidence
    if ($LASTEXITCODE -ne 0) { throw 'Verified fullscreen MesenCE launch failed; regression evidence was not recorded.' }

    [void](Read-Host 'Perform ONLY the case above in MesenCE. Return here and press ENTER when observation is complete')
    $choice = ''
    while ($choice -notin @('P','F')) {
        $choice = (Read-Host 'P = PASS after real visual verification; F = FAIL and classify defect').Trim().ToUpperInvariant()
    }
    if ($choice -eq 'P') {
        $note = Read-Host 'Optional PASS notes (ENTER for none)'
        $record = Invoke-PythonJson @($Tool, 'record', $Manifest, $RuntimePack, $case.key, 'PASS', '--notes', $note, '--output', $Output)
        Write-Host ('RECORDED PASS: {0}' -f $case.key) -ForegroundColor Green
    } else {
        $categories = @('MISSING_HD','WRONG_PALETTE','ANIMATION_SEAM','TRANSPARENCY','MAPPING','SCALE_OR_FILTER','CAPTURE_GAP','OTHER')
        Write-Host 'Failure categories:' -ForegroundColor Red
        for ($i=0; $i -lt $categories.Count; $i++) { Write-Host ('  {0}. {1}' -f ($i+1), $categories[$i]) }
        $number = 0
        while ($number -lt 1 -or $number -gt $categories.Count) {
            [void][int]::TryParse((Read-Host 'Choose failure category number'), [ref]$number)
        }
        $category = $categories[$number-1]
        $failure = Read-Host 'Describe the visible defect / exact location or state'
        $notes = Read-Host 'Optional additional notes (ENTER for none)'
        $record = Invoke-PythonJson @($Tool, 'record', $Manifest, $RuntimePack, $case.key, 'FAIL', '--category', $category, '--failure-notes', $failure, '--notes', $notes, '--output', $Output)
        Write-Host ('RECORDED FAIL: {0} / {1}' -f $case.key, $category) -ForegroundColor Red
        Write-Host $record.session.next_action -ForegroundColor Yellow
        break
    }

    if (-not $RunAll) {
        Write-Host ('Next case prepared: {0}' -f $record.session.next_case.label) -ForegroundColor Cyan
        break
    }
}

if (-not $NoOpen -and (Test-Path $Dashboard)) { Start-Process $Dashboard }
