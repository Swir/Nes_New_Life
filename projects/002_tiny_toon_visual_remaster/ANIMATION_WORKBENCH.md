# Project #002 — Animation Family Workbench

This milestone moves art production above isolated tile review without pretending that Mesen HD texture-sheet coordinates are on-screen sprite coordinates.

## What it does

`tools/animation_workbench.py` uses Mesen condition names plus captured tile/palette/visual metadata to build **semantic animation families** such as a player, enemy or boss across idle/walk/run/jump/hit/phase states. It also emits **condition co-occurrence candidates**: tiles sharing the same condition and art group that should be inspected together in the running game.

The tool deliberately does **not** infer screen geometry from PNG-sheet X/Y positions. Those are HD-pack texture coordinates, not reliable sprite assembly coordinates.

## Recommended flow

```bash
python tools/animation_workbench.py dashboard \
  "C:\\TinyToonWork\\ModernizedPack\\final_art" \
  --queue "C:\\TinyToonWork\\Artwork\\ART_QUEUE.csv" \
  --review "C:\\TinyToonWork\\Artwork\\ANIMATION_FAMILY_REVIEW.csv" \
  --output "C:\\TinyToonWork\\Reports\\AnimationWorkbench"
```

For a local visual workboard:

```bash
python tools/animation_workbench.py contact-sheets \
  "C:\\TinyToonWork\\ModernizedPack\\final_art" \
  --queue "C:\\TinyToonWork\\Artwork\\ART_QUEUE.csv" \
  --output "C:\\TinyToonWork\\Reports\\AnimationWorkbench\\LocalContactSheets"
```

Contact sheets contain locally captured graphics and must stay local/gitignored. The normal HTML/JSON dashboard is metadata-only.

After checking a family in MesenCE:

```bash
python tools/animation_workbench.py mark-reviewed \
  "C:\\TinyToonWork\\Artwork\\ANIMATION_FAMILY_REVIEW.csv" HERO \
  --notes "walk/run/jump transitions checked in MesenCE"
```

Reviews are fingerprinted. If the capture or visual composition of a family changes, the old review becomes stale.

## Release behavior

The authoritative release gate now **really enforces** the rc3 Visual Context Review. A missing, pending or stale `VISUAL_CONTEXT_REVIEW.csv` blocks packaging. Animation Family Review is currently a production accelerator/advisory review because condition naming is heuristic; final exact-build regression remains authoritative for animation correctness.

## Safety

No ROM, save state, capture PNG, ripped commercial art/audio or emulator binary belongs in the repository. Synthetic tests are the only visual fixtures committed by this milestone.
