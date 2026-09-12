param(
    [string]$RomPath,
    [string]$PackDir,
    [string]$EvidencePath,
    [switch]$AllowDifferentRom,
    [int]$WindowTimeoutSeconds = 8
)

$ErrorActionPreference = 'Stop'
$ExpectedSha1 = '110796622e50c2e8c20b1430acadc5bae5f36586'
$ProjectDir = Split-Path -Parent $PSScriptRoot
$InstallDir = Join-Path $ProjectDir 'vendor\MesenCE'
$SetupScript = Join-Path $PSScriptRoot 'setup_mesence.ps1'
$EvidenceTool = Join-Path $ProjectDir 'tools\fullscreen_launch.py'

Add-Type -AssemblyName System.Windows.Forms
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class Win32Rect {
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
}
'@

function Get-PythonCommand {
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) { return @{ Exe = 'py'; Prefix = @('-3') } }
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) { return @{ Exe = 'python'; Prefix = @() } }
    return $null
}

function Test-FullscreenWindow([System.Diagnostics.Process]$Process, [int]$Tolerance = 8) {
    $Process.Refresh()
    if ($Process.HasExited -or $Process.MainWindowHandle -eq [IntPtr]::Zero) { return $false }
    $rect = New-Object Win32Rect+RECT
    if (-not [Win32Rect]::GetWindowRect($Process.MainWindowHandle, [ref]$rect)) { return $false }
    $screen = [System.Windows.Forms.Screen]::FromHandle($Process.MainWindowHandle)
    $bounds = $screen.Bounds
    $width = $rect.Right - $rect.Left
    $height = $rect.Bottom - $rect.Top
    return (
        [Math]::Abs($rect.Left - $bounds.Left) -le $Tolerance -and
        [Math]::Abs($rect.Top - $bounds.Top) -le $Tolerance -and
        [Math]::Abs($width - $bounds.Width) -le $Tolerance -and
        [Math]::Abs($height - $bounds.Height) -le $Tolerance
    )
}

function Wait-MainWindow([System.Diagnostics.Process]$Process, [int]$Seconds) {
    $deadline = [DateTime]::UtcNow.AddSeconds($Seconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        if ($Process.HasExited) { return $false }
        $Process.Refresh()
        if ($Process.MainWindowHandle -ne [IntPtr]::Zero) { return $true }
        Start-Sleep -Milliseconds 200
    }
    return $false
}

function Write-FullscreenEvidence([bool]$Verified, [string]$Method, [int]$Attempts, [string]$Details) {
    if (-not $PackDir -or -not $EvidencePath -or -not (Test-Path $EvidenceTool)) { return }
    $python = Get-PythonCommand
    if (-not $python) {
        Write-Warning 'Python not found; fullscreen was checked but exact-build evidence could not be written.'
        return
    }
    $args = @()
    $args += $python.Prefix
    $args += @(
        $EvidenceTool, 'record', $PackDir, $EvidencePath,
        '--emulator', $exe.FullName,
        '--rom-name', (Split-Path -Leaf $RomPath),
        '--verified', $(if ($Verified) { 'true' } else { 'false' }),
        '--method', $Method,
        '--attempts', $Attempts,
        '--details', $Details
    )
    & $python.Exe @args | Out-Host
}

$exe = Get-ChildItem -Path $InstallDir -Filter 'Mesen.exe' -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $exe) {
    Write-Host 'MesenCE is not installed yet. Installing the latest official Windows build...' -ForegroundColor Yellow
    & $SetupScript -InstallDir $InstallDir
    $exe = Get-ChildItem -Path $InstallDir -Filter 'Mesen.exe' -File -Recurse | Select-Object -First 1
}
if (-not $exe) { throw 'Mesen.exe was not found after setup.' }

if ([string]::IsNullOrWhiteSpace($RomPath)) {
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
if ($PackDir) { $PackDir = (Resolve-Path $PackDir).Path }
if (-not $EvidencePath -and $PackDir) {
    $EvidencePath = Join-Path (Split-Path -Parent (Split-Path -Parent $PackDir)) 'Reports\FullscreenPlaytest\FULLSCREEN_PLAYTEST.json'
}

$sha1 = (Get-FileHash -Path $RomPath -Algorithm SHA1).Hash.ToLowerInvariant()
if ($sha1 -ne $ExpectedSha1 -and -not $AllowDifferentRom) {
    throw "This ROM does not match the Project #002 fingerprint. SHA-1: $sha1. Expected: $ExpectedSha1. Use -AllowDifferentRom only if you intentionally want to test another revision."
}

Write-Host ''
Write-Host '=== Tiny Toon Visual Remaster — Fullscreen MesenCE Playtest ===' -ForegroundColor Cyan
Write-Host 'Controls:' -ForegroundColor Cyan
Write-Host '  Arrow keys  = D-pad'
Write-Host '  Z           = NES A'
Write-Host '  X           = NES B'
Write-Host '  Enter       = Start'
Write-Host '  Right Shift = Select'
Write-Host '  F11         = Fullscreen toggle'
Write-Host '  Esc         = emulator/menu'
Write-Host ''
Write-Host 'The ROM is launched from its current location and is never copied.'
Write-Host 'Fullscreen is a required Project #002 playtest condition.' -ForegroundColor Yellow

$process = Start-Process -FilePath $exe.FullName -ArgumentList @('/fullscreen', $RomPath) -PassThru
$attempts = 1
if (-not (Wait-MainWindow $process $WindowTimeoutSeconds)) {
    Write-FullscreenEvidence $false 'commandline:/fullscreen' $attempts 'MesenCE did not expose a main window before timeout.'
    throw 'MesenCE did not expose a playable window before timeout.'
}

Start-Sleep -Milliseconds 700
$verified = Test-FullscreenWindow $process
$method = 'commandline:/fullscreen'

if (-not $verified) {
    $attempts = 2
    Write-Host 'Command-line fullscreen was not confirmed. Retrying with F11...' -ForegroundColor Yellow
    [Microsoft.VisualBasic.Interaction]::AppActivate($process.Id) | Out-Null
    [System.Windows.Forms.SendKeys]::SendWait('{F11}')
    Start-Sleep -Milliseconds 1200
    $verified = Test-FullscreenWindow $process
    $method = 'commandline:/fullscreen+F11-fallback'
}

if (-not $verified) {
    Write-FullscreenEvidence $false $method $attempts 'Window bounds did not match the active monitor after fullscreen attempts.'
    throw 'Fullscreen verification failed. Project #002 playtest is not accepted in windowed mode.'
}

Write-Host 'FULLSCREEN VERIFIED against active monitor bounds.' -ForegroundColor Green
Write-FullscreenEvidence $true $method $attempts 'Window bounds match active monitor bounds.'
Write-Host 'MesenCE is running with the local ROM. Continue the required in-game regression in Final Regression Cockpit.' -ForegroundColor Green
