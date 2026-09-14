param(
    [string]$ProjectRoot,
    [string]$CurrentCapture,
    [string]$ReviewJson,
    [string]$PreviousCapture,
    [int]$BatchSize = 30,
    [switch]$OverwriteSprint
)
$ErrorActionPreference = 'Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$DefaultProject = Split-Path -Parent $Here
$Tool = Join-Path $DefaultProject 'tools\evidence_bound_art_handoff.py'

function Pick-Folder([string]$Title) {
    Add-Type -AssemblyName System.Windows.Forms
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = $Title
    if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { return $dialog.SelectedPath }
    return $null
}
function Pick-Json([string]$Title) {
    Add-Type -AssemblyName System.Windows.Forms
    $dialog = New-Object System.Windows.Forms.OpenFileDialog
    $dialog.Title = $Title
    $dialog.Filter = 'JSON files (*.json)|*.json|All files (*.*)|*.*'
    if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { return $dialog.FileName }
    return $null
}

if (-not $ProjectRoot) { $ProjectRoot = Pick-Folder 'Select local Project #002 workspace' }
if (-not $ProjectRoot) { exit 1 }
if (-not $CurrentCapture) { $CurrentCapture = Pick-Folder 'Select the exact current MesenCE capture / HD pack' }
if (-not $CurrentCapture) { exit 1 }
if (-not $ReviewJson) {
    $candidate = Join-Path $ProjectRoot 'Reports\CaptureReviewDirector\CAPTURE_REVIEW_DIRECTOR.json'
    if (Test-Path $candidate) { $ReviewJson = $candidate } else { $ReviewJson = Pick-Json 'Select CAPTURE_REVIEW_DIRECTOR.json for this capture' }
}
if (-not $ReviewJson) { exit 1 }

$argsList = @($Tool, $ProjectRoot, $CurrentCapture, $ReviewJson, '--batch-size', [string]([Math]::Max(1,$BatchSize)))
if ($PreviousCapture) { $argsList += @('--previous-capture', $PreviousCapture) }
if ($OverwriteSprint) { $argsList += '--overwrite-sprint' }

Write-Host 'Evidence-bound HD art handoff' -ForegroundColor Cyan
Write-Host 'The review fingerprint must match the exact current capture. Unsafe regression/provenance evidence blocks before art mutation.'
& python @argsList
$code = $LASTEXITCODE
if ($code -ne 0) {
    Write-Host "Handoff BLOCKED (exit $code). Existing art sprint/workspace remains protected by the underlying gates." -ForegroundColor Red
    exit $code
}
$dashboard = Join-Path $ProjectRoot 'Reports\EvidenceBoundArtHandoff\EVIDENCE_BOUND_ART_HANDOFF.html'
if (Test-Path $dashboard) { Start-Process $dashboard }
$kit = Join-Path $ProjectRoot 'Artwork\CurrentImpactSprint'
if (Test-Path $kit) { Start-Process explorer.exe $kit }
Write-Host 'ART HANDOFF READY. Edit only CurrentImpactSprint\editable, then finish through transactional Pixel QA.' -ForegroundColor Green
