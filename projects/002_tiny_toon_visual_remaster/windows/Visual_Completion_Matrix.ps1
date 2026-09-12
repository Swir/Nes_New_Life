param(
  [string]$Pack,
  [string]$Queue,
  [string]$Workspace,
  [int]$BatchSize = 40
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Tool = Join-Path $ProjectRoot 'tools\visual_completion_matrix.py'
$Output = Join-Path $ProjectRoot 'Reports\VisualCompletion'

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
if (-not $Queue) {
  $defaultQueue = Join-Path $ProjectRoot 'Artwork\ART_QUEUE.csv'
  if (Test-Path $defaultQueue) { $Queue = $defaultQueue } else { $Queue = Pick-File 'Select ART_QUEUE.csv' 'CSV files (*.csv)|*.csv' }
}
if (-not $Workspace) {
  $defaultWorkspace = Join-Path $ProjectRoot 'Artwork\MasterWorkspace'
  if (Test-Path $defaultWorkspace) { $Workspace = $defaultWorkspace } else { $Workspace = Pick-Folder 'Select MasterWorkspace folder' }
}

New-Item -ItemType Directory -Force -Path $Output | Out-Null
& python $Tool $Pack $Output --queue $Queue --workspace $Workspace --batch-size $BatchSize
if ($LASTEXITCODE -ne 0) { throw "Visual Completion Matrix failed with exit code $LASTEXITCODE" }

$Dashboard = Join-Path $Output 'VISUAL_COMPLETION_MATRIX.html'
$Batch = Join-Path $Output 'NEXT_HIGH_IMPACT_ART_BATCH.csv'
Write-Host "Visual completion report: $Dashboard" -ForegroundColor Green
Write-Host "Next high-impact art batch: $Batch" -ForegroundColor Cyan
Start-Process $Dashboard
