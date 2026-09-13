param(
    [string]$Pack,
    [string]$Workspace,
    [string]$Rom,
    [string]$HdPacksRoot
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
$ProjectDir = Split-Path -Parent $PSScriptRoot
$Finish = Join-Path $PSScriptRoot 'High_Impact_Art_Sprint.ps1'
$Playtest = Join-Path $PSScriptRoot 'Build_HD_Playtest.ps1'

function Select-Folder([string]$Description) {
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = $Description
    if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { return $null }
    return $dialog.SelectedPath
}

if (-not $Pack) {
    $Pack = Select-Folder 'Select the current Project #002 capture/HD pack containing hires.txt'
    if (-not $Pack) { exit 0 }
}
if (-not (Test-Path (Join-Path $Pack 'hires.txt'))) { throw "Selected pack does not contain hires.txt: $Pack" }

if (-not $Workspace) {
    $Workspace = Select-Folder 'Select the LOCAL Project #002 production workspace root'
    if (-not $Workspace) { exit 0 }
}

$Master = Join-Path $Workspace 'Artwork\MasterWorkspace'
$Kit = Join-Path $Workspace 'Artwork\CurrentImpactSprint'
$Candidate = Join-Path $Workspace 'Build\HighImpactCandidate'
if (-not (Test-Path (Join-Path $Kit 'ART_SPRINT_KIT.json'))) { throw "No active High-Impact Art Sprint: $Kit" }
if (-not (Test-Path $Master)) { throw "MasterWorkspace not found: $Master" }

Write-Host '=== Project #002 — Family Art Commit -> QA -> Fullscreen Playtest ===' -ForegroundColor Cyan
Write-Host '1/2 Transactional family art commit + visual/family/Pixel QA...' -ForegroundColor Yellow
& $Finish -Pack $Pack -Workspace $Master -Kit $Kit -OutputPack $Candidate -Finish -Overwrite
if ($LASTEXITCODE -ne 0) { throw 'Transactional art finish failed. Playtest was NOT started.' }

$Transaction = Join-Path $Workspace 'Reports\ArtQA\ART_TRANSACTION.json'
if (Test-Path $Transaction) {
    try {
        $tx = Get-Content -Raw $Transaction | ConvertFrom-Json
        if ($tx.status -and $tx.status -ne 'COMMITTED') { throw "Art transaction is not COMMITTED: $($tx.status)" }
    } catch {
        throw "Could not validate committed art transaction: $($_.Exception.Message)"
    }
}

Write-Host '2/2 QA passed. Building/deploying exact current workspace and launching verified fullscreen MesenCE...' -ForegroundColor Green
$Args = @('-Capture', $Pack, '-ProjectRoot', $Workspace)
if ($Rom) { $Args += @('-Rom', $Rom) }
if ($HdPacksRoot) { $Args += @('-HdPacksRoot', $HdPacksRoot) }
& $Playtest @Args
if ($LASTEXITCODE -ne 0) { throw 'Fullscreen HD playtest failed after a successful art commit.' }

Write-Host 'Family redraw committed, QA-passed and handed to verified fullscreen playtest.' -ForegroundColor Green
