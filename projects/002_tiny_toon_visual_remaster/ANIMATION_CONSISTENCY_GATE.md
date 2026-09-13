# Project #002 — Animation Family Consistency Gate

`animation_consistency_gate.py` adds a fail-closed family-level quality check for staged **PLAYER / ENEMY / BOSS** redraws before they can enter the authoritative HD Pack.

The existing master-tile visual gate catches catastrophic mistakes inside one PNG. This gate adds the missing context check: a single technically valid redraw can still look wrong when placed beside neighboring animation frames or palette variants.

## What it checks

The gate derives semantic animation families from the existing Mesen condition metadata used by Animation Workbench. For every changed character master it compares staged geometry against peer frames in the same family.

Blocking signals are intentionally conservative and limited to catastrophic consistency failures:

- normalized bounding-box width below 45% or above 220% of the family median,
- normalized bounding-box height below 45% or above 220% of the family median,
- visible alpha coverage below 30% or above 320% of the family median,
- normalized canvas-center jump greater than 0.34,
- fully transparent changed frame,
- same tile ID across palette variants with best alpha-mask IoU below 0.32.

Extreme detail-density and visible-color-count differences are recorded as warnings instead of blockers because a legitimate HD redesign may intentionally add detail or richer color.

## Full-family redraws

When every detected peer frame in a family is changed in the same transaction, the gate compares each changed frame against the staged family median. It does not force a new coherent redraw to resemble the old NES pixels.

## Scope

WORLD, UI and EFFECTS are deliberately excluded from family geometry blocking because their animated elements may legitimately expand, wipe, scroll or occupy radically different regions of the canvas. Their individual redraw safety remains covered by the master-tile visual gate and Pixel QA.

## Transaction order

The authoritative art finish is now:

`stale check → staged import → master visual gate → animation consistency gate → candidate composition → hires.txt preservation → Pixel QA → second stale check → atomic commit / rollback`

A family failure returns `BLOCKED_ANIMATION_CONSISTENCY`. Candidate-pack composition is not attempted and neither the real `MasterWorkspace` nor the current runtime pack is modified.

## Metadata-only output

Each transaction writes:

`ART_ANIMATION_CONSISTENCY_GATE.json`

The report contains only family names, master filenames, normalized ratios, blocker/warning codes and summary counters. It never serializes ROM bytes, save states, image pixels, emulator binaries or absolute local paths.

## Relationship to Animation Workbench

Both systems share the same semantic-family concept derived from condition names. Animation Workbench remains the human review surface and can generate local contact sheets. The consistency gate is narrower: it automatically blocks only catastrophic geometry/silhouette outliers that are unsafe to commit without repair.

## ROADMAP policy

Passing this gate improves production safety but does not complete any Gate A–D checkbox by itself. Real local art evidence plus exact-build QA/gameplay verification is still required for ROADMAP progress.
