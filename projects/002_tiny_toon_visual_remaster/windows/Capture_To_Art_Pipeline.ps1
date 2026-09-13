param(
    [string]$CurrentCapture,
    [string]$PreviousCapture,
    [switch]$CreateSprint
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Tool = Join-Path $ProjectRoot 'tools\capture_production_director.py'
$Report = Join-Path $ProjectRoot 'Reports\CaptureProductionDirector\CAPTURE_PRODUCTION_DIRECTOR.html'

function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) { return @('py', '-3') }
    if (Get-Command python -ErrorAction SilentlyContinue) { return @('python') }
    throw 'Python 3 was not found in PATH.'
}

function Select-Folder([string]$Description) {
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = $Description
    if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { return $dialog.SelectedPath }
    return $null
}

$Python = Get-PythonCommand
if (-not $CurrentCapture) { $CurrentCapture = Select-Folder 'Select CURRENT MesenCE HD Pack capture folder' }
if (-not $CurrentCapture) { exit 2 }
$CurrentCapture = (Resolve-Path $CurrentCapture).Path
if (-not (Test-Path (Join-Path $CurrentCapture 'hires.txt'))) { throw 'Current capture must contain hires.txt.' }

if (-not $PreviousCapture) {
    $answer = [System.Windows.Forms.MessageBox]::Show(
        'Select a previous accepted capture for regression comparison? Recommended when available.',
        'Project #002 Capture → Art Pipeline',
        [System.Windows.Forms.MessageBoxButtons]::YesNo,
        [System.Windows.Forms.MessageBoxIcon]::Question
    )
    if ($answer -eq [System.Windows.Forms.DialogResult]::Yes) {
        $PreviousCapture = Select-Folder 'Select PREVIOUS accepted capture'
    }
}
if ($PreviousCapture) { $PreviousCapture = (Resolve-Path $PreviousCapture).Path }

$args = @($Tool, $ProjectRoot, $CurrentCapture, '--promote-safe')
if ($PreviousCapture) { $args += @('--previous-capture', $PreviousCapture) }
if ($CreateSprint) { $args += '--create-sprint' }

Write-Host ''
Write-Host '=== PROJECT #002 — CAPTURE TO ART PIPELINE ===' -ForegroundColor Cyan
Write-Host 'Running fingerprint-bound acceptance before any production mutation.' -ForegroundColor Yellow
Write-Host 'Unsafe regression/integrity/provenance evidence will stop the pipeline.'
Write-Host 'Pending missions may continue as SAFE_INCREMENTAL_ART but remain Gate A blockers.'
Write-Host ''

$exe = $Python[0]
$all = @()
if ($Python.Count -gt 1) { $all += $Python[1..($Python.Count - 1)] }
$all += $args
& $exe @all | Out-Host
$rc = $LASTEXITCODE

if (Test-Path $Report) { Start-Process $Report }

if ($rc -eq 3) {
    Write-Host ''
    Write-Host 'PIPELINE BLOCKED: fix regression/integrity/provenance before production sync.' -ForegroundColor Red
    exit 3
}
if ($rc -ne 0) { throw "Capture Production Director failed with exit code $rc" }

Write-Host ''
Write-Host 'PIPELINE COMPLETE: capture was safe for the allowed production mode.' -ForegroundColor Green
Write-Host 'Open the dashboard for the exact CAPTURE MORE / SAFE INCREMENTAL ART / READY FOR GATE A REVIEW decision.' -ForegroundColor Green
