param(
    [string]$ProjectRoot,
    [string]$CurrentCapture,
    [string]$ReviewJson,
    [string]$PreviousCapture,
    [int]$BatchSize = 30,
    [switch]$RequireFullGateA,
    [switch]$SkipReview,
    [switch]$NoOpen
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms

$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$DefaultProject = Split-Path -Parent $Here
if (-not $ProjectRoot) { $ProjectRoot = $DefaultProject }
$ProjectRoot = (Resolve-Path $ProjectRoot).Path

$Tool = Join-Path $ProjectRoot 'tools\evidence_bound_art_handoff.py'
$ReviewDirector = Join-Path $Here 'Capture_Review_Director.ps1'
$OutputDir = Join-Path $ProjectRoot 'Reports\EvidenceBoundArtHandoff'
$ReportJson = Join-Path $OutputDir 'EVIDENCE_BOUND_ART_HANDOFF.json'
$ReportHtml = Join-Path $OutputDir 'EVIDENCE_BOUND_ART_HANDOFF.html'
$StatePath = Join-Path $env:LOCALAPPDATA 'Swir\TinyToonVisualRemaster\capture-session.json'
$Kit = Join-Path $ProjectRoot 'Artwork\CurrentImpactSprint'

function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) { return @('py', '-3') }
    if (Get-Command python -ErrorAction SilentlyContinue) { return @('python') }
    throw 'Python 3 was not found in PATH.'
}

function Pick-Folder([string]$Title) {
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = $Title
    if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { return $dialog.SelectedPath }
    return $null
}

function Load-LocalCaptureState {
    if (-not (Test-Path $StatePath)) { return $null }
    try { return (Get-Content -Raw -Path $StatePath | ConvertFrom-Json) } catch { return $null }
}

function Resolve-SafeKitPath([string]$RelativePath) {
    if (-not $RelativePath) { return $null }
    $candidate = [System.IO.Path]::GetFullPath((Join-Path $Kit $RelativePath))
    $kitRoot = [System.IO.Path]::GetFullPath($Kit)
    if (-not $candidate.StartsWith($kitRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'Refusing unsafe active-family path outside CurrentImpactSprint.'
    }
    return $candidate
}

$Saved = Load-LocalCaptureState
if (-not $CurrentCapture -and $Saved -and $Saved.current_capture -and (Test-Path $Saved.current_capture)) {
    $CurrentCapture = $Saved.current_capture
}
if (-not $PreviousCapture -and $Saved -and $Saved.previous_capture -and (Test-Path $Saved.previous_capture)) {
    $PreviousCapture = $Saved.previous_capture
}
if (-not $CurrentCapture) {
    $CurrentCapture = Pick-Folder 'Select the exact current MesenCE capture / HD pack'
}
if (-not $CurrentCapture) { exit 2 }
$CurrentCapture = (Resolve-Path $CurrentCapture).Path
if (-not (Test-Path (Join-Path $CurrentCapture 'hires.txt'))) {
    throw 'Current capture must contain hires.txt.'
}
if ($PreviousCapture) { $PreviousCapture = (Resolve-Path $PreviousCapture).Path }

if (-not $SkipReview) {
    Write-Host 'Refreshing current Gate A review against the latest local evidence...' -ForegroundColor Cyan
    $reviewArgs = @{
        CurrentCapture = $CurrentCapture
        SkipCapture = $true
        NoOpen = $true
    }
    if ($PreviousCapture) { $reviewArgs['PreviousCapture'] = $PreviousCapture }
    & $ReviewDirector @reviewArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'Capture Review Director did not complete cleanly; the handoff will validate existing evidence and fail closed if stale.' -ForegroundColor Yellow
    }
}

if (-not $ReviewJson) {
    $ReviewJson = Join-Path $ProjectRoot 'Reports\CaptureReviewDirector\CAPTURE_REVIEW_DIRECTOR.json'
}
if (-not (Test-Path $ReviewJson)) {
    throw 'CAPTURE_REVIEW_DIRECTOR.json is missing. Run the real capture/review workflow first.'
}
$ReviewJson = (Resolve-Path $ReviewJson).Path

$Python = Get-PythonCommand
$exe = $Python[0]
$argsList = @()
if ($Python.Count -gt 1) { $argsList += $Python[1..($Python.Count - 1)] }
$argsList += @($Tool, $ProjectRoot, $CurrentCapture, $ReviewJson, '--batch-size', [string]([Math]::Max(1, $BatchSize)))
if ($PreviousCapture) { $argsList += @('--previous-capture', $PreviousCapture) }
if ($RequireFullGateA) { $argsList += '--require-full-gate-a' }

Write-Host ''
Write-Host '=== PROJECT #002 — EVIDENCE-BOUND CAPTURE REVIEW → HD ART HANDOFF v2 ===' -ForegroundColor Cyan
Write-Host 'Ledger-backed VERIFIED_GATE_A + exact capture fingerprint → Production Director → HD Art Autopilot → active family workbench.' -ForegroundColor Yellow
Write-Host 'Safe incomplete capture may remain incremental; ROADMAP is never changed automatically.' -ForegroundColor DarkGray

& $exe @argsList | Out-Host
$code = $LASTEXITCODE

if (Test-Path $ReportJson) {
    $state = Get-Content $ReportJson -Raw | ConvertFrom-Json
    if ($state.active_family) {
        Write-Host ''
        Write-Host ("ACTIVE FAMILY WORKBENCH: {0}" -f $state.active_family.family) -ForegroundColor Green
        Write-Host ("DO THIS NEXT: {0}" -f $state.next_action) -ForegroundColor Cyan
        $activeState = Join-Path $Kit 'ACTIVE_FAMILY_WORKBENCH.json'
        if (-not (Test-Path $activeState)) {
            Write-Host 'ACTIVE_FAMILY_WORKBENCH metadata is missing; continue from the handoff dashboard.' -ForegroundColor Yellow
        }
        if (-not $NoOpen) {
            $board = Resolve-SafeKitPath $state.active_family.board
            $editable = Resolve-SafeKitPath $state.active_family.editable_dir
            if ($board -and (Test-Path $board)) { Start-Process $board }
            if ($editable -and (Test-Path $editable)) { Start-Process $editable }
        }
    }
}

if (-not $NoOpen -and (Test-Path $ReportHtml)) {
    Start-Process $ReportHtml
}

if ($code -ne 0) {
    Write-Host "Handoff BLOCKED (exit $code). Existing production state remains protected by the underlying gates." -ForegroundColor Red
    exit $code
}

Write-Host 'ART HANDOFF READY. Finish the active family through transactional QA, then verified-fullscreen MesenCE playtest.' -ForegroundColor Green
exit 0
