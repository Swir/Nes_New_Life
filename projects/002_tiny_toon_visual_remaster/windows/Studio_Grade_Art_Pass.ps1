param(
    [string]$Kit,
    [switch]$Force,
    [switch]$NoCandidates
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Tool = Join-Path $ProjectRoot 'tools\studio_grade_art_pass.py'
if (-not $Kit) {
    $defaultKit = Join-Path $ProjectRoot 'Artwork\CurrentImpactSprint'
    if (Test-Path (Join-Path $defaultKit 'ART_SPRINT_KIT.json')) {
        $Kit = $defaultKit
    } else {
        $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
        $dialog.Description = 'Select High-Impact Art Sprint folder containing ART_SPRINT_KIT.json'
        if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { exit 2 }
        $Kit = $dialog.SelectedPath
    }
}
$Kit = (Resolve-Path $Kit).Path
if (-not (Test-Path (Join-Path $Kit 'ART_SPRINT_KIT.json'))) { throw 'Selected sprint does not contain ART_SPRINT_KIT.json.' }

$Python = 'python'
if (Get-Command py -ErrorAction SilentlyContinue) {
    $Python = 'py'
    $Prefix = @('-3')
} else {
    $Prefix = @()
}

$args = @()
$args += $Prefix
$args += @($Tool, $Kit)
if ($Force) { $args += '--force' }
if ($NoCandidates) { $args += '--no-candidates' }

Write-Host 'Applying Studio-Grade Art Pass to untouched High-Impact Sprint masters...' -ForegroundColor Cyan
& $Python @args
if ($LASTEXITCODE -ne 0) { throw "Studio-Grade Art Pass failed with exit code $LASTEXITCODE" }

$Dashboard = Join-Path $Kit 'STUDIO_GRADE_ART_PASS.html'
$Editable = Join-Path $Kit 'editable'
$Candidates = Join-Path $Kit 'quality_candidates'
Write-Host ''
Write-Host 'STUDIO-GRADE ART PASS READY' -ForegroundColor Green
Write-Host "Editable sprint: $Editable"
Write-Host 'Existing artist edits were protected unless -Force was supplied.' -ForegroundColor Yellow
Write-Host 'Dimensions and alpha are preserved; final Pixel QA and in-game review are still mandatory.' -ForegroundColor Yellow
if (Test-Path $Dashboard) { Start-Process $Dashboard }
if (Test-Path $Editable) { Start-Process explorer.exe $Editable }
if ((Test-Path $Candidates) -and -not $NoCandidates) { Write-Host "Local A/B/C candidates: $Candidates" -ForegroundColor Cyan }
