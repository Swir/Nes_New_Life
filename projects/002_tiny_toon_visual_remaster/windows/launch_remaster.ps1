param(
    [string]$RomPath,
    [switch]$AllowDifferentRom
)

$ErrorActionPreference = 'Stop'
$ExpectedSha1 = '110796622e50c2e8c20b1430acadc5bae5f36586'
$ProjectDir = Split-Path -Parent $PSScriptRoot
$InstallDir = Join-Path $ProjectDir 'vendor\MesenCE'
$SetupScript = Join-Path $PSScriptRoot 'setup_mesence.ps1'

$exe = Get-ChildItem -Path $InstallDir -Filter 'Mesen.exe' -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $exe) {
    Write-Host 'MesenCE is not installed yet. Installing the latest official Windows build...' -ForegroundColor Yellow
    & $SetupScript -InstallDir $InstallDir
    $exe = Get-ChildItem -Path $InstallDir -Filter 'Mesen.exe' -File -Recurse | Select-Object -First 1
}

if ([string]::IsNullOrWhiteSpace($RomPath)) {
    Add-Type -AssemblyName System.Windows.Forms
    $dialog = New-Object System.Windows.Forms.OpenFileDialog
    $dialog.Title = 'Select Tiny Toon Adventures NES ROM'
    $dialog.Filter = 'NES ROM (*.nes)|*.nes|All files (*.*)|*.*'
    $dialog.Multiselect = $false
    if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
        Write-Host 'No ROM selected.'
        exit 0
    }
    $RomPath = $dialog.FileName
}

$RomPath = (Resolve-Path $RomPath).Path
$sha1 = (Get-FileHash -Path $RomPath -Algorithm SHA1).Hash.ToLowerInvariant()
if ($sha1 -ne $ExpectedSha1 -and -not $AllowDifferentRom) {
    throw "This ROM does not match the Project #002 fingerprint. SHA-1: $sha1. Expected: $ExpectedSha1. Use -AllowDifferentRom only if you intentionally want to test another revision."
}

Write-Host ''
Write-Host 'Recommended controls in MesenCE:' -ForegroundColor Cyan
Write-Host '  Arrow keys  = D-pad'
Write-Host '  Z           = NES A'
Write-Host '  X           = NES B'
Write-Host '  Enter       = Start'
Write-Host '  Right Shift = Select'
Write-Host '  Esc         = emulator/menu'
Write-Host ''
Write-Host 'For the graphics workflow, use MesenCE HD Packs / HD Pack Builder.' -ForegroundColor Cyan
Write-Host 'The ROM is launched from its current location and is not copied.'

Start-Process -FilePath $exe.FullName -ArgumentList @($RomPath)
