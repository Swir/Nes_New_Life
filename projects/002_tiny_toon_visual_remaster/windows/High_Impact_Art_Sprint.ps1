param(
  [string]$Pack,
  [string]$Queue,
  [string]$Workspace,
  [string]$Kit,
  [string]$OutputPack,
  [int]$BatchSize = 30,
  [switch]$Finish,
  [switch]$Overwrite
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Tool = Join-Path $ProjectRoot 'tools\high_impact_art_sprint.py'
$Reports = Join-Path $ProjectRoot 'Reports\VisualCompletion'
if (-not $Kit) { $Kit = Join-Path $ProjectRoot 'Artwork\CurrentImpactSprint' }

function Pick-Folder([string]$Description) {
  Add-Type -AssemblyName System.Windows.Forms
  $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
  $dialog.Description = $Description
  $dialog.ShowNewFolderButton = $false
  if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { throw 'Cancelled.' }
  return $dialog.SelectedPath
}

function Pick-File([string]$Title, [string]$Filter) {
  Add-Type -AssemblyName System.Windows.Forms
  $dialog = New-Object System.Windows.Forms.OpenFileDialog
  $dialog.Title = $Title
  $dialog.Filter = $Filter
  if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { throw 'Cancelled.' }
  return $dialog.FileName
}

if (-not $Pack) { $Pack = Pick-Folder 'Select current Project #002 HD pack/capture folder containing hires.txt' }
if (-not (Test-Path (Join-Path $Pack 'hires.txt'))) { throw 'Selected folder does not contain hires.txt.' }
if (-not $Workspace) {
  $defaultWorkspace = Join-Path $ProjectRoot 'Artwork\MasterWorkspace'
  if (Test-Path $defaultWorkspace) { $Workspace = $defaultWorkspace } else { $Workspace = Pick-Folder 'Select MasterWorkspace folder' }
}

if ($Finish) {
  if (-not (Test-Path (Join-Path $Kit 'ART_SPRINT_KIT.json'))) { throw "Sprint manifest missing: $Kit" }
  if (-not $OutputPack) { $OutputPack = Join-Path $ProjectRoot 'Build\HighImpactCandidate' }
  $args = @($Tool, 'finish', $Pack, $Workspace, $Kit, $OutputPack)
  if ($Overwrite) { $args += '--overwrite' }
  & python @args
  if ($LASTEXITCODE -ne 0) { throw "High-impact sprint finish failed with exit code $LASTEXITCODE" }
  Write-Host "Candidate HD pack + Pixel QA complete: $OutputPack" -ForegroundColor Green
  exit 0
}

if (-not $Queue) {
  $defaultQueue = Join-Path $ProjectRoot 'Artwork\ART_QUEUE.csv'
  if (Test-Path $defaultQueue) { $Queue = $defaultQueue } else { $Queue = Pick-File 'Select ART_QUEUE.csv' 'CSV files (*.csv)|*.csv' }
}

$args = @($Tool, 'prepare', $Pack, $Workspace, $Kit, $Reports, '--queue', $Queue, '--batch-size', $BatchSize)
if ($Overwrite) { $args += '--overwrite' }
& python @args
if ($LASTEXITCODE -ne 0) { throw "High-impact sprint prepare failed with exit code $LASTEXITCODE" }

$Dashboard = Join-Path $Reports 'VISUAL_COMPLETION_MATRIX.html'
$Board = Join-Path $Kit 'LOCAL_ART_SPRINT_BOARD.png'
Write-Host "High-impact art sprint ready: $Kit" -ForegroundColor Green
Write-Host "Visual completion dashboard: $Dashboard" -ForegroundColor Cyan
Write-Host "Edit only PNG files in: $(Join-Path $Kit 'editable')" -ForegroundColor Yellow
if (Test-Path $Dashboard) { Start-Process $Dashboard }
if (Test-Path $Board) { Start-Process $Board }
if (Test-Path (Join-Path $Kit 'editable')) { Start-Process explorer.exe (Join-Path $Kit 'editable') }
