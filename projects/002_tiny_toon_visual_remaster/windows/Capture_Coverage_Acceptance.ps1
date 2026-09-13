param(
    [string]$ProjectRoot,
    [string]$Capture,
    [string]$PreviousCapture,
    [string]$Output
)

$ErrorActionPreference = 'Stop'
$ProjectDir = Split-Path -Parent $PSScriptRoot
$Tool = Join-Path $ProjectDir 'tools\capture_coverage_acceptance.py'

function Select-Folder([string]$Description) {
    Add-Type -AssemblyName System.Windows.Forms
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = $Description
    $dialog.ShowNewFolderButton = $true
    if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
        return $dialog.SelectedPath
    }
    return $null
}

if (-not $ProjectRoot) {
    $ProjectRoot = Select-Folder 'Select the local Project #002 workspace containing CAPTURE_MISSIONS.json (or where it should be created)'
}
if (-not $ProjectRoot) { Write-Host 'Cancelled.'; exit 1 }

if (-not $Capture) {
    $Capture = Select-Folder 'Select the current MesenCE HD Pack capture folder containing hires.txt'
}
if (-not $Capture) { Write-Host 'Cancelled.'; exit 1 }

if (-not (Test-Path (Join-Path $Capture 'hires.txt'))) {
    Write-Error 'Selected capture does not contain hires.txt.'
    exit 1
}

if (-not $Output) {
    $Output = Join-Path $ProjectRoot 'Reports\CaptureCoverageAcceptance'
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Error 'Python was not found in PATH.'
    exit 1
}

$argsList = @($Tool, $ProjectRoot, $Capture, '--output', $Output)
if ($PreviousCapture) {
    $argsList += @('--previous-capture', $PreviousCapture)
}

Write-Host ''
Write-Host 'Project #002 - Capture Coverage Acceptance' -ForegroundColor Cyan
Write-Host 'This produces metadata-only evidence. It never uploads ROM/capture pixels and never edits ROADMAP checkboxes.'
Write-Host ''

& $python.Source @argsList
$exitCode = $LASTEXITCODE
$dashboard = Join-Path $Output 'CAPTURE_COVERAGE_ACCEPTANCE.html'
if (Test-Path $dashboard) {
    Start-Process $dashboard
}

if ($exitCode -eq 0) {
    Write-Host 'Hard metadata/provenance checks are clean. Manual Gate A gameplay review is still required.' -ForegroundColor Green
} elseif ($exitCode -eq 2) {
    Write-Host 'Capture acceptance remains BLOCKED. Follow DO THIS NEXT in the dashboard.' -ForegroundColor Yellow
} else {
    Write-Host "Capture coverage acceptance failed with exit code $exitCode." -ForegroundColor Red
}
exit $exitCode
