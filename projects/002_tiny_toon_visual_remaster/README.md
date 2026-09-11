# Project #002 — Tiny Toon Visual Remaster

## Goal

This project does **not** rebuild the game from scratch. The user supplies their own NES ROM locally. The ROM remains responsible for gameplay, physics, level layouts, enemy behavior, scrolling and timing. Our work is the presentation layer: higher-resolution replacement graphics, optional audio replacement later, and simple PC controls.

The target workflow is **MesenCE HD Packs**. Mesen's HD-pack tooling records tile/palette combinations seen during gameplay into PNG sheets plus a `hires.txt` mapping. We redraw/replace the recorded graphics while the original game continues to run underneath.

> MesenCE is the actively maintained Community Edition successor. Project #002 targets `nesdev-org/MesenCE` going forward.

## Verified source ROM profile

The uploaded local test ROM was detected as:

- iNES magic: valid
- PRG ROM: 128 KiB
- CHR ROM: 128 KiB
- mapper: 4 (MMC3)
- mirroring: horizontal
- trainer: no
- battery flag: no
- full-file SHA-1: `110796622e50c2e8c20b1430acadc5bae5f36586`
- full-file SHA-256: `688fe19096d8060decf9581165d52400a6d9b1cab79e7ef4cf9a66a794baf45f`

These hashes are used only to identify the local ROM. The ROM itself must never be committed.

## Controls

Recommended MesenCE mapping:

| PC key | NES control |
|---|---|
| Arrow keys | D-pad |
| Z | A |
| X | B |
| Enter | Start |
| Right Shift | Select |
| Esc | Emulator/menu |

If Z/X feel backwards for a specific action, simply swap A and B in MesenCE's input settings.

## Windows 11 — easiest start

From `projects/002_tiny_toon_visual_remaster/windows/` run:

```text
Start_Remaster.bat
```

It downloads/verifies the current official MesenCE Windows build if needed, installs it under the local gitignored `vendor/MesenCE`, asks for the user-supplied `.nes`, verifies the Project #002 fingerprint and launches the ROM without copying it into the repository.

## Fast HD workflow

1. Launch the ROM in MesenCE.
2. Open **Tools → HD Pack Builder**.
3. Capture at **4x Prescale** and trigger every reachable menu, route, animation, enemy, boss, HUD state and effect.
4. Save `hires.txt` + PNG sheets into the local `MesenCapture` folder.
5. Use the capture-diff tooling after later play sessions so new coverage is measurable.
6. Run **Instant HD Preview** for a fast modernized baseline while preserving all `hires.txt` mappings.
7. Generate the ranked/grouped art queue and finish the highest-reuse graphics first.
8. Mark the readiness checklist only after real local verification.
9. Run the **HD readiness dashboard**.
10. Build the release ZIP only from a structurally valid pack.

The automatic preview is a baseline, not a claim of finished modern artwork. The release dashboard deliberately refuses to invent an absolute whole-game percentage from unseen content.

## Capture progress and art queue

`hdpack_pipeline.py` measures capture growth and can rank tile/palette pairs by reuse:

```bash
python tools/hdpack_pipeline.py compare "C:\\TinyToonWork\\Capture_A" "C:\\TinyToonWork\\Capture_B"
python tools/hdpack_pipeline.py art-queue "C:\\TinyToonWork\\MesenCapture" --output "C:\\TinyToonWork\\Artwork\\ART_QUEUE.csv"
```

`hd_readiness.py` can add evidence-based grouping to the queue. It classifies only when Mesen condition names provide meaningful keywords; otherwise the row stays `UNASSIGNED` for local inspection.

```bash
python tools/hd_readiness.py classify "C:\\TinyToonWork\\ModernizedPack\\vibrant" --output "C:\\TinyToonWork\\Artwork\\ART_QUEUE.csv"
```

## Instant HD Preview

```bash
python tools/hdpack_pipeline.py analyze "C:\\TinyToonWork\\MesenCapture" --json
python tools/hdpack_pipeline.py preview "C:\\TinyToonWork\\MesenCapture" "C:\\TinyToonWork\\ModernizedPack\\vibrant" --style vibrant --overwrite
python tools/hdpack_pipeline.py report "C:\\TinyToonWork\\ModernizedPack\\vibrant"
```

The preview pipeline verifies referenced PNG files, processes graphics into a separate folder, preserves alpha, dimensions and mapping coordinates, and writes a SHA-256 manifest.

## HD readiness gate

A prepared Studio workspace contains `HD_READINESS_CHECKLIST.json`. Its evidence items cover:

- boot/title/menu states,
- every player movement/action/hit/death animation,
- every playable route and scrolling section,
- all common enemies,
- all boss phases,
- HUD/text/dialog states,
- projectiles/effects/transitions,
- ending/credits,
- final 4x art completion,
- full-game visual regression verification.

Generate the dashboard with:

```bash
python tools/hd_readiness.py dashboard "C:\\TinyToonWork\\ModernizedPack\\vibrant" --checklist "C:\\TinyToonWork\\HD_READINESS_CHECKLIST.json" --queue "C:\\TinyToonWork\\Artwork\\ART_QUEUE.csv" --output "C:\\TinyToonWork\\Release\\HD_READINESS.html"
```

The release gate is **BLOCKED** when structural validation fails, referenced PNGs are missing, the pack is below the 4x target, manual full-game evidence is incomplete, or the supplied art queue still contains TODO/unassigned rows.

## Safe release ZIP

```bash
python tools/hd_readiness.py package "C:\\TinyToonWork\\ModernizedPack\\vibrant" "C:\\TinyToonWork\\Release\\TinyToon_Visual_Remaster_HD_Pack.zip"
```

The packager validates the HD Pack and refuses ROM/save/patch files. Generated local reports are excluded from the release archive. A successfully created ZIP means the **pack structure is valid**; call it a complete HD release only after the readiness gate also passes through real local full-game verification.

## Tools

- `rom_probe.py` — CLI ROM inspector and CHR exporter.
- `prepare_workspace.py` — creates a local remaster workspace without copying the ROM itself.
- `validate_hdpack.py` — checks `hires.txt`, referenced PNG files and tile coordinates.
- `hdpack_pipeline.py` — capture analysis, capture diffing, ranked art queue, Instant HD Preview and capture report.
- `hd_readiness.py` — art grouping, evidence checklist, readiness dashboard and safe release ZIP packaging.
- `TinyToonRemasterStudio.py` — GUI for the complete capture → preview → art → readiness → package workflow.
- `windows/setup_mesence.ps1` — downloads/verifies the official MesenCE Windows build.
- `windows/launch_remaster.ps1` — verifies the ROM fingerprint and launches it locally.
- `windows/Start_Remaster.bat` — one-click Windows wrapper.

## Python install

Python 3.11+ is recommended.

```bash
python -m pip install -r requirements.txt
```

Pillow is used for PNG export, validation and preview processing.

## Copyright / repository rule

Do not commit ROMs, emulator save states, Mesen captures made from commercial graphics, ripped game artwork, locally generated derivative preview packs, or downloaded emulator binaries. `reference_chr`, `captures`, `MesenPack`, `ModernizedPack`, `work`, `Release`, and `vendor` remain local/gitignored by design. The public repository contains tooling and original project metadata only.
