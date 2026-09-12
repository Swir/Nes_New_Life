param(
    [switch]$NoGitHubPrompt
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Tools = Join-Path $ProjectRoot 'tools'
$Reports = Join-Path $ProjectRoot 'Reports\LocalCaptureBridge'
$Bridge = Join-Path $Tools 'local_capture_bridge.py'
$Validator = Join-Path $Tools 'capture_evidence_validator.py'

function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) { return @('py', '-3') }
    if (Get-Command python -ErrorAction SilentlyContinue) { return @('python') }
    throw 'Python 3 was not found in PATH.'
}

function Select-Folder([string]$Description) {
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = $Description
    if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { return $dialog.SelectedPath }
    return $null
}

function Invoke-Python([string[]]$Prefix, [string[]]$Arguments) {
    $exe = $Prefix[0]
    $all = @()
    if ($Prefix.Count -gt 1) { $all += $Prefix[1..($Prefix.Count - 1)] }
    $all += $Arguments
    & $exe @all
    return $LASTEXITCODE
}

$Python = Get-PythonCommand
$Current = Select-Folder 'Select CURRENT MesenCE HD Pack capture. Capture PNGs stay local.'
if (-not $Current) { exit 2 }

$Previous = $null
$compare = [System.Windows.Forms.MessageBox]::Show(
    'Compare this capture with the previous accepted capture? Recommended: YES.',
    'Project #002 Local Capture Bridge',
    [System.Windows.Forms.MessageBoxButtons]::YesNo,
    [System.Windows.Forms.MessageBoxIcon]::Question
)
if ($compare -eq [System.Windows.Forms.DialogResult]::Yes) {
    $Previous = Select-Folder 'Select PREVIOUS accepted MesenCE capture'
}

New-Item -ItemType Directory -Force -Path $Reports | Out-Null
$args = @($Bridge, $ProjectRoot, $Current, '--output', $Reports)
if ($Previous) { $args += @('--previous-capture', $Previous) }

Write-Host 'Building privacy-safe capture evidence...' -ForegroundColor Cyan
$bridgeRc = Invoke-Python $Python $args
if ($bridgeRc -notin @(0, 2)) {
    throw "Local Capture Bridge failed with exit code $bridgeRc"
}

$Handoff = Join-Path $Reports 'SAFE_CAPTURE_HANDOFF.json'
if (-not (Test-Path $Handoff)) { throw 'SAFE_CAPTURE_HANDOFF.json was not created.' }
$validateRc = Invoke-Python $Python @($Validator, $Handoff)
if ($validateRc -ne 0) { throw 'Privacy validator blocked the handoff.' }

$Dashboard = Join-Path $Reports 'LOCAL_CAPTURE_BRIDGE.html'
if (Test-Path $Dashboard) { Start-Process $Dashboard }

Write-Host ''
Write-Host 'SAFE HANDOFF READY' -ForegroundColor Green
Write-Host "  $Handoff"
Write-Host 'No ROM, save-state, capture image pixels or emulator binary is included.'
if ($bridgeRc -eq 2) {
    Write-Host 'Capture regression was detected. Evidence is safe to share, but promotion must remain blocked.' -ForegroundColor Yellow
}

if ($NoGitHubPrompt) { exit $bridgeRc }

$send = [System.Windows.Forms.MessageBox]::Show(
    'Send ONLY the validated metadata JSON to GitHub as a new evidence PR? This never uploads capture PNGs or the ROM.',
    'Safe GitHub handoff',
    [System.Windows.Forms.MessageBoxButtons]::YesNo,
    [System.Windows.Forms.MessageBoxIcon]::Question
)
if ($send -ne [System.Windows.Forms.DialogResult]::Yes) { exit $bridgeRc }

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    [System.Windows.Forms.MessageBox]::Show(
        "GitHub CLI (gh) is not installed or not in PATH.`nThe validated handoff remains here:`n$Handoff",
        'GitHub handoff not sent',
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Information
    ) | Out-Null
    exit $bridgeRc
}

& gh auth status --hostname github.com *> $null
if ($LASTEXITCODE -ne 0) {
    [System.Windows.Forms.MessageBox]::Show(
        "GitHub CLI is not authenticated. Run: gh auth login`nThe validated handoff remains here:`n$Handoff",
        'GitHub login required',
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Information
    ) | Out-Null
    exit $bridgeRc
}

$Repo = 'Swir/Nes_New_Life'
$Stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss')
$Branch = "evidence/project-002-capture-$Stamp"
$RepoPath = "projects/002_tiny_toon_visual_remaster/evidence/capture/SAFE_CAPTURE_HANDOFF_$Stamp.json"
$BaseSha = (& gh api "repos/$Repo/git/ref/heads/main" --jq '.object.sha').Trim()
if (-not $BaseSha) { throw 'Could not resolve GitHub main SHA.' }

& gh api -X POST "repos/$Repo/git/refs" -f "ref=refs/heads/$Branch" -f "sha=$BaseSha" | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Could not create evidence branch on GitHub.' }

$Bytes = [System.IO.File]::ReadAllBytes($Handoff)
$Base64 = [Convert]::ToBase64String($Bytes)
& gh api -X PUT "repos/$Repo/contents/$RepoPath" -f 'message=Project #002: add validated local capture evidence' -f "content=$Base64" -f "branch=$Branch" | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Could not upload validated evidence JSON.' }

$Body = @"
Privacy-safe Project #002 Local Capture Bridge handoff.

- metadata JSON only
- no ROM
- no save state
- no capture PNG/image payload
- no emulator binary
- no absolute local paths

The capture-evidence workflow must pass before this evidence is trusted. This PR does not auto-complete ROADMAP Gate A-D checkboxes.
"@
& gh pr create --repo $Repo --base main --head $Branch --title 'Project #002: validated local capture evidence handoff' --body $Body
if ($LASTEXITCODE -ne 0) { throw 'Evidence branch was uploaded, but PR creation failed.' }

[System.Windows.Forms.MessageBox]::Show(
    'Validated metadata-only capture evidence was sent to GitHub as a PR. ROADMAP progress still requires authoritative evidence review.',
    'GitHub handoff created',
    [System.Windows.Forms.MessageBoxButtons]::OK,
    [System.Windows.Forms.MessageBoxIcon]::Information
) | Out-Null

exit $bridgeRc
