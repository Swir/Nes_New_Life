param(
    [string]$ProjectRoot,
    [string]$RuntimePack,
    [string]$RomPath,
    [switch]$RunAll,
    [switch]$NoOpen
)

$ErrorActionPreference = 'Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $ProjectRoot) { $ProjectRoot = Split-Path -Parent $Here }
$Tool = Join-Path $ProjectRoot 'tools\guided_regression_playtest.py'
$Locator = Join-Path $ProjectRoot 'tools\regression_defect_locator.py'
$VisualPicker = Join-Path $ProjectRoot 'tools\regression_visual_picker.py'
$RepairTool = Join-Path $ProjectRoot 'tools\regression_repair_sprint.py'
$Launcher = Join-Path $Here 'launch_remaster.ps1'
$Manifest = Join-Path $ProjectRoot 'FINAL_REGRESSION.json'
$Output = Join-Path $ProjectRoot 'Reports\GuidedRegressionPlaytest'
$PlanJson = Join-Path $Output 'GUIDED_REGRESSION_PLAYTEST.json'
$Dashboard = Join-Path $Output 'GUIDED_REGRESSION_PLAYTEST.html'
$LocatorOutput = Join-Path $ProjectRoot 'Reports\RegressionDefectLocator'
$LocatorPlanJson = Join-Path $LocatorOutput 'REGRESSION_DEFECT_TARGETS.json'
$VisualPickerHtml = Join-Path $LocatorOutput 'REGRESSION_VISUAL_PICKER_LOCAL_ONLY.html'
$RepairKit = Join-Path $ProjectRoot 'Artwork\CurrentRepairSprint'
$RepairDashboard = Join-Path $ProjectRoot 'Reports\RegressionRepairSprint\REGRESSION_REPAIR_SPRINT.html'
$StatePath = Join-Path $env:LOCALAPPDATA 'Swir\TinyToonVisualRemaster\capture-session.json'
$FullscreenEvidence = Join-Path $ProjectRoot 'Reports\FullscreenPlaytest\FULLSCREEN_PLAYTEST.json'

function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) { return @('py','-3') }
    if (Get-Command python -ErrorAction SilentlyContinue) { return @('python') }
    throw 'Python 3 was not found in PATH.'
}
function Pick-Folder([string]$Description) {
    Add-Type -AssemblyName System.Windows.Forms
    $d = New-Object System.Windows.Forms.FolderBrowserDialog
    $d.Description = $Description
    if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { return $d.SelectedPath }
    return $null
}
function Pick-Rom {
    Add-Type -AssemblyName System.Windows.Forms
    $d = New-Object System.Windows.Forms.OpenFileDialog
    $d.Title = 'Select the local Tiny Toon NES ROM — remains local'
    $d.Filter = 'NES ROM (*.nes)|*.nes|All files (*.*)|*.*'
    if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { return $d.FileName }
    return $null
}
function Invoke-PythonJson([string[]]$Arguments) {
    $p = Get-PythonCommand
    $exe = $p[0]
    $all = @()
    if ($p.Count -gt 1) { $all += $p[1..($p.Count-1)] }
    $all += $Arguments
    $raw = & $exe @all
    if ($LASTEXITCODE -ne 0) { throw "Python command failed with exit code $LASTEXITCODE" }
    return (($raw -join "`n") | ConvertFrom-Json)
}
function Select-DefectTarget($Case, [string]$Category) {
    $artCategories = @('MISSING_HD','WRONG_PALETTE','ANIMATION_SEAM','TRANSPARENCY','OTHER')
    if ($Category -notin $artCategories) { return $null }
    try {
        New-Item -ItemType Directory -Force -Path $LocatorOutput | Out-Null
        $planned = Invoke-PythonJson @($Locator, 'plan', $ProjectRoot, $RuntimePack, $Case.key, $Category, '--output', $LocatorOutput, '--top', '12')
        $candidates = @($planned.plan.candidates)
        if ($candidates.Count -eq 0) {
            Write-Host 'Defect locator found no safe metadata candidates; continue with descriptive failure notes.' -ForegroundColor Yellow
            return $null
        }

        $visual = Invoke-PythonJson @($VisualPicker, $LocatorPlanJson, $RuntimePack, '--output', $LocatorOutput, '--variants', '4')
        if ($visual.contains_rom_derived_pixels -ne $true) { throw 'Visual picker did not declare its local ROM-derived pixel policy.' }
        Write-Host ''
        Write-Host 'VISUAL DEFECT PICKER READY — inspect the numbered local tile previews.' -ForegroundColor Magenta
        Write-Host ('Local-only board: {0}' -f $VisualPickerHtml) -ForegroundColor DarkGray
        Write-Host 'The board is under gitignored Reports/ and must never be committed or uploaded.' -ForegroundColor Yellow
        if (-not $NoOpen -and (Test-Path $VisualPickerHtml)) { Start-Process $VisualPickerHtml }

        Write-Host ''
        Write-Host 'DEFECT TARGET LOCATOR — choose the visible tile/palette if one matches what you saw:' -ForegroundColor Magenta
        foreach ($candidate in $candidates) {
            $family = if ($candidate.family) { $candidate.family } else { '—' }
            $conditions = (@($candidate.conditions) -join ', ')
            if (-not $conditions) { $conditions = '—' }
            Write-Host ('  {0}. [{1}] tile={2} palette={3} score={4} uses={5} family={6}' -f $candidate.rank, $candidate.group, $candidate.tile_id, $candidate.palette, $candidate.score, $candidate.uses, $family)
            Write-Host ('     contexts: {0}' -f $conditions) -ForegroundColor DarkGray
        }
        Write-Host '  0. Unknown / none of these — keep descriptive FAIL only' -ForegroundColor DarkGray
        $targetNumber = -1
        while ($targetNumber -lt 0 -or $targetNumber -gt $candidates.Count) {
            [void][int]::TryParse((Read-Host 'Choose target number shown on the visual board'), [ref]$targetNumber)
        }
        if ($targetNumber -eq 0) { return $null }
        $chosen = Invoke-PythonJson @($Locator, 'choose', $LocatorPlanJson, [string]$targetNumber, '--output', $LocatorOutput)
        Write-Host ('TARGET LOCKED: {0} / {1}' -f $chosen.selection.target_tag, $chosen.selection.context_note) -ForegroundColor Green
        return $chosen.selection
    } catch {
        Write-Host ('Defect locator could not narrow the target: {0}' -f $_.Exception.Message) -ForegroundColor Yellow
        Write-Host 'The FAIL can still be recorded safely with descriptive notes.' -ForegroundColor Yellow
        return $null
    }
}
function Start-RepairHandoff($Case, [string]$Category, $Target) {
    $artCategories = @('MISSING_HD','WRONG_PALETTE','ANIMATION_SEAM','TRANSPARENCY','OTHER')
    if ($Category -notin $artCategories) { return $null }
    try {
        $prepared = Invoke-PythonJson @($RepairTool, 'prepare', $ProjectRoot, $RuntimePack)
        if ($prepared.status -ne 'REPAIR_SPRINT_READY') {
            Write-Host ('Automatic repair handoff did not create a sprint: {0}' -f $prepared.status) -ForegroundColor Yellow
            if ($prepared.next_action) { Write-Host $prepared.next_action -ForegroundColor Yellow }
            return $prepared
        }

        $editable = Join-Path $RepairKit 'editable'
        $generalBoard = $null
        if ($prepared.local_board) { $generalBoard = Join-Path $RepairKit ([string]$prepared.local_board) }
        $familyBoard = $null
        $familyManifestPath = Join-Path $RepairKit 'FAMILY_CONTACT_BOARDS.json'
        if (Test-Path $familyManifestPath) {
            try {
                $familyManifest = Get-Content -Raw $familyManifestPath | ConvertFrom-Json
                $families = @($familyManifest.families)
                if ($families.Count -gt 0) {
                    $match = $null
                    if ($Target -and $Target.family) {
                        $wantedFamily = [string]$Target.family
                        $match = $families | Where-Object { [string]$_.family -eq $wantedFamily } | Select-Object -First 1
                    }
                    if (-not $match) { $match = $families[0] }
                    if ($match.file) { $familyBoard = Join-Path $RepairKit ([string]$match.file) }
                }
            } catch {
                Write-Host ('Family board lookup skipped: {0}' -f $_.Exception.Message) -ForegroundColor DarkYellow
            }
        }

        Write-Host ''
        Write-Host 'AUTOMATIC REPAIR HANDOFF READY.' -ForegroundColor Green
        Write-Host ('Prepared {0} minimal repair item(s) for {1}.' -f $prepared.repair_items, $Case.label) -ForegroundColor Cyan
        if ($Target) { Write-Host ('Locked target: {0}' -f $Target.target_tag) -ForegroundColor Magenta }
        Write-Host 'Edit only CurrentRepairSprint\editable, then run Regression_Repair_Loop.bat to finish transactional QA + same-case retest.' -ForegroundColor Yellow
        if (-not $NoOpen) {
            if ($familyBoard -and (Test-Path $familyBoard)) { Start-Process $familyBoard }
            elseif ($generalBoard -and (Test-Path $generalBoard)) { Start-Process $generalBoard }
            if (Test-Path $editable) { Start-Process explorer.exe $editable }
        }
        return $prepared
    } catch {
        Write-Host ('Automatic repair handoff could not prepare CurrentRepairSprint: {0}' -f $_.Exception.Message) -ForegroundColor Yellow
        Write-Host 'The authoritative FAIL is safely recorded. Run Regression_Repair_Loop.bat after resolving any existing repair sprint/blocker.' -ForegroundColor Yellow
        if (-not $NoOpen -and (Test-Path $RepairDashboard)) { Start-Process $RepairDashboard }
        return $null
    }
}

if (-not $RuntimePack) {
    $candidate = Join-Path $ProjectRoot 'Build\HighImpactCandidate'
    $playtest = Join-Path $ProjectRoot 'ModernizedPack\playtest_current'
    if (Test-Path (Join-Path $candidate 'hires.txt')) { $RuntimePack = $candidate }
    elseif (Test-Path (Join-Path $playtest 'hires.txt')) { $RuntimePack = $playtest }
    else { $RuntimePack = Pick-Folder 'Select exact runtime HD pack for final regression' }
}
if (-not $RuntimePack) { exit 2 }
$RuntimePack = (Resolve-Path $RuntimePack).Path
if (-not (Test-Path (Join-Path $RuntimePack 'hires.txt'))) { throw 'Runtime pack must contain hires.txt.' }

if (-not $RomPath -and (Test-Path $StatePath)) {
    try {
        $state = Get-Content -Raw $StatePath | ConvertFrom-Json
        if ($state.rom_path -and (Test-Path $state.rom_path)) { $RomPath = $state.rom_path }
    } catch {}
}
if (-not $RomPath) { $RomPath = Pick-Rom }
if (-not $RomPath) { exit 2 }
$RomPath = (Resolve-Path $RomPath).Path

New-Item -ItemType Directory -Force -Path $Output | Out-Null
Write-Host ''
Write-Host '=== PROJECT #002 — GUIDED EXACT-BUILD REGRESSION PLAYTEST ===' -ForegroundColor Cyan
Write-Host 'Every PASS/FAIL is manual evidence from the exact current runtime fingerprint.' -ForegroundColor Yellow
Write-Host 'No case can auto-PASS. FAIL is routed before any pending/stale case.'
Write-Host 'Art-related FAILs now open the visual picker and auto-prepare the minimal repair sprint.' -ForegroundColor DarkGray

while ($true) {
    $plan = Invoke-PythonJson @($Tool, 'plan', $Manifest, $RuntimePack, '--output', $Output)
    $session = $plan.session
    if ($session.state -eq 'REGRESSION_COMPLETE') {
        Write-Host ''
        Write-Host 'FINAL REGRESSION: 10/10 PASS for this exact build.' -ForegroundColor Green
        Write-Host 'DO THIS NEXT: Final Release Gate.' -ForegroundColor Green
        break
    }

    $case = $session.next_case
    Write-Host ''
    Write-Host ('CASE {0}/10 — {1}' -f $case.order, $case.label) -ForegroundColor Cyan
    Write-Host ('Key: {0} | prior state: {1}' -f $case.key, $case.prior_state) -ForegroundColor DarkGray
    if ($case.prior_state -eq 'FAIL') {
        Write-Host ('Existing defect: {0} — {1}' -f $case.failure_category, $case.failure_notes) -ForegroundColor Red
        Write-Host $session.next_action -ForegroundColor Yellow
        Write-Host 'Repair/rebuild first. The guided runner will not overwrite a known FAIL with an unverified result.' -ForegroundColor Yellow
        if (-not $NoOpen -and (Test-Path $Dashboard)) { Start-Process $Dashboard }
        break
    }
    Write-Host ('ROUTE: {0}' -f $case.route) -ForegroundColor White
    foreach ($cue in @($case.cues)) { Write-Host ('  - {0}' -f $cue) }
    Write-Host ''
    Write-Host 'Launching this exact build through verified-fullscreen MesenCE...' -ForegroundColor Yellow
    & $Launcher -RomPath $RomPath -PackDir $RuntimePack -EvidencePath $FullscreenEvidence
    if ($LASTEXITCODE -ne 0) { throw 'Verified fullscreen MesenCE launch failed; regression evidence was not recorded.' }

    [void](Read-Host 'Perform ONLY the case above in MesenCE. Return here and press ENTER when observation is complete')
    $choice = ''
    while ($choice -notin @('P','F')) {
        $choice = (Read-Host 'P = PASS after real visual verification; F = FAIL and classify defect').Trim().ToUpperInvariant()
    }
    if ($choice -eq 'P') {
        $note = Read-Host 'Optional PASS notes (ENTER for none)'
        $record = Invoke-PythonJson @($Tool, 'record', $Manifest, $RuntimePack, $case.key, 'PASS', '--notes', $note, '--output', $Output)
        Write-Host ('RECORDED PASS: {0}' -f $case.key) -ForegroundColor Green
    } else {
        $categories = @('MISSING_HD','WRONG_PALETTE','ANIMATION_SEAM','TRANSPARENCY','MAPPING','SCALE_OR_FILTER','CAPTURE_GAP','OTHER')
        Write-Host 'Failure categories:' -ForegroundColor Red
        for ($i=0; $i -lt $categories.Count; $i++) { Write-Host ('  {0}. {1}' -f ($i+1), $categories[$i]) }
        $number = 0
        while ($number -lt 1 -or $number -gt $categories.Count) {
            [void][int]::TryParse((Read-Host 'Choose failure category number'), [ref]$number)
        }
        $category = $categories[$number-1]
        $target = Select-DefectTarget $case $category
        $failure = Read-Host 'Describe the visible defect / exact location or state'
        if ($target) {
            $failure = (($failure.Trim() + ' ' + $target.target_tag + ' | ' + $target.context_note).Trim())
        }
        $notes = Read-Host 'Optional additional notes (ENTER for none)'
        $record = Invoke-PythonJson @($Tool, 'record', $Manifest, $RuntimePack, $case.key, 'FAIL', '--category', $category, '--failure-notes', $failure, '--notes', $notes, '--output', $Output)
        Write-Host ('RECORDED FAIL: {0} / {1}' -f $case.key, $category) -ForegroundColor Red
        if ($target) { Write-Host ('Repair target: {0}' -f $target.target_tag) -ForegroundColor Magenta }
        Write-Host $record.session.next_action -ForegroundColor Yellow
        [void](Start-RepairHandoff $case $category $target)
        break
    }

    if (-not $RunAll) {
        Write-Host ('Next case prepared: {0}' -f $record.session.next_case.label) -ForegroundColor Cyan
        break
    }
}

if (-not $NoOpen -and (Test-Path $Dashboard)) { Start-Process $Dashboard }
