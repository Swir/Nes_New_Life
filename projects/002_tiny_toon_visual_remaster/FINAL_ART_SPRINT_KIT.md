# Project #002 — Final Art Sprint Kit

`art_sprint_kit.py` turns the evidence-driven Final Art Priority Board into a practical batch-edit loop for real HD artwork.

## Why it exists

The priority board already knows which captured graphics matter most. The Sprint Kit removes the manual step of hunting through the whole MasterWorkspace. It exports only the highest-priority unfinished masters into one local editing folder, keeps untouched references beside them, records exact hashes/dimensions, and can safely import the edited batch back.

## Export a sprint

```bash
python tools/art_sprint_kit.py export \
  "C:\\TinyToonWork\\ModernizedPack\\final_art" \
  "C:\\TinyToonWork\\Artwork\\MasterWorkspace" \
  "C:\\TinyToonWork\\Artwork\\CurrentArtSprint" \
  --queue "C:\\TinyToonWork\\Artwork\\ART_QUEUE.csv" \
  --visual-review "C:\\TinyToonWork\\Artwork\\VISUAL_CONTEXT_REVIEW.csv" \
  --animation-review "C:\\TinyToonWork\\Artwork\\ANIMATION_FAMILY_REVIEW.csv" \
  --top 20 --overwrite
```

The kit contains:

- `editable/` — the files to redraw,
- `reference/` — untouched source references,
- `ART_SPRINT_KIT.json` — priority, hashes, dimensions and provenance,
- `LOCAL_ART_SPRINT_BOARD.png` — a local visual board ordered by priority.

Do not rename files and do not resize the canvas.

## Import only

```bash
python tools/art_sprint_kit.py import \
  "C:\\TinyToonWork\\Artwork\\MasterWorkspace" \
  "C:\\TinyToonWork\\Artwork\\CurrentArtSprint"
```

Import is conflict-safe. If a MasterWorkspace file changed after the sprint was exported and the sprint also changed that file, import stops instead of silently overwriting newer work. Resized or missing sprint masters also block import.

## Finish a sprint in one command

```bash
python tools/art_sprint_kit.py finish \
  "C:\\TinyToonWork\\ModernizedPack\\final_art" \
  "C:\\TinyToonWork\\Artwork\\MasterWorkspace" \
  "C:\\TinyToonWork\\Artwork\\CurrentArtSprint" \
  "C:\\TinyToonWork\\ModernizedPack\\sprint_output" \
  --overwrite
```

`finish` performs:

`safe import → MasterWorkspace scan → combined HD composition → hires.txt preservation check → structural validation → pixel QA`

A successful result records `qa_gate=PASS` and `mapping_preserved=true` in `ART_SPRINT_FINISH.json`.

## Recommended loop

1. Complete a targeted MesenCE capture session.
2. Run production sync.
3. Refresh Visual Context / Animation Family evidence.
4. Export a Top-20 sprint.
5. Redraw `CurrentArtSprint/editable/*.png`.
6. Finish the sprint and playtest the resulting HD Pack.
7. Refresh the Final Art Priority Board; completed masters fall out automatically.
8. Repeat until no TODO/INVALID captured masters remain.

## Safety boundary

The sprint kit contains ROM-derived captured graphics and must stay local. `Artwork/` and `Reports/` are explicitly ignored by the repository. Never commit sprint graphics, captures, ROMs, save states, ripped commercial art/audio or emulator binaries.
