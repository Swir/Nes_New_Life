param(
    [string]$ProjectRoot,
    [string]$RuntimePack,
    [switch]$NoOpen
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $ProjectRoot) { $ProjectRoot = Split-Path -Parent $Here }
$ProjectRoot = (Resolve-Path $ProjectRoot).Path
$Validator = Join-Path $ProjectRoot 'tools\validate_hdpack.py'

function Pick-Folder([string]$Description) {
    $d = New-Object System.Windows.Forms.FolderBrowserDialog
    $d.Description = $Description
    if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { return $d.SelectedPath }
    return $null
}
function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) { return @('py','-3') }
    if (Get-Command python -ErrorAction SilentlyContinue) { return @('python') }
    throw 'Python 3 was not found in PATH.'
}
function Invoke-Validator([string]$Pack) {
    $p = Get-PythonCommand
    $exe = $p[0]
    $args = @()
    if ($p.Count -gt 1) { $args += $p[1..($p.Count-1)] }
    $args += @($Validator, $Pack)
    $output = & $exe @args 2>&1
    return @{ Code = $LASTEXITCODE; Text = ($output -join "`n") }
}

if (-not $RuntimePack) { $RuntimePack = Pick-Folder 'Select the exact runtime HD pack with the MAPPING regression FAIL' }
if (-not $RuntimePack) { exit 2 }
$RuntimePack = (Resolve-Path $RuntimePack).Path
$Hires = Join-Path $RuntimePack 'hires.txt'
if (-not (Test-Path $Hires)) { throw 'Runtime pack must contain hires.txt.' }

$BackupRoot = Join-Path $env:LOCALAPPDATA 'Swir\TinyToonVisualRemaster\mapping-repair-backups'
New-Item -ItemType Directory -Force -Path $BackupRoot | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$Backup = Join-Path $BackupRoot ("hires-{0}.txt" -f $stamp)
Copy-Item -LiteralPath $Hires -Destination $Backup -Force
$BeforeHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $Hires).Hash

Write-Host ''
Write-Host '=== PROJECT #002 — REGRESSION MAPPING REPAIR WORKBENCH ===' -ForegroundColor Cyan
Write-Host ('Local backup: {0}' -f $Backup) -ForegroundColor DarkGray
Write-Host ('Original hires.txt SHA-256: {0}' -f $BeforeHash) -ForegroundColor DarkGray
$before = Invoke-Validator $RuntimePack
Write-Host ''
Write-Host 'PRE-EDIT HD PACK VALIDATION:' -ForegroundColor Yellow
Write-Host $before.Text
Write-Host ''
Write-Host 'Edit ONLY the mapping defect that produced the authoritative MAPPING FAIL.' -ForegroundColor Yellow
Write-Host 'Do not replace pixels to hide a mapping/provenance error.' -ForegroundColor Yellow
if (-not $NoOpen) { Start-Process notepad.exe $Hires }
[void](Read-Host 'After saving the mapping repair, press ENTER to validate the exact runtime pack')

$AfterHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $Hires).Hash
if ($AfterHash -eq $BeforeHash) {
    Write-Host 'hires.txt did not change. Mapping repair remains unresolved.' -ForegroundColor Red
    exit 3
}
$after = Invoke-Validator $RuntimePack
Write-Host ''
Write-Host 'POST-EDIT HD PACK VALIDATION:' -ForegroundColor Yellow
Write-Host $after.Text
if ($after.Code -ne 0) {
    Write-Host ''
    Write-Host 'Mapping repair is still invalid. Regression FAIL remains authoritative.' -ForegroundColor Red
    Write-Host ('Restore backup if needed: {0}' -f $Backup) -ForegroundColor Yellow
    exit $after.Code
}

Write-Host ''
Write-Host 'HD PACK STRUCTURAL VALIDATION: PASS' -ForegroundColor Green
Write-Host ('New hires.txt SHA-256: {0}' -f $AfterHash) -ForegroundColor DarkGray
Write-Host 'This does NOT clear the regression case. Re-run the exact failed case in verified-fullscreen MesenCE.' -ForegroundColor Yellow
exit 0
