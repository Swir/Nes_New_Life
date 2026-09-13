param(
    [string]$RomPath,
    [string]$CurrentCapture,
    [string]$PreviousCapture,
    [switch]$NoGitHubPrompt,
    [switch]$ForgetSavedPaths,
    [switch]$SkipCapture,
    [switch]$NoOpen
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$CaptureLoop = Join-Path $PSScriptRoot 'Capture_Next_Best_Loop.ps1'
$ReviewLauncher = Join-Path $PSScriptRoot 'Gate_A_Review_Attestation.ps1'
$PatchDirector = Join-Path $PSScriptRoot 'Roadmap_Patch_Director.ps1'
$Tool = Join-Path $ProjectRoot 'tools\capture_review_director.py'
$ReviewJson = Join-Path $ProjectRoot 'Reports\GateAReviewAttestation\GATE_A_REVIEW_HANDOFF.json'
$DirectorOutput = Join-Path $ProjectRoot 'Reports\CaptureReviewDirector'
$DirectorJson = Join-Path $DirectorOutput 'CAPTURE_REVIEW_DIRECTOR.json'
$DirectorDashboard = Join-Path $DirectorOutput 'CAPTURE_REVIEW_DIRECTOR.html'

function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) { return @('py', '-3') }
    if (Get-Command python -ErrorAction SilentlyContinue) { return @('python') }
    throw 'Python 3 was not found in PATH.'
}

function Refresh-Director {
    if (-not (Test-Path $ReviewJson)) {
        throw 'Gate A review handoff is missing. Run a real capture session first.'
    }
    New-Item -ItemType Directory -Force -Path $DirectorOutput | Out-Null
    $Python = Get-PythonCommand
    $exe = $Python[0]
    $args = @()
    if ($Python.Count -gt 1) { $args += $Python[1..($Python.Count - 1)] }
    $args += @($Tool, $ReviewJson, '--output', $DirectorOutput)
    & $exe @args | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "Capture Review Director failed with exit code $LASTEXITCODE" }
    if (-not (Test-Path $DirectorJson)) { throw 'Capture Review Director did not produce its state JSON.' }
    return (Get-Content $DirectorJson -Raw | ConvertFrom-Json)
}

Write-Host ''
Write-Host '=== PROJECT #002 — CAPTURE → REVIEW DIRECTOR ===' -ForegroundColor Cyan
Write-Host 'One operational path: highest-impact MesenCE capture → evidence refresh → explicit Gate A review → ROADMAP patch preview.' -ForegroundColor Yellow
Write-Host 'Nothing is attested automatically. Every evidence-ready Gate A criterion still requires exact VERIFIED_GATE_A confirmation after real local gameplay review.'
Write-Host ''

if (-not $SkipCapture) {
    $captureArgs = @{}
    if ($RomPath) { $captureArgs['RomPath'] = $RomPath }
    if ($CurrentCapture) { $captureArgs['CurrentCapture'] = $CurrentCapture }
    if ($PreviousCapture) { $captureArgs['PreviousCapture'] = $PreviousCapture }
    if ($NoGitHubPrompt) { $captureArgs['NoGitHubPrompt'] = $true }
    if ($ForgetSavedPaths) { $captureArgs['ForgetSavedPaths'] = $true }
    & $CaptureLoop @captureArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Capture loop returned exit code $LASTEXITCODE. Director will still inspect any refreshed evidence that exists." -ForegroundColor Yellow
    }
}

$state = Refresh-Director

while ($state.state -eq 'REVIEW_REQUIRED') {
    $next = $state.next_action
    $index = [int]$next.index
    Write-Host ''
    Write-Host ("NEXT REVIEW #{0}: {1}" -f $index, $next.criterion) -ForegroundColor Cyan
    Write-Host $next.instruction -ForegroundColor Yellow
    Write-Host 'The review launcher will require the exact token VERIFIED_GATE_A. Any other input cancels without changing evidence state.'
    & $ReviewLauncher -AttestIndex $index -NoOpen
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'Review was not attested. Stopping without changing ROADMAP.' -ForegroundColor Yellow
        break
    }
    $state = Refresh-Director
}

if ($state.state -eq 'GATE_A_REVIEW_COMPLETE') {
    Write-Host ''
    Write-Host 'All 12 Gate A criteria are explicitly reviewed for this exact capture fingerprint.' -ForegroundColor Green
    Write-Host 'Refreshing the fail-closed Project/Master ROADMAP patch preview...' -ForegroundColor Cyan
    & $PatchDirector -NoOpen
    if ($LASTEXITCODE -ne 0) { throw "ROADMAP patch preview failed with exit code $LASTEXITCODE" }
} elseif ($state.state -eq 'CAPTURE_WORK_REQUIRED') {
    Write-Host ''
    Write-Host 'Gate A still requires real gameplay capture work.' -ForegroundColor Yellow
    Write-Host ("DO THIS NEXT: {0}" -f $state.next_action.criterion)
    Write-Host $state.next_action.instruction
}

if (-not $NoOpen -and (Test-Path $DirectorDashboard)) {
    Start-Process $DirectorDashboard
}

Write-Host ''
Write-Host ("CAPTURE REVIEW DIRECTOR STATE: {0}" -f $state.state) -ForegroundColor Cyan
Write-Host ("Verified {0}/12 · Reviewable {1} · Blocked {2}" -f $state.summary.verified, $state.summary.reviewable, $state.summary.blocked)
Write-Host 'Repository ROADMAP files were not edited automatically.' -ForegroundColor Cyan
