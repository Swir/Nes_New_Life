# Project #002 — HD Art Autopilot

`windows/Full_Capture_To_HD_Autopilot.bat` is the highest-level safe local workflow for moving a real MesenCE gameplay capture into the next exact 4x art batch.

## Authoritative chain

```text
Guided Capture Marathon
  -> Local Capture Bridge
  -> fingerprint-bound Capture Coverage Acceptance
  -> guarded Capture Promotion
  -> Visual Completion Matrix
  -> exact NEXT_HIGH_IMPACT_ART_BATCH
  -> CurrentImpactSprint
  -> QA-gated finish / Pixel QA
```

The launcher reuses `Full_Capture_To_HD_Production.ps1` for gameplay, evidence, acceptance and promotion. It only enters the HD art stage after that pipeline returns a safe production result.

## Fail-closed rules

`hd_art_autopilot.py` refuses to prepare art when:

- the current `hires.txt + referenced PNG` fingerprint differs from the fingerprint accepted by Capture Production Director,
- production is `BLOCK_PRODUCTION`,
- the candidate was not actually `PROMOTED`,
- guarded promotion did not create a valid `MasterWorkspace`.

An existing `Artwork/CurrentImpactSprint` is **never overwritten automatically**. The workflow returns `RESUME_EXISTING_SPRINT` so unfinished artist work remains intact.

## Exact high-impact selection

For safe `SAFE_INCREMENTAL_ART` and `FULL_CAPTURE_READY` states, the autopilot builds a fresh Visual Completion Matrix against the exact current capture and authoritative `MasterWorkspace`. If captured unfinished art exists, it exports the matrix's exact `next_batch` through `prepare_high_impact_sprint(...)`.

This removes the older mismatch where a legacy Top-N priority export could differ from the Visual Completion Matrix batch. PLAYER/BOSS/ENEMY, invalid, high-reuse and classification blockers keep the matrix's production weighting.

If the matrix has no next batch, the state is `CAPTURED_ART_COMPLETE`. This means only that currently captured art has no remaining batch. It **does not** prove whole-game capture, Gate A, QA, regression or release completion.

## Outputs

Local outputs are written under:

- `Reports/HDArtAutopilot/HD_ART_AUTOPILOT.json`
- `Reports/HDArtAutopilot/HD_ART_AUTOPILOT.html`
- `Reports/VisualCompletion/`
- `Artwork/CurrentImpactSprint/` when a new exact batch is prepared

The committed tool/report contract is metadata-only. ROM bytes, save states, capture pixels, emulator binaries, absolute local paths and local derivative art are not intended for Git.

## ROADMAP rule

This automation never modifies Gate A–D checkboxes. Project #002 remains governed only by real local capture/art/QA evidence and the authoritative 52-item release checklist.
