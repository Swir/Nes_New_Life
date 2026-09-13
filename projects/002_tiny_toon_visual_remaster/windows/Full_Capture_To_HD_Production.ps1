param(
    [string]$RomPath,
    [string]$CurrentCapture,
    [string]$PreviousCapture,
    [switch]$CreateSprint,
    [switch]$SkipGameplay
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Marathon = Join-Path $PSScriptRoot 'Guided_Capture_Marathon.ps1'
$Production = Join-Path $PSScriptRoot 'Capture_To_Art_Pipeline.ps1'
$DirectorJson = Join-Path $ProjectRoot 'Reports\CaptureProductionDirector\CAPTURE_PRODUCTION_DIRECTOR.json'
$DirectorHtml = Join-Path $ProjectRoot 'Reports\CaptureProductionDirector\CAPTURE_PRODUCTION_DIRECTOR.html'
$SessionDir = Join-Path $ProjectRoot 'Reports\CaptureToHDSession'
$SessionJson = Join-Path $SessionDir 'CAPTURE_TO_HD_SESSION.json'
$SessionHtml = Join-Path $SessionDir 'CAPTURE_TO_HD_SESSION.html'

function Select-Folder([string]$Description) {
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = $Description
    if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { return $dialog.SelectedPath }
    return $null
}

function Select-Rom {
    $dialog = New-Object System.Windows.Forms.OpenFileDialog
    $dialog.Title = 'Select Tiny Toon Adventures NES ROM - stays local'
    $dialog.Filter = 'NES ROM (*.nes)|*.nes|All files (*.*)|*.*'
    $dialog.Multiselect = $false
    if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { return $dialog.FileName }
    return $null
}

function ConvertTo-HtmlSafe([object]$Value) {
    return [System.Net.WebUtility]::HtmlEncode([string]$Value)
}

if (-not $CurrentCapture) { $CurrentCapture = Select-Folder 'Select CURRENT MesenCE HD Pack capture folder' }
if (-not $CurrentCapture) { exit 2 }
$CurrentCapture = (Resolve-Path $CurrentCapture).Path
if (-not (Test-Path (Join-Path $CurrentCapture 'hires.txt'))) { throw 'Current capture must contain hires.txt.' }

if (-not $SkipGameplay) {
    if (-not $RomPath) { $RomPath = Select-Rom }
    if (-not $RomPath) { exit 2 }
    $RomPath = (Resolve-Path $RomPath).Path
}

if (-not $PreviousCapture) {
    $compare = [System.Windows.Forms.MessageBox]::Show(
        'Do you have a previous accepted capture for regression comparison? Recommended when available.',
        'Project #002 Full Capture -> HD Production',
        [System.Windows.Forms.MessageBoxButtons]::YesNo,
        [System.Windows.Forms.MessageBoxIcon]::Question
    )
    if ($compare -eq [System.Windows.Forms.DialogResult]::Yes) {
        $PreviousCapture = Select-Folder 'Select PREVIOUS accepted MesenCE capture'
    }
}
if ($PreviousCapture) { $PreviousCapture = (Resolve-Path $PreviousCapture).Path }

New-Item -ItemType Directory -Force -Path $SessionDir | Out-Null

Write-Host ''
Write-Host '=== PROJECT #002 - FULL CAPTURE -> HD PRODUCTION ===' -ForegroundColor Cyan
Write-Host 'One authoritative path: gameplay capture -> safe bridge -> fingerprint acceptance -> guarded production.' -ForegroundColor Yellow
Write-Host 'No Gate A-D checkbox is changed by this workflow.'
Write-Host 'ROM, save states, capture pixels and emulator binaries remain local.'
Write-Host ''

$MarathonRc = 0
if (-not $SkipGameplay) {
    $marathonArgs = @('-RomPath', $RomPath, '-CurrentCapture', $CurrentCapture, '-NoGitHubPrompt')
    if ($PreviousCapture) { $marathonArgs += @('-PreviousCapture', $PreviousCapture) }

    & $Marathon @marathonArgs
    $MarathonRc = $LASTEXITCODE
    if ($MarathonRc -ne 0) {
        Write-Host ''
        Write-Host ("CAPTURE STAGE STOPPED with exit code {0}. Production will NOT run." -f $MarathonRc) -ForegroundColor Red
        exit $MarathonRc
    }
} else {
    Write-Host 'Gameplay stage skipped by explicit -SkipGameplay. Existing local capture will still be fully revalidated.' -ForegroundColor Yellow
}

Write-Host ''
Write-Host 'Capture stage finished. Running fingerprint-bound acceptance and guarded production...' -ForegroundColor Cyan
$productionArgs = @('-CurrentCapture', $CurrentCapture)
if ($PreviousCapture) { $productionArgs += @('-PreviousCapture', $PreviousCapture) }
if ($CreateSprint) { $productionArgs += '-CreateSprint' }

& $Production @productionArgs
$ProductionRc = $LASTEXITCODE
if ($ProductionRc -notin @(0, 3)) { throw "Capture -> Art pipeline failed with exit code $ProductionRc" }
if (-not (Test-Path $DirectorJson)) { throw 'Capture Production Director did not create its decision JSON.' }

$Director = Get-Content -Raw -Path $DirectorJson | ConvertFrom-Json
$CaptureDecision = [string]$Director.decision.capture_decision
$ProductionDecision = [string]$Director.decision.production_decision
$NextAction = [string]$Director.decision.next_action
$Fingerprint = [string]$Director.acceptance.capture_fingerprint_sha256
$AcceptanceGate = [string]$Director.acceptance.acceptance_gate
$PromotionGate = if ($null -ne $Director.promotion) { [string]$Director.promotion.promotion_gate } else { 'NOT_RUN' }
$Pending = [int]$Director.acceptance.mission_summary.pending
$Verified = [int]$Director.acceptance.mission_summary.verified
$Total = [int]$Director.acceptance.mission_summary.total

$Session = [ordered]@{
    schema = 'swir.project002.capture-to-hd-session.v1'
    generated_utc = [DateTime]::UtcNow.ToString('o')
    gameplay_stage = if ($SkipGameplay) { 'SKIPPED_EXPLICITLY' } else { 'COMPLETED' }
    capture_decision = $CaptureDecision
    production_decision = $ProductionDecision
    acceptance_gate = $AcceptanceGate
    promotion_gate = $PromotionGate
    capture_fingerprint_sha256 = $Fingerprint
    missions = [ordered]@{ verified = $Verified; pending = $Pending; total = $Total }
    next_action = $NextAction
    create_sprint_requested = [bool]$CreateSprint
    roadmap_policy = 'Metadata and tooling never auto-complete Gate A-D.'
    privacy_contract = [ordered]@{
        metadata_only = $true
        rom_bytes = $false
        save_states = $false
        capture_pixels = $false
        emulator_binaries = $false
        absolute_local_paths = $false
    }
}
$Session | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -Path $SessionJson

$decisionClass = if ($ProductionDecision -eq 'BLOCK_PRODUCTION') { 'bad' } elseif ($CaptureDecision -eq 'READY_FOR_GATE_A_REVIEW') { 'ok' } else { 'warn' }
$html = @"
<!doctype html><html lang='en'><head><meta charset='utf-8'><title>Project #002 Capture to HD Session</title>
<style>body{font:15px system-ui;max-width:1000px;margin:30px auto;padding:0 22px;background:#0d1117;color:#e6edf3}.card{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:16px;margin:12px 0}.ok{color:#3fb950}.warn{color:#d29922}.bad{color:#f85149}code{color:#79c0ff;word-break:break-all}</style></head><body>
<h1>Project #002 - Capture -> HD Production Session</h1>
<div class='card'><h2 class='$decisionClass'>$(ConvertTo-HtmlSafe $CaptureDecision)</h2>
<p>Production: <b>$(ConvertTo-HtmlSafe $ProductionDecision)</b></p>
<p>Acceptance: <b>$(ConvertTo-HtmlSafe $AcceptanceGate)</b> | Promotion: <b>$(ConvertTo-HtmlSafe $PromotionGate)</b></p>
<p>Missions: <b>$Verified/$Total</b> verified; <b>$Pending</b> pending</p>
<p>Fingerprint: <code>$(ConvertTo-HtmlSafe $Fingerprint)</code></p>
<p><b>DO THIS NEXT:</b> $(ConvertTo-HtmlSafe $NextAction)</p></div>
<div class='card'><p>Metadata-only session summary. No ROM bytes, save states, capture pixels, emulator binaries or absolute local paths are stored here.</p><p>This workflow never edits ROADMAP Gate A-D.</p></div>
</body></html>
"@
Set-Content -Encoding UTF8 -Path $SessionHtml -Value $html

Write-Host ''
Write-Host '=== AUTHORITATIVE SESSION RESULT ===' -ForegroundColor Cyan
Write-Host ("Capture decision:    {0}" -f $CaptureDecision)
Write-Host ("Production decision: {0}" -f $ProductionDecision)
Write-Host ("Acceptance gate:     {0}" -f $AcceptanceGate)
Write-Host ("Promotion gate:      {0}" -f $PromotionGate)
Write-Host ("Missions:            {0}/{1} verified; {2} pending" -f $Verified, $Total, $Pending)
Write-Host ("Fingerprint:         {0}" -f $Fingerprint)
Write-Host ("DO THIS NEXT:         {0}" -f $NextAction) -ForegroundColor Yellow

if (Test-Path $SessionHtml) { Start-Process $SessionHtml }
elseif (Test-Path $DirectorHtml) { Start-Process $DirectorHtml }

if ($ProductionDecision -eq 'BLOCK_PRODUCTION') {
    Write-Host 'SESSION BLOCKED: unsafe capture evidence was not allowed to mutate production state.' -ForegroundColor Red
    exit 3
}

Write-Host 'SESSION COMPLETE: all allowed safe work was routed automatically.' -ForegroundColor Green
exit 0
