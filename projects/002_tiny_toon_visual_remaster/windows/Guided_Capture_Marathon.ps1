param(
    [string]$RomPath,
    [string]$CurrentCapture,
    [string]$PreviousCapture,
    [switch]$NoGitHubPrompt
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Tools = Join-Path $ProjectRoot 'tools'
$Manifest = Join-Path $ProjectRoot 'CAPTURE_MISSIONS.json'
$MarathonTool = Join-Path $Tools 'guided_capture_marathon.py'
$LedgerTool = Join-Path $Tools 'capture_integrity_ledger.py'
$Launcher = Join-Path $PSScriptRoot 'launch_remaster.ps1'
$Bridge = Join-Path $PSScriptRoot 'Local_Capture_Bridge.ps1'
$Reports = Join-Path $ProjectRoot 'Reports\CaptureMarathon'
$Dashboard = Join-Path $Reports 'CAPTURE_MARATHON.html'
$IntegrityDashboard = Join-Path $Reports 'CAPTURE_INTEGRITY.html'

function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) { return @('py', '-3') }
    if (Get-Command python -ErrorAction SilentlyContinue) { return @('python') }
    throw 'Python 3 was not found in PATH.'
}

function Invoke-PythonJson([string[]]$Prefix, [string[]]$Arguments) {
    $exe = $Prefix[0]
    $all = @()
    if ($Prefix.Count -gt 1) { $all += $Prefix[1..($Prefix.Count - 1)] }
    $all += $Arguments
    $raw = & $exe @all
    if ($LASTEXITCODE -ne 0) { throw "Python command failed with exit code $LASTEXITCODE" }
    return (($raw -join "`n") | ConvertFrom-Json)
}

function Invoke-Python([string[]]$Prefix, [string[]]$Arguments) {
    $exe = $Prefix[0]
    $all = @()
    if ($Prefix.Count -gt 1) { $all += $Prefix[1..($Prefix.Count - 1)] }
    $all += $Arguments
    & $exe @all | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "Python command failed with exit code $LASTEXITCODE" }
}

function Select-Folder([string]$Description) {
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = $Description
    if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { return $dialog.SelectedPath }
    return $null
}

function Select-Rom {
    $dialog = New-Object System.Windows.Forms.OpenFileDialog
    $dialog.Title = 'Select Tiny Toon Adventures NES ROM — stays local'
    $dialog.Filter = 'NES ROM (*.nes)|*.nes|All files (*.*)|*.*'
    $dialog.Multiselect = $false
    if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { return $dialog.FileName }
    return $null
}

$Python = Get-PythonCommand
if (-not $CurrentCapture) { $CurrentCapture = Select-Folder 'Select CURRENT MesenCE HD Pack capture folder' }
if (-not $CurrentCapture) { exit 2 }
$CurrentCapture = (Resolve-Path $CurrentCapture).Path
if (-not (Test-Path (Join-Path $CurrentCapture 'hires.txt'))) { throw 'Current capture must contain hires.txt.' }

if (-not $RomPath) { $RomPath = Select-Rom }
if (-not $RomPath) { exit 2 }
$RomPath = (Resolve-Path $RomPath).Path

if (-not $PreviousCapture) {
    $compare = [System.Windows.Forms.MessageBox]::Show(
        'Do you have a previous accepted capture for regression comparison? Recommended: YES when available.',
        'Guided Capture Marathon',
        [System.Windows.Forms.MessageBoxButtons]::YesNo,
        [System.Windows.Forms.MessageBoxIcon]::Question
    )
    if ($compare -eq [System.Windows.Forms.DialogResult]::Yes) {
        $PreviousCapture = Select-Folder 'Select PREVIOUS accepted MesenCE capture'
    }
}
if ($PreviousCapture) { $PreviousCapture = (Resolve-Path $PreviousCapture).Path }

New-Item -ItemType Directory -Force -Path $Reports | Out-Null

Write-Host ''
Write-Host '=== PROJECT #002 — GUIDED CAPTURE MARATHON ===' -ForegroundColor Cyan
Write-Host 'This session can create real Capture Mission Control evidence.' -ForegroundColor Yellow
Write-Host 'A mission is recorded ONLY after you explicitly press V after actually verifying it in-game.'
Write-Host 'The current capture must also pass the integrity admission gate before gameplay begins and before every mission write.'
Write-Host 'Tile growth, heuristics or the script itself never auto-complete a mission.'
Write-Host ''

# Admission preflight happens BEFORE launching the ROM. Incomplete missions are allowed; structural regressions are not.
$Preflight = Invoke-PythonJson $Python @($MarathonTool, 'plan', $Manifest, '--capture', $CurrentCapture)
if ($Preflight.capture_admission_gate -ne 'PASS') {
    & $Python[0] $(if ($Python.Count -gt 1) { $Python[1] }) $LedgerTool $Manifest $CurrentCapture '--output' $IntegrityDashboard '--admission-only' | Out-Host
    Write-Host 'CAPTURE ADMISSION BLOCKED. No new verified mission may be recorded from this capture.' -ForegroundColor Red
    Write-Host ("Structural blockers: {0}" -f ($Preflight.capture_structural_blockers -join ', ')) -ForegroundColor Red
    if (Test-Path $IntegrityDashboard) { Start-Process $IntegrityDashboard }
    exit 3
}
Write-Host ("Capture admission PASS. Fingerprint: {0}" -f $Preflight.capture_fingerprint_sha256) -ForegroundColor Green

# Launch the legally supplied local ROM in verified fullscreen. launch_remaster.ps1 returns after fullscreen is confirmed while MesenCE stays running.
& $Launcher -RomPath $RomPath
$LaunchSucceeded = $?
if (-not $LaunchSucceeded) { throw 'Could not start a verified-fullscreen MesenCE session.' }

$Plan = Invoke-PythonJson $Python @($MarathonTool, 'plan', $Manifest, '--capture', $CurrentCapture)
if ($Plan.release_capture_gate -eq 'PASS') {
    Write-Host 'All Capture Mission Control missions are already complete.' -ForegroundColor Green
} else {
    Write-Host ("Starting with {0}/{1} missions complete ({2}%)." -f $Plan.done, $Plan.total, $Plan.percent) -ForegroundColor Cyan
}

foreach ($Mission in @($Plan.pending)) {
    Clear-Host
    Write-Host '============================================================' -ForegroundColor DarkCyan
    Write-Host ("CAPTURE MISSION [{0}]  priority {1}" -f $Mission.group, $Mission.priority) -ForegroundColor Cyan
    Write-Host $Mission.label -ForegroundColor White
    Write-Host ("Key: {0}" -f $Mission.key) -ForegroundColor DarkGray
    Write-Host '============================================================' -ForegroundColor DarkCyan
    foreach ($Cue in @($Mission.cues)) { Write-Host ("  - {0}" -f $Cue) }
    Write-Host ''
    Write-Host 'Play this mission in the already running fullscreen MesenCE.' -ForegroundColor Yellow
    Write-Host 'When you are done, return here:'
    Write-Host '  V = I actually verified this mission in-game; integrity-check and record evidence'
    Write-Host '  S = skip for now (NO completion recorded)'
    Write-Host '  Q = finish marathon now'

    $Choice = ''
    while ($Choice -notin @('V', 'S', 'Q')) {
        $Choice = (Read-Host 'Choose V / S / Q').Trim().ToUpperInvariant()
    }
    if ($Choice -eq 'Q') { break }
    if ($Choice -eq 'S') {
        Write-Host 'Skipped — no ROADMAP/capture completion recorded.' -ForegroundColor Yellow
        continue
    }

    try {
        $Result = Invoke-PythonJson $Python @(
            $MarathonTool, 'confirm', $Manifest, $CurrentCapture, $Mission.key,
            '--attestation', 'VERIFIED_IN_GAME'
        )
    } catch {
        Write-Host 'Mission was NOT recorded because capture integrity admission failed.' -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        & $Python[0] $(if ($Python.Count -gt 1) { $Python[1] }) $LedgerTool $Manifest $CurrentCapture '--output' $IntegrityDashboard '--admission-only' | Out-Host
        if (Test-Path $IntegrityDashboard) { Start-Process $IntegrityDashboard }
        break
    }
    Write-Host ("RECORDED: {0}. Capture missions now {1}/{2} ({3}%)." -f $Mission.key, $Result.plan.done, $Result.plan.total, $Result.plan.percent) -ForegroundColor Green
    Write-Host ("Integrity admission: {0}; fingerprint: {1}" -f $Result.capture_integrity.admission_gate, $Result.capture_integrity.fingerprint_sha256) -ForegroundColor DarkGreen
    if ($Result.stagnating_warning) {
        Write-Host 'NOTE: this confirmation produced no structural tile/palette/image growth. That can be valid for reused graphics, but review the mission before relying on it.' -ForegroundColor Yellow
    }
}

Invoke-Python $Python @($MarathonTool, 'dashboard', $Manifest, $Dashboard, '--capture', $CurrentCapture)
if (Test-Path $Dashboard) { Start-Process $Dashboard }
$FinalPlan = Invoke-PythonJson $Python @($MarathonTool, 'plan', $Manifest, '--capture', $CurrentCapture)

Write-Host ''
Write-Host ("CAPTURE MARATHON STATUS: {0}/{1} ({2}%) — gate {3}" -f $FinalPlan.done, $FinalPlan.total, $FinalPlan.percent, $FinalPlan.release_capture_gate) -ForegroundColor Cyan
Write-Host ("CAPTURE INTEGRITY ADMISSION: {0}" -f $FinalPlan.capture_admission_gate) -ForegroundColor Cyan
Write-Host 'Generating privacy-safe Local Capture Bridge evidence from this session...' -ForegroundColor Cyan

$BridgeArgs = @('-CurrentCapture', $CurrentCapture)
if ($PreviousCapture) { $BridgeArgs += @('-PreviousCapture', $PreviousCapture) }
if ($NoGitHubPrompt) { $BridgeArgs += '-NoGitHubPrompt' }
& $Bridge @BridgeArgs
$BridgeRc = $LASTEXITCODE
if ($BridgeRc -eq 2) {
    Write-Host 'Safe evidence was generated, but capture regression exists. Do not promote this capture until it is repaired.' -ForegroundColor Yellow
} elseif ($BridgeRc -ne 0) {
    throw "Local Capture Bridge failed with exit code $BridgeRc"
}

Write-Host ''
if ($FinalPlan.release_capture_gate -eq 'PASS' -and $FinalPlan.capture_admission_gate -eq 'PASS' -and $BridgeRc -eq 0) {
    Write-Host 'CAPTURE MARATHON COMPLETE: all explicit capture missions are verified and the safe handoff is clean.' -ForegroundColor Green
    Write-Host 'Next: run regression-safe Capture Promotion Director before any art workspace sync.' -ForegroundColor Green
} else {
    Write-Host 'Marathon session saved. Continue pending missions next time; nothing unverified or structurally regressed was auto-completed.' -ForegroundColor Yellow
}
