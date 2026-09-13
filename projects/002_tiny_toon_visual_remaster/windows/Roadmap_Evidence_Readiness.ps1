$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Tool = Join-Path $ProjectRoot 'tools\roadmap_evidence_readiness.py'

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Error 'Python 3.11+ was not found on PATH.'
    exit 1
}

Write-Host 'Project #002 - ROADMAP Evidence Readiness' -ForegroundColor Cyan
Write-Host 'This is read-only: it never edits ROADMAP Gate A-D.' -ForegroundColor Yellow
& $python.Source $Tool $ProjectRoot
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$Report = Join-Path $ProjectRoot 'Reports\RoadmapEvidenceReadiness\ROADMAP_EVIDENCE_READINESS.html'
if (Test-Path $Report) {
    Start-Process $Report
}
