param(
    [string]$RomPath,
    [string]$CurrentCapture,
    [string]$PreviousCapture,
    [switch]$NoGitHubPrompt,
    [switch]$ForgetSavedPaths
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Tools = Join-Path $ProjectRoot 'tools'
$Manifest = Join-Path $ProjectRoot 'CAPTURE_MISSIONS.json'
$MarathonTool = Join-Path $Tools 'guided_capture_marathon.py'
$GapTool = Join-Path $Tools 'capture_gap_planner.py'
$SequencerTool = Join-Path $Tools 'route_capture_sequencer.py'
$NextTool = Join-Path $Tools 'next_capture_action.py'
$Launcher = Join-Path $PSScriptRoot 'launch_remaster.ps1'
$Bridge = Join-Path $PSScriptRoot 'Local_Capture_Bridge.ps1'
$Acceptance = Join-Path $PSScriptRoot 'Capture_Coverage_Acceptance.ps1'
$GapReports = Join-Path $ProjectRoot 'Reports\CaptureGapPlanner'
$GapJson = Join-Path $GapReports 'CAPTURE_GAP_PLAN.json'
$RouteReports = Join-Path $ProjectRoot 'Reports\RouteCaptureSequencer'
$RouteJson = Join-Path $RouteReports 'ROUTE_CAPTURE_SESSION_PLAN.json'
$NextReports = Join-Path $ProjectRoot 'Reports\NextCaptureAction'
$NextDashboard = Join-Path $NextReports 'NEXT_CAPTURE_ACTION.html'
$ArtQueue = Join-Path $ProjectRoot 'Artwork\ART_QUEUE.csv'
$StateDir = Join-Path $env:LOCALAPPDATA 'Swir\TinyToonVisualRemaster'
$StatePath = Join-Path $StateDir 'capture-session.json'

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

function Load-LocalState {
    if ($ForgetSavedPaths -and (Test-Path $StatePath)) { Remove-Item -Force $StatePath }
    if (-not (Test-Path $StatePath)) { return $null }
    try { return (Get-Content -Raw -Path $StatePath | ConvertFrom-Json) } catch { return $null }
}

function Save-LocalState([string]$Rom, [string]$Capture, [string]$Previous) {
    New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
    [ordered]@{
        schema = 'swir.project002.local-capture-session.v1'
        rom_path = $Rom
        current_capture = $Capture
        previous_capture = $Previous
        note = 'LOCAL ONLY — never commit this file or its paths.'
    } | ConvertTo-Json | Set-Content -Encoding UTF8 -Path $StatePath
}

function Refresh-GapAndRoute {
    New-Item -ItemType Directory -Force -Path $GapReports | Out-Null
    $gapArgs = @($GapTool, $CurrentCapture, '--capture-manifest', $Manifest, '--output', $GapReports)
    if ($PreviousCapture) { $gapArgs += @('--previous', $PreviousCapture) }
    if (Test-Path $ArtQueue) { $gapArgs += @('--queue', $ArtQueue) }
    Invoke-Python $Python $gapArgs

    New-Item -ItemType Directory -Force -Path $RouteReports | Out-Null
    $routeArgs = @($SequencerTool, $Manifest, '--output', $RouteReports)
    if (Test-Path $GapJson) { $routeArgs += @('--gap-plan', $GapJson) }
    return (Invoke-PythonJson $Python $routeArgs).plan
}

function Show-Session($Session) {
    Write-Host ''
    Write-Host '============================================================' -ForegroundColor DarkCyan
    Write-Host 'ONE HIGHEST-IMPACT GAMEPLAY PASS' -ForegroundColor Cyan
    Write-Host ("Session {0}: {1}" -f $Session.session_index, $Session.label) -ForegroundColor White
    Write-Host ("Mode: {0} | score: {1}" -f $Session.route_mode, $Session.score) -ForegroundColor DarkGray
    Write-Host '============================================================' -ForegroundColor DarkCyan
    foreach ($Instruction in @($Session.instructions)) { Write-Host ("  - {0}" -f $Instruction) }
    foreach ($Gap in @($Session.gap_targets)) {
        $gapTarget = if ($Gap.family) { $Gap.family } else { $Gap.target }
        Write-Host ("  GAP [{0}/{1}] {2}: {3}" -f $Gap.kind, $Gap.art_group, $gapTarget, $Gap.reason) -ForegroundColor Magenta
    }
    foreach ($Mission in @($Session.missions)) {
        Write-Host ("  MISSION [{0}] {1} ({2})" -f $Mission.group, $Mission.label, $Mission.key) -ForegroundColor Yellow
    }
}

$Python = Get-PythonCommand
$Saved = Load-LocalState
if (-not $RomPath -and $Saved -and $Saved.rom_path -and (Test-Path $Saved.rom_path)) { $RomPath = $Saved.rom_path }
if (-not $CurrentCapture -and $Saved -and $Saved.current_capture -and (Test-Path $Saved.current_capture)) { $CurrentCapture = $Saved.current_capture }
if (-not $PreviousCapture -and $Saved -and $Saved.previous_capture -and (Test-Path $Saved.previous_capture)) { $PreviousCapture = $Saved.previous_capture }

if (-not $CurrentCapture) { $CurrentCapture = Select-Folder 'Select CURRENT MesenCE HD Pack capture folder' }
if (-not $CurrentCapture) { exit 2 }
$CurrentCapture = (Resolve-Path $CurrentCapture).Path
if (-not (Test-Path (Join-Path $CurrentCapture 'hires.txt'))) { throw 'Current capture must contain hires.txt.' }

if (-not $RomPath) { $RomPath = Select-Rom }
if (-not $RomPath) { exit 2 }
$RomPath = (Resolve-Path $RomPath).Path
if ($PreviousCapture) { $PreviousCapture = (Resolve-Path $PreviousCapture).Path }
Save-LocalState $RomPath $CurrentCapture $PreviousCapture

Write-Host ''
Write-Host '=== PROJECT #002 — SINGLE BEST CAPTURE SESSION ===' -ForegroundColor Cyan
Write-Host 'Local ROM/capture paths are remembered in LOCALAPPDATA only; no ROM path or capture pixels are committed.' -ForegroundColor DarkGray

$Preflight = Invoke-PythonJson $Python @($MarathonTool, 'plan', $Manifest, '--capture', $CurrentCapture)
if (-not $Preflight.gameplay_launch_allowed) {
    throw ("Capture preflight hard-blocked gameplay: {0}" -f ($Preflight.hard_preflight_blockers -join ', '))
}

$RoutePlan = Refresh-GapAndRoute
if (@($RoutePlan.sessions).Count -eq 0) {
    Write-Host 'No route-aware session remains. Running capture acceptance only.' -ForegroundColor Green
    & $Acceptance -CurrentCapture $CurrentCapture -PreviousCapture $PreviousCapture
    exit $LASTEXITCODE
}
$Session = @($RoutePlan.sessions)[0]
Show-Session $Session

& $Launcher -RomPath $RomPath
if (-not $?) { throw 'Could not start verified-fullscreen MesenCE.' }

if ($Preflight.capture_admission_gate -ne 'PASS') {
    Write-Host ''
    Write-Host 'RECOVERY-ONLY MODE: restore the listed regression/coverage in MesenCE, then return here.' -ForegroundColor Yellow
    [void](Read-Host 'Press ENTER after attempting recovery; no mission evidence will be auto-recorded')
} else {
    [void](Read-Host 'Complete ONLY this grouped gameplay pass, then press ENTER to verify its missions')
    $Plan = Invoke-PythonJson $Python @($MarathonTool, 'plan', $Manifest, '--capture', $CurrentCapture)
    foreach ($MissionRef in @($Session.missions)) {
        $Mission = @($Plan.pending | Where-Object { $_.key -eq $MissionRef.key } | Select-Object -First 1)
        if ($Mission.Count -eq 0) { continue }
        $Mission = $Mission[0]
        Write-Host ''
        Write-Host ("VERIFY [{0}] {1}" -f $Mission.group, $Mission.label) -ForegroundColor Cyan
        foreach ($Cue in @($Mission.cues)) { Write-Host ("  - {0}" -f $Cue) }
        $Choice = ''
        while ($Choice -notin @('V', 'S')) {
            $Choice = (Read-Host 'V = VERIFIED_IN_GAME and record; S = keep pending').Trim().ToUpperInvariant()
        }
        if ($Choice -eq 'S') { continue }
        try {
            $Result = Invoke-PythonJson $Python @(
                $MarathonTool, 'confirm', $Manifest, $CurrentCapture, $Mission.key,
                '--attestation', 'VERIFIED_IN_GAME',
                '--notes', ("Single best-session pass: {0}" -f $Session.session_key)
            )
            Write-Host ("RECORDED {0}: missions {1}/{2} ({3}%)." -f $Mission.key, $Result.plan.done, $Result.plan.total, $Result.plan.percent) -ForegroundColor Green
        } catch {
            Write-Host 'Mission was NOT recorded because live capture integrity failed.' -ForegroundColor Red
            Write-Host $_.Exception.Message -ForegroundColor Red
            break
        }
    }
}

$RoutePlan = Refresh-GapAndRoute
$BridgeArgs = @('-CurrentCapture', $CurrentCapture)
if ($PreviousCapture) { $BridgeArgs += @('-PreviousCapture', $PreviousCapture) }
if ($NoGitHubPrompt) { $BridgeArgs += '-NoGitHubPrompt' }
& $Bridge @BridgeArgs
$BridgeRc = $LASTEXITCODE
if ($BridgeRc -notin @(0,2)) { throw "Local Capture Bridge failed with exit code $BridgeRc" }

& $Acceptance -CurrentCapture $CurrentCapture -PreviousCapture $PreviousCapture
$AcceptanceRc = $LASTEXITCODE

New-Item -ItemType Directory -Force -Path $NextReports | Out-Null
if (Test-Path $RouteJson) {
    Invoke-Python $Python @($NextTool, $RouteJson, '--output', $NextReports)
    if (Test-Path $NextDashboard) { Start-Process $NextDashboard }
}

Write-Host ''
Write-Host ("ONE-PASS LOOP COMPLETE. Remaining route sessions: {0}." -f $RoutePlan.planned_session_count) -ForegroundColor Cyan
Write-Host 'Saved local paths will be reused automatically next run. Use -ForgetSavedPaths to clear them.' -ForegroundColor DarkGray
if ($BridgeRc -eq 2 -or $AcceptanceRc -ne 0) { exit 2 }
exit 0
