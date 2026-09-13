param(
    [string]$RomPath,
    [string]$CurrentCapture,
    [string]$PreviousCapture,
    [int]$BatchSize = 30,
    [switch]$SkipGameplay
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$FullPipeline = Join-Path $PSScriptRoot 'Full_Capture_To_HD_Production.ps1'
$Autopilot = Join-Path $ProjectRoot 'tools\hd_art_autopilot.py'
$AutopilotHtml = Join-Path $ProjectRoot 'Reports\HDArtAutopilot\HD_ART_AUTOPILOT.html'

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

if (-not $CurrentCapture) { $CurrentCapture = Select-Folder 'Select CURRENT MesenCE HD Pack capture folder' }
if (-not $CurrentCapture) { exit 2 }
$CurrentCapture = (Resolve-Path $CurrentCapture).Path
if (-not (Test-Path (Join-Path $CurrentCapture 'hires.txt'))) { throw 'Current capture must contain hires.txt.' }

Write-Host ''
Write-Host '=== PROJECT #002 - FULL CAPTURE -> EXACT HD ART AUTOPILOT ===' -ForegroundColor Cyan
Write-Host 'Stage 1: guided gameplay/safe bridge/fingerprint acceptance/guarded promotion.' -ForegroundColor Yellow
Write-Host 'Stage 2: Visual Completion Matrix -> exact High-Impact Art Sprint.' -ForegroundColor Yellow
Write-Host 'Existing CurrentImpactSprint is never overwritten automatically.'
Write-Host 'No ROADMAP Gate A-D checkbox is changed by this workflow.'
Write-Host ''

$pipelineArgs = @('-CurrentCapture', $CurrentCapture)
if ($RomPath) { $pipelineArgs += @('-RomPath', $RomPath) }
if ($PreviousCapture) { $pipelineArgs += @('-PreviousCapture', $PreviousCapture) }
if ($SkipGameplay) { $pipelineArgs += '-SkipGameplay' }

& $FullPipeline @pipelineArgs
$pipelineRc = $LASTEXITCODE
if ($pipelineRc -eq 3) {
    Write-Host 'AUTOPILOT STOPPED: capture production is blocked; no art sprint will be prepared.' -ForegroundColor Red
    exit 3
}
if ($pipelineRc -ne 0) { throw "Full Capture -> HD Production failed with exit code $pipelineRc" }

$Python = Get-PythonCommand
$exe = $Python[0]
$args = @()
if ($Python.Count -gt 1) { $args += $Python[1..($Python.Count - 1)] }
$args += @($Autopilot, $ProjectRoot, $CurrentCapture, '--batch-size', [string]([Math]::Max(1, $BatchSize)))

Write-Host ''
Write-Host 'Safe promotion complete. Building exact captured-art completion matrix...' -ForegroundColor Cyan
& $exe @args | Out-Host
$autoRc = $LASTEXITCODE

if (Test-Path $AutopilotHtml) { Start-Process $AutopilotHtml }
if ($autoRc -eq 3) {
    Write-Host 'HD ART AUTOPILOT BLOCKED: production decision/fingerprint is stale or unsafe.' -ForegroundColor Red
    exit 3
}
if ($autoRc -ne 0) { throw "HD Art Autopilot failed with exit code $autoRc" }

Write-Host ''
Write-Host 'AUTOPILOT COMPLETE: safe capture work is now routed to the exact highest-impact captured-art batch.' -ForegroundColor Green
Write-Host 'If a sprint already existed, it was preserved and must be finished before replacement.' -ForegroundColor Green
exit 0
