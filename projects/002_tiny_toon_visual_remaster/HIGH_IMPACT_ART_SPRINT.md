# High-Impact Art Sprint — Project #002

This workflow turns the Visual Completion Matrix from a ranking report into an immediately editable, **family-aware** production batch.

## What it does

`tools/high_impact_art_sprint.py prepare` runs the current Visual Completion Matrix and uses its `NEXT_HIGH_IMPACT_ART_BATCH` as the seed ranking. For PLAYER / ENEMY / BOSS seeds it then expands the seed to unfinished masters that belong to the same semantic animation family and to unfinished palette siblings of the same tile.

This closes a production-quality gap: a single high-impact character frame is no longer routinely redrawn in isolation while neighboring walk/run/jump/attack frames or palette variants wait for a later sprint.

The planner follows four rules:

1. the Visual Completion Matrix remains the source of priority;
2. already-final masters are never reopened automatically;
3. a selected character family is atomic — it is not split merely to satisfy the nominal batch size;
4. if the first highest-impact family is larger than the requested batch, that one family may overflow the nominal size, while later families that do not fit are deferred as complete units.

WORLD / UI / EFFECTS keep normal item-by-item high-impact selection because those graphics may legitimately have unrelated geometry even when conditions are nearby.

## Outputs

The report directory now contains both:

- `NEXT_HIGH_IMPACT_ART_BATCH.csv` — the original Visual Completion Matrix seed ranking;
- `FAMILY_AWARE_ART_BATCH.json` / `.csv` — the exact family-aware execution plan used by the sprint.

The local kit contains:

- `editable/` — files the artist is allowed to redraw,
- `reference/` — untouched local baseline copies,
- `LOCAL_ART_SPRINT_BOARD.png` — local contact board,
- `ART_SPRINT_KIT.json` schema 3 — dimensions, hashes, seed relation, family bundles, deferred families and impact scores,
- `HIGH_IMPACT_SPRINT_READY.json` — metadata-only handoff status.

The board and PNG content are local derivative/capture material and must never be committed.

## Windows one-click

Run `windows/High_Impact_Art_Sprint.bat` to select the current local capture/pack, generate the completion report and family-aware batch, create `Artwork/CurrentImpactSprint`, and open the dashboard, board and editable folder.

After editing the PNGs without resizing or renaming them, run `windows/Finish_High_Impact_Art_Sprint.bat`.

## QA-gated finish

Finish uses the transactional art path:

`stale check → staged import → master visual QA → animation-family consistency QA → candidate HD Pack → hires.txt preservation → Pixel QA → second stale check → atomic commit / rollback`

A bad family redraw cannot partially poison `MasterWorkspace`. Family geometry/silhouette failures, master visual failures, Pixel QA failures, mapping changes and stale-workspace conflicts all block before the authoritative local production state is replaced.

## Safety boundaries

This workflow never supplies or commits a ROM, emulator binary, save state, captured graphics or ripped commercial assets. The ROM remains the local gameplay source in MesenCE. Reports committed to the repository are code/documentation only; runtime visual assets remain on the user's machine.

## ROADMAP policy

Family-aware batching materially improves the quality and efficiency of the real 4x art pass, but tooling alone does not complete Gate A–D. ROADMAP progress changes only after real local capture/art/QA evidence is verified.
