param(
    [string]$RomPath,
    [string]$CurrentCapture,
    [string]$PreviousCapture,
    [switch]$NoGitHubPrompt,
    [switch]$ForgetSavedPaths
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$SingleSession = Join-Path $PSScriptRoot 'Capture_Single_Best_Session.ps1'
$GateATool = Join-Path $ProjectRoot 'tools\gate_a_evidence_matrix.py'
$AcceptanceJson = Join-Path $ProjectRoot 'Reports\CaptureCoverageAcceptance\CAPTURE_COVERAGE_ACCEPTANCE.json'
$GateAReports = Join-Path $ProjectRoot 'Reports\GateAEvidenceMatrix'
$GateADashboard = Join-Path $GateAReports 'GATE_A_EVIDENCE_MATRIX.html'

function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) { return @('py', '-3') }
    if (Get-Command python -ErrorAction SilentlyContinue) { return @('python') }
    throw 'Python 3 was not found in PATH.'
}

$singleArgs = @{}
if ($RomPath) { $singleArgs['RomPath'] = $RomPath }
if ($CurrentCapture) { $singleArgs['CurrentCapture'] = $CurrentCapture }
if ($PreviousCapture) { $singleArgs['PreviousCapture'] = $PreviousCapture }
if ($NoGitHubPrompt) { $singleArgs['NoGitHubPrompt'] = $true }
if ($ForgetSavedPaths) { $singleArgs['ForgetSavedPaths'] = $true }

Write-Host ''
Write-Host '=== PROJECT #002 — NEXT-BEST CAPTURE LOOP ===' -ForegroundColor Cyan
Write-Host 'Runs exactly one highest-impact route-aware fullscreen MesenCE pass per invocation.' -ForegroundColor Yellow
Write-Host 'Local ROM/capture paths are reused from LOCALAPPDATA after the first run.'
Write-Host 'After the pass: integrity + gap + route + safe evidence + acceptance + Gate A evidence matrix + next action are refreshed automatically.'
Write-Host 'No mission or ROADMAP checkbox is completed automatically.'
Write-Host ''

& $SingleSession @singleArgs
$SessionRc = $LASTEXITCODE

if (Test-Path $AcceptanceJson) {
    $Python = Get-PythonCommand
    New-Item -ItemType Directory -Force -Path $GateAReports | Out-Null
    $exe = $Python[0]
    $args = @()
    if ($Python.Count -gt 1) { $args += $Python[1..($Python.Count - 1)] }
    $args += @($GateATool, $AcceptanceJson, '--output', $GateAReports)
    & $exe @args | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "Gate A evidence matrix failed with exit code $LASTEXITCODE" }
    if (Test-Path $GateADashboard) {
        Start-Process $GateADashboard
        Write-Host ("GATE A EVIDENCE MATRIX: {0}" -f $GateADashboard) -ForegroundColor Green
    }
} else {
    Write-Host 'Gate A evidence matrix skipped: no Capture Coverage Acceptance manifest exists yet.' -ForegroundColor Yellow
}

exit $SessionRc
