param(
    [switch]$NoOpen
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$RepoRoot = (Resolve-Path (Join-Path $ProjectRoot '..\..')).Path
$Tool = Join-Path $ProjectRoot 'tools\roadmap_patch_director.py'
$ReviewDir = Join-Path $ProjectRoot 'Reports\GateAReviewAttestation'
$Review = Join-Path $ReviewDir 'GATE_A_REVIEW_HANDOFF.json'
$Ledger = Join-Path $ReviewDir 'GATE_A_ATTESTATIONS.json'
$ProjectRoadmap = Join-Path $ProjectRoot 'ROADMAP.md'
$MasterRoadmap = Join-Path $RepoRoot 'docs\ROADMAP.md'
$Output = Join-Path $ProjectRoot 'Reports\RoadmapPatchDirector'
$Diff = Join-Path $Output 'ROADMAP_PATCH_PREVIEW.diff'
$Manifest = Join-Path $Output 'ROADMAP_PATCH_DIRECTOR.json'

function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) { return @('py', '-3') }
    if (Get-Command python -ErrorAction SilentlyContinue) { return @('python') }
    throw 'Python 3 was not found in PATH.'
}

foreach ($required in @($Review, $Ledger, $ProjectRoadmap, $MasterRoadmap, $Tool)) {
    if (-not (Test-Path $required)) {
        throw "Required ROADMAP patch input is missing: $required"
    }
}

New-Item -ItemType Directory -Force -Path $Output | Out-Null
$Python = Get-PythonCommand
$exe = $Python[0]
$args = @()
if ($Python.Count -gt 1) { $args += $Python[1..($Python.Count - 1)] }
$args += @(
    $Tool,
    '--review', $Review,
    '--ledger', $Ledger,
    '--project-roadmap', $ProjectRoadmap,
    '--master-roadmap', $MasterRoadmap,
    '--output', $Output
)

Write-Host ''
Write-Host '=== GATE A ROADMAP PATCH DIRECTOR ===' -ForegroundColor Cyan
Write-Host 'Generating a fail-closed preview from exact-fingerprint VERIFIED_GATE_A attestations.'
Write-Host 'No repository ROADMAP file will be modified by this command.' -ForegroundColor Yellow

& $exe @args | Out-Host
if ($LASTEXITCODE -ne 0) {
    throw "ROADMAP Patch Director failed with exit code $LASTEXITCODE"
}

if (-not (Test-Path $Manifest)) {
    throw 'ROADMAP Patch Director did not produce its manifest.'
}

$state = Get-Content -Raw -Path $Manifest | ConvertFrom-Json
Write-Host ("Status: {0}" -f $state.status) -ForegroundColor Green
Write-Host ("Verified Gate A indexes: {0}" -f (($state.verified_gate_a_indexes -join ', ')))
Write-Host ("Projected authoritative progress: {0}/{1} = {2}%" -f $state.stats.completed, $state.stats.total, $state.stats.percent)
Write-Host ("Diff preview: {0}" -f $Diff) -ForegroundColor Green
Write-Host 'The preview must still be reviewed and committed through a normal feature branch + PR with Roadmap Standard CI.' -ForegroundColor Yellow

if (-not $NoOpen -and (Test-Path $Diff)) {
    Start-Process notepad.exe -ArgumentList @($Diff)
}
