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
$GapTool = Join-Path $Tools 'capture_gap_planner.py'
$Launcher = Join-Path $PSScriptRoot 'launch_remaster.ps1'
$Bridge = Join-Path $PSScriptRoot 'Local_Capture_Bridge.ps1'
$Reports = Join-Path $ProjectRoot 'Reports\CaptureMarathon'
$Dashboard = Join-Path $Reports 'CAPTURE_MARATHON.html'
$IntegrityDashboard = Join-Path $Reports 'CAPTURE_INTEGRITY.html'
$GapReports = Join-Path $ProjectRoot 'Reports\CaptureGapPlanner'
$GapJson = Join-Path $GapReports 'CAPTURE_GAP_PLAN.json'
$ArtQueue = Join-Path $ProjectRoot 'Artwork\ART_QUEUE.csv'

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

function Refresh-GapPlan {
    New-Item -ItemType Directory -Force -Path $GapReports | Out-Null
    $args = @($GapTool, $CurrentCapture, '--capture-manifest', $Manifest, '--output', $GapReports)
    if ($PreviousCapture) { $args += @('--previous', $PreviousCapture) }
    if (Test-Path $ArtQueue) { $args += @('--queue', $ArtQueue) }
    Invoke-Python $Python $args
    if (Test-Path $GapJson) {
        return (Get-Content -Raw -Path $GapJson | ConvertFrom-Json)
    }
    return $null
}

function Show-GapFocus($GapPlan, [int]$Limit = 8, [string]$Group = '') {
    if (-not $GapPlan) { return }
    $rows = @($GapPlan.queue)
    if ($Group) {
        $matched = @($rows | Where-Object { $_.art_group -eq $Group -or ($_.kind -eq 'MISSION' -and $_.art_group -eq 'GAMEPLAY') })
        if ($matched.Count -gt 0) { $rows = $matched }
    }
    $top = @($rows | Select-Object -First $Limit)
    if ($top.Count -eq 0) { return }
    Write-Host ''
    Write-Host 'SMART CAPTURE FOCUS:' -ForegroundColor Magenta
    foreach ($row in $top) {
        $family = if ($row.family) { " / $($row.family)" } else { '' }
        Write-Host ("  [{0}] {1}/{2}{3}: {4} — {5}" -f $row.score, $row.kind, $row.art_group, $family, $row.target, $row.reason)
    }
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
Write-Host '=== PROJECT #002 — SMART GUIDED CAPTURE MARATHON ===' -ForegroundColor Cyan
Write-Host 'This session can create real Capture Mission Control evidence and can recover a regressed local capture.' -ForegroundColor Yellow
Write-Host 'A mission is recorded ONLY after explicit VERIFIED_IN_GAME confirmation and integrity admission PASS.'
Write-Host 'Recoverable historical regression may launch gameplay, but evidence recording remains locked until coverage is restored.'
Write-Host 'Tile growth, heuristics or the script itself never auto-complete a mission.'
Write-Host ''

$Preflight = Invoke-PythonJson $Python @($MarathonTool, 'plan', $Manifest, '--capture', $CurrentCapture)
if (-not $Preflight.gameplay_launch_allowed) {
    $exe = $Python[0]
    $ledgerArgs = @()
    if ($Python.Count -gt 1) { $ledgerArgs += $Python[1..($Python.Count - 1)] }
    $ledgerArgs += @($LedgerTool, $Manifest, $CurrentCapture, '--output', $IntegrityDashboard, '--admission-only')
    & $exe @ledgerArgs | Out-Host
    Write-Host 'HARD CAPTURE PREFLIGHT BLOCK. Gameplay recovery cannot safely start.' -ForegroundColor Red
    Write-Host ("Hard blockers: {0}" -f ($Preflight.hard_preflight_blockers -join ', ')) -ForegroundColor Red
    if (Test-Path $IntegrityDashboard) { Start-Process $IntegrityDashboard }
    exit 3
}

$GapPlan = Refresh-GapPlan
Show-GapFocus $GapPlan 10

if ($Preflight.recovery_mode -eq 'GAMEPLAY_RECOVERY_REQUIRED') {
    Write-Host ''
    Write-Host 'RECOVERY MODE REQUIRED.' -ForegroundColor Yellow
    Write-Host 'MesenCE will start so missing historical capture coverage can be restored.' -ForegroundColor Yellow
    Write-Host 'No VERIFIED_IN_GAME mission can be recorded while admission is BLOCKED.' -ForegroundColor Yellow
    foreach ($target in @($Preflight.recovery_targets)) {
        Write-Host ("  - {0}" -f $target.action) -ForegroundColor DarkYellow
    }
} else {
    Write-Host ("Capture admission PASS. Fingerprint: {0}" -f $Preflight.capture_fingerprint_sha256) -ForegroundColor Green
}

& $Launcher -RomPath $RomPath
$LaunchSucceeded = $?
if (-not $LaunchSucceeded) { throw 'Could not start a verified-fullscreen MesenCE session.' }

# A regression against verified history is recoverable only through real gameplay. Keep checking the live capture
# until structural admission is clean; wrong scale/missing images were already rejected before launch.
while ($Preflight.recovery_mode -eq 'GAMEPLAY_RECOVERY_REQUIRED') {
    Clear-Host
    Write-Host '============================================================' -ForegroundColor DarkYellow
    Write-Host 'CAPTURE RECOVERY MODE — restore verified historical coverage' -ForegroundColor Yellow
    Write-Host '============================================================' -ForegroundColor DarkYellow
    foreach ($target in @($Preflight.recovery_targets)) {
        Write-Host ("  - {0}" -f $target.action)
    }
    $GapPlan = Refresh-GapPlan
    Show-GapFocus $GapPlan 12
    Write-Host ''
    Write-Host 'Replay the indicated routes/states in the already running fullscreen MesenCE.' -ForegroundColor Yellow
    Write-Host 'R = recheck the live capture after attempting recovery'
    Write-Host 'Q = finish without recording new mission evidence'
    $choice = ''
    while ($choice -notin @('R', 'Q')) {
        $choice = (Read-Host 'Choose R / Q').Trim().ToUpperInvariant()
    }
    if ($choice -eq 'Q') { break }
    $Preflight = Invoke-PythonJson $Python @($MarathonTool, 'plan', $Manifest, '--capture', $CurrentCapture)
    if (-not $Preflight.gameplay_launch_allowed) {
        Write-Host 'Recovery produced a hard structural blocker. Stop and repair the capture files/settings.' -ForegroundColor Red
        break
    }
    if ($Preflight.capture_admission_gate -eq 'PASS') {
        Write-Host 'RECOVERY SUCCESS: structural admission is PASS. Mission evidence recording is unlocked.' -ForegroundColor Green
        break
    }
}

$Plan = Invoke-PythonJson $Python @($MarathonTool, 'plan', $Manifest, '--capture', $CurrentCapture)
if ($Plan.capture_admission_gate -ne 'PASS') {
    Invoke-Python $Python @($MarathonTool, 'dashboard', $Manifest, $Dashboard, '--capture', $CurrentCapture)
    if (Test-Path $Dashboard) { Start-Process $Dashboard }
    Write-Host 'Session ended in recovery mode. No untrusted mission evidence was recorded.' -ForegroundColor Yellow
} else {
    if ($Plan.release_capture_gate -eq 'PASS') {
        Write-Host 'All Capture Mission Control missions are already complete.' -ForegroundColor Green
    } else {
        Write-Host ("Starting with {0}/{1} missions complete ({2}%)." -f $Plan.done, $Plan.total, $Plan.percent) -ForegroundColor Cyan
    }

    foreach ($Mission in @($Plan.pending)) {
        Clear-Host
        $GapPlan = Refresh-GapPlan
        Write-Host '============================================================' -ForegroundColor DarkCyan
        Write-Host ("CAPTURE MISSION [{0}]  priority {1}" -f $Mission.group, $Mission.priority) -ForegroundColor Cyan
        Write-Host $Mission.label -ForegroundColor White
        Write-Host ("Key: {0}" -f $Mission.key) -ForegroundColor DarkGray
        Write-Host '============================================================' -ForegroundColor DarkCyan
        foreach ($Cue in @($Mission.cues)) { Write-Host ("  - {0}" -f $Cue) }
        Show-GapFocus $GapPlan 6 $Mission.group
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
            Write-Host 'Mission was NOT recorded because live capture integrity is not admissible.' -ForegroundColor Red
            Write-Host $_.Exception.Message -ForegroundColor Red
            Write-Host 'Return to gameplay and restore the missing capture coverage before attempting further attestations.' -ForegroundColor Yellow
            break
        }
        Write-Host ("RECORDED: {0}. Capture missions now {1}/{2} ({3}%)." -f $Mission.key, $Result.plan.done, $Result.plan.total, $Result.plan.percent) -ForegroundColor Green
        Write-Host ("Integrity admission: {0}; fingerprint: {1}" -f $Result.capture_integrity.admission_gate, $Result.capture_integrity.fingerprint_sha256) -ForegroundColor DarkGreen
        if ($Result.stagnating_warning) {
            Write-Host 'NOTE: this confirmation produced no structural tile/palette/image growth. That can be valid for reused graphics, but review the mission before relying on it.' -ForegroundColor Yellow
        }
    }
}

Invoke-Python $Python @($MarathonTool, 'dashboard', $Manifest, $Dashboard, '--capture', $CurrentCapture)
if (Test-Path $Dashboard) { Start-Process $Dashboard }
$FinalPlan = Invoke-PythonJson $Python @($MarathonTool, 'plan', $Manifest, '--capture', $CurrentCapture)

Write-Host ''
Write-Host ("CAPTURE MARATHON STATUS: {0}/{1} ({2}%) — gate {3}" -f $FinalPlan.done, $FinalPlan.total, $FinalPlan.percent, $FinalPlan.release_capture_gate) -ForegroundColor Cyan
Write-Host ("CAPTURE INTEGRITY ADMISSION: {0}; recovery mode: {1}" -f $FinalPlan.capture_admission_gate, $FinalPlan.recovery_mode) -ForegroundColor Cyan
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
    Write-Host 'Marathon session saved. Continue pending/recovery work next time; nothing unverified or structurally regressed was auto-completed.' -ForegroundColor Yellow
}