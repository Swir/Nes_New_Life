# High-Impact Art Sprint — Project #002

This milestone turns the Visual Completion Matrix from a ranking report into an immediately editable production batch.

## What it does

`tools/high_impact_art_sprint.py prepare` runs the current Visual Completion Matrix and exports its exact `NEXT_HIGH_IMPACT_ART_BATCH` selection into a local sprint kit. The selection therefore stays focused on PLAYER/BOSS/ENEMY visibility, invalid masters, high-reuse graphics and classification blockers instead of falling back to a separate ranking algorithm.

The local kit contains:

- `editable/` — files the artist is allowed to redraw,
- `reference/` — untouched local baseline copies,
- `LOCAL_ART_SPRINT_BOARD.png` — local contact board,
- `ART_SPRINT_KIT.json` — dimensions, source hashes, selection reasons and impact scores,
- `HIGH_IMPACT_SPRINT_READY.json` — metadata-only handoff status.

The board and PNG content are local derivative/capture material and must never be committed.

## Windows one-click

Run `windows/High_Impact_Art_Sprint.bat` to select the current local capture/pack, generate the completion report, create `Artwork/CurrentImpactSprint`, open the dashboard, board and editable folder.

After editing the PNGs without resizing or renaming them, run `windows/Finish_High_Impact_Art_Sprint.bat`.

Finish reuses the existing safe Art Sprint importer. It blocks stale MasterWorkspace conflicts by SHA-256, rejects changed dimensions, composes a candidate HD pack while preserving `hires.txt`, and runs Pixel QA before reporting success.

## Safety boundaries

This workflow never supplies or commits a ROM, emulator binary, save state, captured graphics or ripped commercial assets. The ROM remains the local gameplay source in MesenCE. Reports committed to the repository are code/documentation only; runtime visual assets remain on the user's machine.

## Why this is higher impact

Before this milestone, Visual Completion Matrix produced the right next batch but creating an Art Sprint could use a separate Final Art Priority ranking. The new director removes that gap: the exact graphics measured as the highest-impact unfinished work are the exact graphics exported for the next local art session.
