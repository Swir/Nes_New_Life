# Project #002 — Accelerated 4x Art Production

The goal of this stage is to spend artist time once per unique captured graphic instead of redrawing identical Mesen tiles repeatedly.

## 1. Start from a real local capture

Use a MesenCE HD Pack Builder capture containing `hires.txt` and its PNG sheets. Keep the capture local; do not commit ROM-derived graphics.

Create or refresh the grouped queue first:

```bash
python tools/hd_readiness.py classify "C:\\TinyToonWork\\MesenCapture" --output "C:\\TinyToonWork\\Artwork\\ART_QUEUE.csv"
```

## 2. Generate visual workboards

```bash
python tools/art_production.py workboards "C:\\TinyToonWork\\MesenCapture" "C:\\TinyToonWork\\Artwork\\Workboards" --queue "C:\\TinyToonWork\\Artwork\\ART_QUEUE.csv"
```

This produces separate contact sheets for PLAYER, ENEMY, BOSS, WORLD, UI, EFFECTS and UNASSIGNED when those groups exist. Each thumbnail is labeled with its tile ID, palette fragment, rule number and condition name.

## 3. Detect duplicated drawing work

```bash
python tools/art_production.py duplicates "C:\\TinyToonWork\\MesenCapture" --queue "C:\\TinyToonWork\\Artwork\\ART_QUEUE.csv" --output "C:\\TinyToonWork\\Artwork\\DUPLICATES.json"
```

The report separates:

- exact duplicates — byte-identical RGBA tile crops that can safely share one redraw,
- near duplicates — perceptual candidates for artist review only.

Near-duplicate detection never rewrites graphics automatically.

## 4. Export unique master tiles

```bash
python tools/art_production.py masters "C:\\TinyToonWork\\MesenCapture" "C:\\TinyToonWork\\Artwork\\Masters" --queue "C:\\TinyToonWork\\Artwork\\ART_QUEUE.csv"
```

Only one PNG is exported for each exact visual hash. `MASTER_TILES.json` records every Mesen sheet coordinate that uses that visual. A master with `uses: 12` means one redraw can replace twelve captured occurrences.

## 5. Draw one master and propagate it safely

Edit one exported `MASTER_....png` at the same dimensions. Save the finished art as a separate PNG, then run:

```bash
python tools/art_production.py propagate ^
  "C:\\TinyToonWork\\MesenCapture" ^
  "C:\\TinyToonWork\\Artwork\\Masters\\MASTER_TILES.json" ^
  "C:\\TinyToonWork\\Artwork\\Masters\\MASTER_0001_PLAYER_....png" ^
  "C:\\TinyToonWork\\Artwork\\Finished\\player_idle.png" ^
  "C:\\TinyToonWork\\ModernizedPack\\art-pass-01"
```

Propagation writes to a new output folder, copies untouched sheets, updates every exact target recorded for that master, and copies `hires.txt` byte-for-byte. It never edits the source capture.

## Safety rules

- Exact hash matches may be propagated automatically.
- Near matches are review hints only.
- Keep replacement dimensions identical to the exported master.
- Validate the output pack after every propagation batch.
- Do not call the remaster complete until the readiness checklist and full-game local regression pass are complete.
