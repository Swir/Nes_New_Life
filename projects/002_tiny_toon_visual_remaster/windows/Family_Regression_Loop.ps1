param(
    [string]$ProjectRoot,
    [string]$Capture,
    [string]$RuntimePack,
    [int]$BatchSize = 30,
    [switch]$PrepareNextFamily,
    [switch]$NoOpen
)
$ErrorActionPreference = 'Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $ProjectRoot) { $ProjectRoot = Split-Path -Parent $Here }
$Tool = Join-Path $ProjectRoot 'tools\family_regression_loop.py'
$StatePath = Join-Path $env:LOCALAPPDATA 'Swir\TinyToonVisualRemaster\capture-session.json'

function Python-Cmd {
    if (Get-Command py -ErrorAction SilentlyContinue) { return @('py','-3') }
    if (Get-Command python -ErrorAction SilentlyContinue) { return @('python') }
    throw 'Python 3 was not found in PATH.'
}
function Pick-Folder([string]$Title) {
    Add-Type -AssemblyName System.Windows.Forms
    $d = New-Object System.Windows.Forms.FolderBrowserDialog
    $d.Description = $Title
    if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { return $d.SelectedPath }
    return $null
}
if (-not $Capture -and (Test-Path $StatePath)) {
    try { $s = Get-Content -Raw $StatePath | ConvertFrom-Json; if ($s.current_capture -and (Test-Path $s.current_capture)) { $Capture = $s.current_capture } } catch {}
}
if (-not $Capture) { $Capture = Pick-Folder 'Select current accepted MesenCE capture / HD pack' }
if (-not $Capture) { exit 2 }
if (-not $RuntimePack) {
    $candidate = Join-Path $ProjectRoot 'Build\HighImpactCandidate'
    if (Test-Path (Join-Path $candidate 'hires.txt')) { $RuntimePack = $candidate } else { $RuntimePack = Pick-Folder 'Select exact runtime HD pack used for fullscreen/regression' }
}
if (-not $RuntimePack) { exit 2 }
if (-not (Test-Path (Join-Path $RuntimePack 'hires.txt'))) { throw 'Runtime pack must contain hires.txt.' }

$p = Python-Cmd
$argsList = @($Tool, $ProjectRoot, $Capture, $RuntimePack, '--batch-size', [string]([Math]::Max(1,$BatchSize)))
if ($PrepareNextFamily) { $argsList += '--prepare-next-family' }
$exe = $p[0]; $all = @(); if ($p.Count -gt 1) { $all += $p[1..($p.Count-1)] }; $all += $argsList
Write-Host '=== PROJECT #002 — FAMILY → QA → FULLSCREEN → REGRESSION LOOP ===' -ForegroundColor Cyan
& $exe @all | Out-Host
if ($LASTEXITCODE -ne 0) { throw "Family Regression Loop failed with exit code $LASTEXITCODE" }
$report = Join-Path $ProjectRoot 'Reports\FamilyRegressionLoop\FAMILY_REGRESSION_LOOP.json'
$dashboard = Join-Path $ProjectRoot 'Reports\FamilyRegressionLoop\FAMILY_REGRESSION_LOOP.html'
if (Test-Path $report) {
    $r = Get-Content -Raw $report | ConvertFrom-Json
    Write-Host ("STATE: {0}" -f $r.decision.state) -ForegroundColor Green
    Write-Host ("DO THIS NEXT: {0}" -f $r.decision.action) -ForegroundColor Yellow
    if ($r.decision.state -eq 'NEXT_FAMILY_READY' -and $r.active_family) {
        $kit = Join-Path $ProjectRoot 'Artwork\CurrentImpactSprint'
        $board = Join-Path $kit $r.active_family.board
        $editable = Join-Path $kit $r.active_family.editable_dir
        if (-not $NoOpen -and (Test-Path $board)) { Start-Process $board }
        if (-not $NoOpen -and (Test-Path $editable)) { Start-Process explorer.exe $editable }
    }
}
if (-not $NoOpen -and (Test-Path $dashboard)) { Start-Process $dashboard }
