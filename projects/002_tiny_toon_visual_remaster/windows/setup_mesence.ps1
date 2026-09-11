param(
    [switch]$Force,
    [string]$InstallDir
)

$ErrorActionPreference = 'Stop'
$ProjectDir = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($InstallDir)) {
    $InstallDir = Join-Path $ProjectDir 'vendor\MesenCE'
}

$exe = Get-ChildItem -Path $InstallDir -Filter 'Mesen.exe' -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
if ($exe -and -not $Force) {
    Write-Host "MesenCE is already installed: $($exe.FullName)" -ForegroundColor Green
    exit 0
}

Write-Host 'Reading latest MesenCE release from GitHub...' -ForegroundColor Cyan
$headers = @{ 'User-Agent' = 'NES-New-Life-Project-002' }
$release = Invoke-RestMethod -Uri 'https://api.github.com/repos/nesdev-org/MesenCE/releases/latest' -Headers $headers
$asset = $release.assets | Where-Object {
    $_.name -match '^Mesen_.*_Windows\.zip$' -and $_.name -notmatch 'Windows_7_And_8'
} | Select-Object -First 1

if (-not $asset) {
    throw 'Could not find the current Windows MesenCE ZIP in the latest official release.'
}

$tempRoot = Join-Path $env:TEMP ('nes-new-life-mesence-' + [Guid]::NewGuid().ToString('N'))
$tempZip = Join-Path $tempRoot $asset.name
New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null

try {
    Write-Host "Downloading MesenCE $($release.tag_name): $($asset.name)" -ForegroundColor Cyan
    Invoke-WebRequest -Uri $asset.browser_download_url -Headers $headers -OutFile $tempZip

    if ($asset.digest -and $asset.digest -match '^sha256:(.+)$') {
        $expected = $Matches[1].ToLowerInvariant()
        $actual = (Get-FileHash -Path $tempZip -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actual -ne $expected) {
            throw "MesenCE ZIP checksum mismatch. Expected $expected but got $actual."
        }
        Write-Host 'SHA-256 verification passed.' -ForegroundColor Green
    }

    if (Test-Path $InstallDir) {
        Remove-Item -Path $InstallDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    Expand-Archive -Path $tempZip -DestinationPath $InstallDir -Force

    $exe = Get-ChildItem -Path $InstallDir -Filter 'Mesen.exe' -File -Recurse | Select-Object -First 1
    if (-not $exe) {
        throw 'Mesen.exe was not found after extraction.'
    }

    Set-Content -Path (Join-Path $InstallDir 'MESENCE_VERSION.txt') -Value $release.tag_name -Encoding UTF8
    Write-Host "MesenCE $($release.tag_name) installed successfully." -ForegroundColor Green
    Write-Host "Executable: $($exe.FullName)"
}
finally {
    if (Test-Path $tempRoot) {
        Remove-Item -Path $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
