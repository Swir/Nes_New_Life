param(
    [string]$RomPath,
    [string]$CurrentCapture,
    [string]$PreviousCapture,
    [switch]$NoGitHubPrompt,
    [switch]$ForgetSavedPaths
)

$ErrorActionPreference = 'Stop'
$SingleSession = Join-Path $PSScriptRoot 'Capture_Single_Best_Session.ps1'

$singleArgs = @{}
if ($RomPath) { $singleArgs['RomPath'] = $RomPath }
if ($CurrentCapture) { $singleArgs['CurrentCapture'] = $CurrentCapture }
if ($PreviousCapture) { $singleArgs['PreviousCapture'] = $PreviousCapture }
if ($NoGitHubPrompt) { $singleArgs['NoGitHubPrompt'] = $true }
if ($ForgetSavedPaths) { $singleArgs['ForgetSavedPaths'] = $true }

Write-Host ''
Write-Host '=== PROJECT #002 — NEXT-BEST CAPTURE LOOP ===' -ForegroundColor Cyan
Write-Host 'Runs exactly one highest-impact route-aware fullscreen MesenCE pass per invocation.' -ForegroundColor Yellow
Write-Host 'Local ROM/capture paths are reused from LOCALAPPDATA after the first run.'
Write-Host 'After the pass: integrity + gap + route + safe evidence + acceptance + next action are refreshed automatically.'
Write-Host 'No mission or ROADMAP checkbox is completed automatically.'
Write-Host ''

& $SingleSession @singleArgs
exit $LASTEXITCODE
