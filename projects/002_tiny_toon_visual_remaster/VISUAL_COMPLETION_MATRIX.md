# Visual Completion Matrix

`tools/visual_completion_matrix.py` measures captured-art completion by production group and produces the next high-impact art batch.

It is deliberately **capture-bounded**: it never claims that unseen game states are complete. Capture Mission Control remains authoritative for full-game coverage.

## What it measures

For every unique `tile_id + palette` master found in the supplied MesenCE HD pack/capture, the matrix joins local `ART_QUEUE.csv` classification with `MasterWorkspace/ART_STATE.csv` state and reports:

- PLAYER, BOSS, ENEMY, WORLD, UI, EFFECTS and UNASSIGNED completion,
- finished/TODO/invalid counts,
- usage-weighted completion,
- a weighted overall captured-art percentage that gives PLAYER/BOSS/ENEMY more production importance,
- blocking invalid or unassigned items,
- the next bounded batch of highest-impact unfinished masters.

The batch score strongly promotes invalid masters, PLAYER/BOSS work, classification blockers and high-reuse graphics so an art session moves the visible game forward instead of spending time on low-impact tiles first.

## One-click Windows use

Run:

`windows/Visual_Completion_Matrix.bat`

The launcher uses the default local `Artwork/ART_QUEUE.csv` and `Artwork/MasterWorkspace` when present, asks for missing paths, then opens:

`Reports/VisualCompletion/VISUAL_COMPLETION_MATRIX.html`

It also writes:

- `VISUAL_COMPLETION_MATRIX.json`
- `VISUAL_COMPLETION_MATRIX.csv`
- `NEXT_HIGH_IMPACT_ART_BATCH.csv`

All of these reports are metadata-only. They do not copy PNG capture data, ROM content, save states, emulator binaries or commercial assets.

## CLI

```powershell
python tools/visual_completion_matrix.py <PACK> Reports/VisualCompletion `
  --queue Artwork/ART_QUEUE.csv `
  --workspace Artwork/MasterWorkspace `
  --batch-size 40
```

Use the matrix after every successful capture promotion and after every finished art sprint. The target is not just a high percentage: every captured group must reach zero TODO/invalid, every UNASSIGNED item must be classified, and full-game Capture Mission Control must still be complete before release.
