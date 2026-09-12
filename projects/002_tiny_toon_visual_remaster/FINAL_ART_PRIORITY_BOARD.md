# Project #002 — Final Art Priority Board

This milestone turns the existing capture, context, animation and master-art evidence into one practical answer: **which captured graphics should be finished next for the largest visible HD gain?**

## What it combines

`tools/final_art_priority.py` scores each captured tile/palette candidate using:

- art group priority (`PLAYER`, `BOSS`, `ENEMY`, `UI`, `EFFECTS`, `WORLD`, `UNASSIGNED`),
- reuse count across the current HD pack,
- Visual Context risk and pending review state,
- Animation Family risk and pending review state,
- MasterWorkspace state (`TODO`, `EDITED`, `INVALID`),
- classification blockers such as `UNASSIGNED`.

Already edited master entries are removed from the work queue. Invalid masters are pushed to the top because they can block production. The board is intentionally metadata-only and never embeds captured game artwork.

## Recommended command

```bash
python tools/final_art_priority.py \
  "C:\\TinyToonWork\\ModernizedPack\\final_art" \
  "C:\\TinyToonWork\\Reports\\FinalArtPriority" \
  --queue "C:\\TinyToonWork\\Artwork\\ART_QUEUE.csv" \
  --workspace "C:\\TinyToonWork\\Artwork\\MasterWorkspace" \
  --visual-review "C:\\TinyToonWork\\Artwork\\VISUAL_CONTEXT_REVIEW.csv" \
  --animation-review "C:\\TinyToonWork\\Artwork\\ANIMATION_FAMILY_REVIEW.csv" \
  --top 20
```

Outputs:

- `FINAL_ART_NEXT.csv` — the practical redraw queue,
- `FINAL_ART_PRIORITY.json` — machine-readable ranking,
- `FINAL_ART_PRIORITY.html` — metadata-only dashboard.

## Production loop

1. Run Capture Gap Planner and resolve capture regressions first.
2. Sync the latest accepted capture into production.
3. Run Visual Context and Animation Family reviews.
4. Generate the Final Art Priority Board.
5. Finish the highest-ranked master art inside `MasterWorkspace/editable/`.
6. Re-run the board; completed (`EDITED`) masters disappear automatically.
7. Apply workspace, run build-bound Pixel QA and MesenCE playtest.

## Important boundary

This ranking only prioritizes **captured** material. It cannot prove that uncaptured routes, animations, bosses or effects do not exist. Capture Mission Control and real full-game playthrough remain authoritative for coverage.

## Repository safety

The priority reports contain metadata only. ROMs, save states, Mesen captures, commercial art/audio, local contact sheets, derivative final packs and emulator binaries remain local and must not be committed.
