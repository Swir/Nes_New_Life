param(
    [string]$ProjectRoot,
    [string]$RuntimePack,
    [switch]$PlanOnly,
    [switch]$NoOpen
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms

$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $ProjectRoot) { $ProjectRoot = Split-Path -Parent $Here }
$ProjectRoot = (Resolve-Path $ProjectRoot).Path
$Director = Join-Path $ProjectRoot 'tools\release_finalization_director.py'
$ReleaseTool = Join-Path $ProjectRoot 'tools\final_release_director.py'
$Output = Join-Path $ProjectRoot 'Reports\ReleaseFinalization'
$PlanJson = Join-Path $Output 'RELEASE_FINALIZATION.json'
$Dashboard = Join-Path $Output 'RELEASE_FINALIZATION.html'

function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) { return @('py','-3') }
    if (Get-Command python -ErrorAction SilentlyContinue) { return @('python') }
    throw 'Python 3 was not found in PATH.'
}
function Invoke-PythonRaw([string[]]$Arguments) {
    $p = Get-PythonCommand
    $exe = $p[0]
    $all = @()
    if ($p.Count -gt 1) { $all += $p[1..($p.Count-1)] }
    $all += $Arguments
    & $exe @all
    return $LASTEXITCODE
}
function Pick-Folder([string]$Description) {
    $d = New-Object System.Windows.Forms.FolderBrowserDialog
    $d.Description = $Description
    if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { return $d.SelectedPath }
    return $null
}
function Resolve-EvidencePath($Plan, [string]$Key) {
    $relative = [string]$Plan.evidence.$Key.path
    if ([System.IO.Path]::IsPathRooted($relative)) { return $relative }
    return Join-Path $ProjectRoot $relative
}

if (-not $RuntimePack) {
    $candidates = @(
        (Join-Path $ProjectRoot 'Build\CaptureGapRecoveredCandidate'),
        (Join-Path $ProjectRoot 'Build\RegressionRepairCandidate'),
        (Join-Path $ProjectRoot 'Build\HighImpactCandidate'),
        (Join-Path $ProjectRoot 'ModernizedPack\playtest_current'),
        (Join-Path $ProjectRoot 'ModernizedPack\final_art')
    )
    foreach ($candidate in $candidates) {
        if (Test-Path (Join-Path $candidate 'hires.txt')) { $RuntimePack = $candidate; break }
    }
}
if (-not $RuntimePack) { $RuntimePack = Pick-Folder 'Select the exact final HD Pack candidate' }
if (-not $RuntimePack) { exit 2 }
$RuntimePack = (Resolve-Path $RuntimePack).Path
if (-not (Test-Path (Join-Path $RuntimePack 'hires.txt'))) { throw 'Runtime pack must contain hires.txt.' }

New-Item -ItemType Directory -Force -Path $Output | Out-Null
$code = Invoke-PythonRaw @($Director, 'plan', $ProjectRoot, $RuntimePack, '--output', $Output)
if ($code -ne 0) { throw ('Release finalization planning failed with code ' + $code) }
$plan = Get-Content -Raw $PlanJson | ConvertFrom-Json

Write-Host ''
Write-Host '=== PROJECT #002 — RELEASE FINALIZATION DIRECTOR ===' -ForegroundColor Cyan
Write-Host ('State: {0}' -f $plan.state) -ForegroundColor Yellow
Write-Host ('Exact fingerprint: {0}' -f $plan.pack_fingerprint) -ForegroundColor DarkGray
Write-Host ('Release gate: {0}' -f $plan.release_gate) -ForegroundColor $(if ($plan.release_gate -eq 'PASS') { 'Green' } else { 'Yellow' })
if ($plan.next_stage) { Write-Host ('First blocker: {0}' -f $plan.next_stage.name) -ForegroundColor Magenta }
Write-Host ('DO THIS NEXT: {0}' -f $plan.next_action) -ForegroundColor Yellow
if (-not $NoOpen -and (Test-Path $Dashboard)) { Start-Process $Dashboard }
if ($PlanOnly) { exit 0 }

if ($plan.state -eq 'PACKAGE_READY') {
    $ReleaseDir = Join-Path $ProjectRoot 'Release'
    New-Item -ItemType Directory -Force -Path $ReleaseDir | Out-Null
    $short = ([string]$plan.pack_fingerprint).Substring(0, [Math]::Min(12, ([string]$plan.pack_fingerprint).Length))
    $Zip = Join-Path $ReleaseDir ("TinyToon_Visual_Remaster_HD_{0}.zip" -f $short)
    $Manifest = Join-Path $ReleaseDir ("TinyToon_Visual_Remaster_HD_{0}.manifest.json" -f $short)

    $capture = Resolve-EvidencePath $plan 'capture'
    $queue = Resolve-EvidencePath $plan 'queue'
    $visual = Resolve-EvidencePath $plan 'visual_review'
    $artQa = Resolve-EvidencePath $plan 'art_qa'
    $regression = Resolve-EvidencePath $plan 'regression'
    $fullscreen = Resolve-EvidencePath $plan 'fullscreen'

    Write-Host 'All seven gates PASS. Re-auditing atomically immediately before packaging...' -ForegroundColor Green
    $code = Invoke-PythonRaw @(
        $ReleaseTool, 'package', $RuntimePack,
        '--capture', $capture,
        '--queue', $queue,
        '--visual-review', $visual,
        '--art-qa', $artQa,
        '--regression', $regression,
        '--fullscreen', $fullscreen,
        '--output', $Output,
        '--zip', $Zip
    )
    if ($code -ne 0) { throw 'Exact-build release gate changed or packaging failed; no release manifest was accepted.' }

    $code = Invoke-PythonRaw @($Director, 'manifest', $PlanJson, $Zip, '--output', $Manifest)
    if ($code -ne 0) { throw 'Release ZIP exists but manifest verification failed.' }
    Write-Host ''
    Write-Host ('ROM-FREE RELEASE READY: {0}' -f $Zip) -ForegroundColor Green
    Write-Host ('Manifest: {0}' -f $Manifest) -ForegroundColor Green
    exit 0
}

$launcher = Join-Path $Here ([string]$plan.launcher)
if (-not (Test-Path $launcher)) { throw ('Finalization route launcher does not exist: ' + $launcher) }
Write-Host ('Dispatching first blocking stage through {0}...' -f $plan.launcher) -ForegroundColor Cyan

switch ($plan.state) {
    'REPAIR_HD_STRUCTURE' { & $launcher -ProjectRoot $ProjectRoot -RuntimePack $RuntimePack -NoOpen:$NoOpen }
    'COMPLETE_FINAL_REGRESSION' { & $launcher -ProjectRoot $ProjectRoot -RuntimePack $RuntimePack -NoOpen:$NoOpen }
    default { & $launcher }
}
$code = $LASTEXITCODE
if ($code -ne 0) {
    Write-Host ('Routed stage exited with code {0}. Release remains blocked.' -f $code) -ForegroundColor Yellow
    exit $code
}
Write-Host 'The routed stage finished. Re-run Finalize_Release_Candidate.bat to re-audit every exact-build gate.' -ForegroundColor Green
exit 0
