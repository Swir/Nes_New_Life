param(
  [string]$Pack,
  [int]$BatchSize = 30
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Tool = Join-Path $ProjectRoot 'tools\art_session_controller.py'

function Pick-Folder([string]$Description) {
  Add-Type -AssemblyName System.Windows.Forms
  $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
  $dialog.Description = $Description
  $dialog.ShowNewFolderButton = $false
  if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { throw 'Cancelled.' }
  return $dialog.SelectedPath
}

if (-not $Pack) { $Pack = Pick-Folder 'Select the current HD pack used to export CurrentImpactSprint' }
if (-not (Test-Path (Join-Path $Pack 'hires.txt'))) { throw 'Selected folder does not contain hires.txt.' }

& python $Tool $ProjectRoot $Pack --batch-size $BatchSize
$code = $LASTEXITCODE
$Report = Join-Path $ProjectRoot 'Reports\ArtSessionController\ART_SESSION_CONTROLLER.json'
if (Test-Path $Report) {
  $result = Get-Content $Report -Raw | ConvertFrom-Json
  Write-Host "Art session controller: $($result.status)" -ForegroundColor Cyan
  Write-Host "Pixel QA: $($result.qa_gate) | mapping preserved: $($result.mapping_preserved)"
  Write-Host "Captured unfinished: $($result.captured_unfinished) | blockers: $($result.blocking_items)"
  Write-Host "DO THIS NEXT: $($result.next_action)" -ForegroundColor Yellow
  $NextEditable = Join-Path $ProjectRoot 'Artwork\CurrentImpactSprint\editable'
  if (($result.status -eq 'NEXT_BATCH_READY' -or $result.status -eq 'NEXT_BATCH_PARTIAL') -and (Test-Path $NextEditable)) {
    Start-Process explorer.exe $NextEditable
  }
}
if ($code -ne 0) { throw "Art session continuation blocked with exit code $code" }
