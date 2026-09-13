param(
    [int]$AttestIndex = 0,
    [string]$Reviewer = $env:USERNAME
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Tool = Join-Path $ProjectRoot 'tools\gate_a_review_attestation.py'
$Matrix = Join-Path $ProjectRoot 'Reports\GateAEvidenceMatrix\GATE_A_EVIDENCE_MATRIX.json'
$Output = Join-Path $ProjectRoot 'Reports\GateAReviewAttestation'
$Dashboard = Join-Path $Output 'GATE_A_REVIEW_HANDOFF.html'

function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) { return @('py', '-3') }
    if (Get-Command python -ErrorAction SilentlyContinue) { return @('python') }
    throw 'Python 3 was not found in PATH.'
}

if (-not (Test-Path $Matrix)) {
    throw 'Gate A evidence matrix is missing. Run Capture_Next_Best_Loop.bat first.'
}

New-Item -ItemType Directory -Force -Path $Output | Out-Null
$Python = Get-PythonCommand
$exe = $Python[0]
$args = @()
if ($Python.Count -gt 1) { $args += $Python[1..($Python.Count - 1)] }
$args += @($Tool, $Matrix, '--output', $Output)

if ($AttestIndex -gt 0) {
    Write-Host ''
    Write-Host '=== GATE A EXPLICIT LOCAL ATTESTATION ===' -ForegroundColor Yellow
    Write-Host "Criterion index: $AttestIndex"
    Write-Host 'This action is valid only after reviewing the real local MesenCE gameplay evidence for the exact current capture fingerprint.' -ForegroundColor Yellow
    $confirmation = Read-Host 'Type exactly VERIFIED_GATE_A to attest this criterion'
    if ($confirmation -ne 'VERIFIED_GATE_A') {
        Write-Host 'Attestation cancelled. No evidence state was changed.' -ForegroundColor Yellow
        exit 2
    }
    $args += @('--attest-index', [string]$AttestIndex, '--confirmation', 'VERIFIED_GATE_A', '--reviewer', $Reviewer)
}

& $exe @args | Out-Host
if ($LASTEXITCODE -ne 0) { throw "Gate A review handoff failed with exit code $LASTEXITCODE" }

if (Test-Path $Dashboard) {
    Start-Process $Dashboard
    Write-Host ("GATE A REVIEW DASHBOARD: {0}" -f $Dashboard) -ForegroundColor Green
}
Write-Host 'ROADMAP.md was not edited automatically. Any checkbox update still requires a reviewed repository change.' -ForegroundColor Cyan

$PatchDirector = Join-Path $PSScriptRoot 'Roadmap_Patch_Director.ps1'
if (Test-Path $PatchDirector) {
    Write-Host ''
    Write-Host 'Refreshing exact ROADMAP patch preview from current attestations...' -ForegroundColor Cyan
    & $PatchDirector -NoOpen
    if ($LASTEXITCODE -ne 0) { throw "ROADMAP patch preview failed with exit code $LASTEXITCODE" }
}
