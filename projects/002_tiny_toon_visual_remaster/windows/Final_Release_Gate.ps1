$ErrorActionPreference = 'Stop'
$Project = Split-Path -Parent $PSScriptRoot
$Tools = Join-Path $Project 'tools'
$Reports = Join-Path $Project 'Reports\FinalReleaseReadiness'

function Pick-File([string]$Title, [string]$Filter) {
    Add-Type -AssemblyName System.Windows.Forms
    $dialog = New-Object System.Windows.Forms.OpenFileDialog
    $dialog.Title = $Title
    $dialog.Filter = $Filter
    if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { throw "Cancelled: $Title" }
    return $dialog.FileName
}

function Pick-Folder([string]$Title) {
    Add-Type -AssemblyName System.Windows.Forms
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = $Title
    if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { throw "Cancelled: $Title" }
    return $dialog.SelectedPath
}

Write-Host 'Project #002 - FINAL RELEASE GATE' -ForegroundColor Cyan
Write-Host 'Select the exact final HD Pack and its current evidence files.'

$Pack = Pick-Folder 'Select exact final HD Pack folder (contains hires.txt)'
$Capture = Pick-File 'Select CAPTURE_MISSIONS.json' 'JSON files (*.json)|*.json|All files (*.*)|*.*'
$Queue = Pick-File 'Select ART_QUEUE.csv' 'CSV files (*.csv)|*.csv|All files (*.*)|*.*'
$Visual = Pick-File 'Select VISUAL_CONTEXT_REVIEW.csv' 'CSV files (*.csv)|*.csv|All files (*.*)|*.*'
$ArtQa = Pick-File 'Select ART_QA_RESULT.json' 'JSON files (*.json)|*.json|All files (*.*)|*.*'
$Regression = Pick-File 'Select FINAL_REGRESSION.json' 'JSON files (*.json)|*.json|All files (*.*)|*.*'
$Fullscreen = Pick-File 'Select FULLSCREEN_PLAYTEST.json' 'JSON files (*.json)|*.json|All files (*.*)|*.*'

New-Item -ItemType Directory -Force -Path $Reports | Out-Null

& python (Join-Path $Tools 'final_release_director.py') audit $Pack `
    --capture $Capture `
    --queue $Queue `
    --visual-review $Visual `
    --art-qa $ArtQa `
    --regression $Regression `
    --fullscreen $Fullscreen `
    --output $Reports
$code = $LASTEXITCODE

$Dashboard = Join-Path $Reports 'FINAL_RELEASE_READINESS.html'
if (Test-Path $Dashboard) { Start-Process $Dashboard }

if ($code -eq 0) {
    Write-Host ''
    Write-Host 'FINAL RELEASE GATE: PASS' -ForegroundColor Green
    $answer = Read-Host 'Create the gated public HD Pack ZIP now? (Y/N)'
    if ($answer -match '^[Yy]$') {
        $ReleaseDir = Join-Path $Project 'Release'
        New-Item -ItemType Directory -Force -Path $ReleaseDir | Out-Null
        $Zip = Join-Path $ReleaseDir 'TinyToon_Visual_Remaster_HD.zip'
        & python (Join-Path $Tools 'final_release_director.py') package $Pack `
            --capture $Capture `
            --queue $Queue `
            --visual-review $Visual `
            --art-qa $ArtQa `
            --regression $Regression `
            --fullscreen $Fullscreen `
            --output $Reports `
            --zip $Zip
        if ($LASTEXITCODE -ne 0) { throw 'Packaging gate failed.' }
        Write-Host "Created: $Zip" -ForegroundColor Green
    }
} else {
    Write-Host ''
    Write-Host 'FINAL RELEASE GATE: BLOCKED - follow DO THIS NEXT in the dashboard.' -ForegroundColor Yellow
}
