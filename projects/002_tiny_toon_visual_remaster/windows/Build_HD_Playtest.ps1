param(
    [string]$Capture,
    [string]$ProjectRoot,
    [string]$Rom,
    [string]$HdPacksRoot,
    [switch]$BuildOnly
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms

function Select-Folder([string]$Description, [string]$InitialDirectory = '') {
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = $Description
    if ($InitialDirectory -and (Test-Path $InitialDirectory)) { $dialog.SelectedPath = $InitialDirectory }
    if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { return $null }
    return $dialog.SelectedPath
}

function Select-Rom([string]$InitialDirectory = '') {
    $dialog = New-Object System.Windows.Forms.OpenFileDialog
    $dialog.Title = 'Choose your local Tiny Toon NES ROM'
    $dialog.Filter = 'NES ROM (*.nes)|*.nes|All files (*.*)|*.*'
    if ($InitialDirectory -and (Test-Path $InitialDirectory)) { $dialog.InitialDirectory = $InitialDirectory }
    if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { return $null }
    return $dialog.FileName
}

$ProjectDir = Split-Path -Parent $PSScriptRoot
$Tool = Join-Path $ProjectDir 'tools\rapid_hd_playtest.py'
$Launcher = Join-Path $PSScriptRoot 'launch_remaster.ps1'
if (-not (Test-Path $Tool)) { throw "Missing rapid playtest tool: $Tool" }
if (-not (Test-Path $Launcher)) { throw "Missing fullscreen launcher: $Launcher" }

if (-not $Capture) {
    $Capture = Select-Folder 'Choose the MesenCE HD Pack Builder capture folder (hires.txt + PNG files)'
    if (-not $Capture) { exit 0 }
}
if (-not (Test-Path (Join-Path $Capture 'hires.txt'))) { throw "Selected capture does not contain hires.txt: $Capture" }

if (-not $ProjectRoot) {
    $ProjectRoot = Select-Folder 'Choose your LOCAL Tiny Toon remaster workspace root'
    if (-not $ProjectRoot) { exit 0 }
}

if (-not $Rom) {
    $Rom = Select-Rom
    if (-not $Rom) { exit 0 }
}

if (-not $HdPacksRoot) {
    $DefaultHdPacks = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'MesenCE\HdPacks'
    $answer = [System.Windows.Forms.MessageBox]::Show(
        "Install the QA-passed playtest directly to:`n$DefaultHdPacks`n`nChoose No to select a different MesenCE HdPacks folder.",
        'NES New Life - HD Playtest',
        [System.Windows.Forms.MessageBoxButtons]::YesNoCancel,
        [System.Windows.Forms.MessageBoxIcon]::Question
    )
    if ($answer -eq [System.Windows.Forms.DialogResult]::Cancel) { exit 0 }
    if ($answer -eq [System.Windows.Forms.DialogResult]::Yes) {
        $HdPacksRoot = $DefaultHdPacks
    } else {
        $HdPacksRoot = Select-Folder 'Choose the MesenCE HdPacks folder'
        if (-not $HdPacksRoot) { exit 0 }
    }
}

$Python = Get-Command py -ErrorAction SilentlyContinue
if ($Python) {
    $PythonExe = 'py'
    $PythonPrefix = @('-3')
} else {
    $Python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $Python) { throw 'Python 3 was not found. Install Python 3.11+ and dependencies from requirements.txt.' }
    $PythonExe = 'python'
    $PythonPrefix = @()
}

$Arguments = @()
$Arguments += $PythonPrefix
$Arguments += @(
    $Tool,
    $Capture,
    $ProjectRoot,
    '--profile', 'group-aware',
    '--rom-name', (Split-Path -Leaf $Rom),
    '--hdpacks-root', $HdPacksRoot
)

Write-Host ''
Write-Host '=== NES New Life — Tiny Toon QA-Gated Fullscreen HD Playtest ===' -ForegroundColor Cyan
Write-Host "Capture:   $Capture"
Write-Host "Workspace: $ProjectRoot"
Write-Host "ROM:       $Rom"
Write-Host "HdPacks:   $HdPacksRoot"
Write-Host ''
Write-Host 'Running capture sync -> automatic baseline -> batch apply -> pixel QA -> validation -> MesenCE install...' -ForegroundColor Yellow

& $PythonExe @Arguments
if ($LASTEXITCODE -ne 0) { throw "Rapid HD Playtest failed with exit code $LASTEXITCODE. No successful deployment was reported." }

$Installed = Join-Path $HdPacksRoot ([IO.Path]::GetFileNameWithoutExtension($Rom))
$RuntimePack = Join-Path $ProjectRoot 'ModernizedPack\playtest_current'
$Evidence = Join-Path $ProjectRoot 'Reports\FullscreenPlaytest\FULLSCREEN_PLAYTEST.json'

if ($BuildOnly) {
    [System.Windows.Forms.MessageBox]::Show(
        "HD playtest build completed and installed to:`n$Installed`n`nBuildOnly was requested, so MesenCE was not launched.",
        'Tiny Toon HD Playtest Ready',
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Information
    ) | Out-Null
    exit 0
}

Write-Host ''
Write-Host 'Build passed. Launching the exact playtest in REQUIRED fullscreen mode...' -ForegroundColor Yellow
& $Launcher -RomPath $Rom -PackDir $RuntimePack -EvidencePath $Evidence
if ($LASTEXITCODE -ne 0) { throw 'MesenCE fullscreen launch failed.' }

[System.Windows.Forms.MessageBox]::Show(
    "HD playtest is installed and running in verified fullscreen.`n`nInstalled pack:`n$Installed`n`nFullscreen evidence:`n$Evidence`n`nContinue the real full-game regression in Final Regression Cockpit.",
    'Tiny Toon Fullscreen HD Playtest Running',
    [System.Windows.Forms.MessageBoxButtons]::OK,
    [System.Windows.Forms.MessageBoxIcon]::Information
) | Out-Null
