# Capture Coverage Acceptance Manifest

`capture_coverage_acceptance.py` is the final metadata/provenance checkpoint between a local Guided Capture Marathon session and manual Gate A review.

It exists to answer one practical question without pretending that GitHub can see the user's game: **is the local capture structurally and evidentially strong enough to deserve human Gate A review?**

## What it binds together

The manifest joins the current Capture Integrity Ledger fingerprint with:

- all eleven authoritative Capture Mission Control missions,
- the source session and SHA-256 fingerprint for every completed mission,
- explicit `VERIFIED_IN_GAME` provenance,
- current structural regression / at-risk mission state,
- PLAYER / BOSS / ENEMY / WORLD / UI / EFFECTS / UNASSIGNED mapping counts,
- animation-family counts and advisory missing-state signals,
- current mapping / tile / palette / condition / referenced-image counts.

The output is deliberately metadata-only. It does not copy ROM bytes, save states, screenshots, capture PNG/JPG pixels, emulator binaries, commercial art/audio or absolute local paths.

## Acceptance semantics

There are only two top-level states:

- `BLOCKED` — one or more hard capture/provenance checks are not satisfied.
- `READY_FOR_GATE_A_REVIEW` — the hard metadata/provenance checks are clean, but a human still has to review the real local MesenCE gameplay evidence before changing any ROADMAP checkbox.

`READY_FOR_GATE_A_REVIEW` is **not** a release PASS and never changes Gate A–D automatically.

Hard blockers include:

1. Capture Integrity Ledger admission is not `PASS`.
2. Structural blockers, capture regressions or at-risk verified missions remain.
3. One or more authoritative capture missions are still pending.
4. A completed mission lacks fingerprint-bound `VERIFIED_IN_GAME` provenance.
5. A required production group (PLAYER, BOSS, ENEMY, WORLD, UI or EFFECTS) has no captured mapping signal.

Generic PLAYER/BOSS/ENEMY missing-state vocabulary remains advisory. It is useful for finding likely holes, but it is not proof that a specific state exists in Tiny Toon Adventures.

## Outputs

By default the Windows flow writes:

```text
Reports/CaptureCoverageAcceptance/
  CAPTURE_COVERAGE_ACCEPTANCE.json
  CAPTURE_COVERAGE_MATRIX.csv
  CAPTURE_COVERAGE_ACCEPTANCE.html
```

The JSON is the machine-readable acceptance manifest. The CSV provides a compact mission/group matrix. The HTML dashboard shows hard blockers, mission provenance, structural group coverage and one ordered **DO THIS NEXT** action.

## Windows one-click

Run:

```text
windows/Capture_Coverage_Acceptance.bat
```

Select the local Project #002 workspace and the current MesenCE HD Pack capture. The launcher opens the generated dashboard automatically.

Optional scripted usage:

```powershell
powershell -ExecutionPolicy Bypass -File windows/Capture_Coverage_Acceptance.ps1 `
  -ProjectRoot C:\Local\TinyToonWorkspace `
  -Capture C:\Local\MesenCapture `
  -PreviousCapture C:\Local\PreviousAcceptedCapture
```

## CLI

```bash
python tools/capture_coverage_acceptance.py \
  /local/project002-workspace \
  /local/current-mesen-capture \
  --previous-capture /local/previous-accepted-capture \
  --output /local/reports/CaptureCoverageAcceptance
```

Exit code `0` means `READY_FOR_GATE_A_REVIEW`; exit code `2` means `BLOCKED`. Neither result edits the ROADMAP.

## Why this improves the HD workflow

Earlier tools could independently show mission completion, capture structure, regression history and group counts. This manifest makes them one fingerprint-bound acceptance decision, so the next local capture session can focus directly on the exact blocking mission/group/provenance gap instead of manually reconciling several reports.

The original ROM in MesenCE remains the authoritative source of gameplay, physics, timing, routes and visual occurrence. This repository only automates safe metadata handling and HD production around that local source.
