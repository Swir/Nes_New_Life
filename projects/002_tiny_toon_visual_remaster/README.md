# Project #002 — Tiny Toon Visual Remaster

## Goal

This project does **not** rebuild the game from scratch. The user supplies their own NES ROM locally. The ROM remains responsible for gameplay, physics, level layouts, enemy behavior, scrolling and timing. Our work is the presentation layer: higher-resolution replacement graphics and a production workflow for a safe MesenCE HD Pack.

The target workflow is **MesenCE HD Packs**. MesenCE's HD-pack tooling records tile/palette combinations seen during gameplay into PNG sheets plus a `hires.txt` mapping. We redraw/replace the recorded graphics while the original game continues to run underneath.

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

Gamepads are configured through MesenCE Input settings. The remaster does not alter the ROM's controls, physics or timing.

## Windows 11 — easiest start

From `projects/002_tiny_toon_visual_remaster/windows/` run:

```text
Start_Remaster.bat
```

It downloads/verifies the current official MesenCE Windows build if needed, installs it under the local gitignored `vendor/MesenCE`, asks for the user-supplied `.nes`, verifies the Project #002 fingerprint and launches the ROM without copying it into the repository.

For the fastest capture-to-playtest loop use:

```text
Build_HD_Playtest.bat
```

This creates a QA-gated current HD pack and can deploy it into the user's local MesenCE `HdPacks/<ROM stem>` folder with a backup of the previously installed pack.

## Remaster Studio — production command center

`tools/TinyToonRemasterStudio.py` is now the preferred GUI workflow. It exposes the authoritative production path instead of the older standalone readiness/package flow:

1. Open the user-supplied ROM locally.
2. Prepare the local workspace. Studio initializes Capture Mission Control and build-bound final-regression evidence.
3. Capture with MesenCE HD Pack Builder at **4x Prescale**.
4. Use **Capture Mission Control** and **Record capture session** to verify menus, player states, routes, enemies, bosses, UI, effects and ending coverage.
5. Generate/sync the grouped art queue and MasterWorkspace.
6. Edit only `Artwork/MasterWorkspace/editable/*.png` while keeping dimensions unchanged.
7. Use **Apply + build-bound QA**. Studio composes the batch and fingerprints the exact runtime pack.
8. Use **One-click HD Playtest** to build/deploy the current result into MesenCE.
9. Complete final regression against that exact build fingerprint.
10. Run **Release Candidate Audit**.
11. **GATED release ZIP** is enabled in practice only when the unified release gate returns PASS.

Changing `hires.txt` or any referenced runtime PNG after QA/regression makes previous evidence stale automatically.

## Capture progress and art queue

`capture_mission_control.py` tracks explicit gameplay coverage while `hdpack_pipeline.py` measures structural capture growth. Tile-count growth alone never auto-completes a gameplay mission.

```bash
python tools/capture_mission_control.py init "C:\\TinyToonWork\\CAPTURE_MISSIONS.json"
python tools/capture_mission_control.py record "C:\\TinyToonWork\\CAPTURE_MISSIONS.json" "C:\\TinyToonWork\\MesenCapture" --complete player_idle_walk_run
python tools/capture_mission_control.py dashboard "C:\\TinyToonWork\\CAPTURE_MISSIONS.json" "C:\\TinyToonWork\\Reports\\CAPTURE_MISSION_CONTROL.html"

python tools/hdpack_pipeline.py compare "C:\\TinyToonWork\\Capture_A" "C:\\TinyToonWork\\Capture_B"
python tools/hdpack_pipeline.py art-queue "C:\\TinyToonWork\\MesenCapture" --output "C:\\TinyToonWork\\Artwork\\ART_QUEUE.csv"
```

Unknown artwork stays `UNASSIGNED`; the unified release gate blocks shipping until every art-queue row is both classified and finished.

## Instant HD Preview

```bash
python tools/hdpack_pipeline.py analyze "C:\\TinyToonWork\\MesenCapture" --json
python tools/hdpack_pipeline.py preview "C:\\TinyToonWork\\MesenCapture" "C:\\TinyToonWork\\ModernizedPack\\vibrant" --style vibrant --overwrite
python tools/hdpack_pipeline.py report "C:\\TinyToonWork\\ModernizedPack\\vibrant"
```

The preview is a fast baseline, not final artwork. It preserves alpha, dimensions and `hires.txt` mapping coordinates.

## Final release gate

The authoritative final gate is `release_candidate.py`, not the legacy readiness dashboard by itself. PASS requires all of the following on the **same current runtime build**:

- structurally valid 4x HD Pack,
- complete Capture Mission Control evidence,
- zero TODO art-queue rows,
- zero UNASSIGNED art-queue rows,
- build-bound Pixel Art QA PASS,
- every final full-game regression case completed against the current runtime fingerprint,
- no ROM/save-state/patch payloads.

Audit example:

```bash
python tools/release_candidate.py audit "C:\\TinyToonWork\\ModernizedPack\\final_art" \
  --capture "C:\\TinyToonWork\\CAPTURE_MISSIONS.json" \
  --queue "C:\\TinyToonWork\\Artwork\\ART_QUEUE.csv" \
  --art-qa "C:\\TinyToonWork\\Reports\\ArtQA\\ART_QA_RESULT.json" \
  --regression "C:\\TinyToonWork\\FINAL_REGRESSION.json" \
  --output "C:\\TinyToonWork\\Reports\\ReleaseCandidate"
```

The Studio's **GATED release ZIP** action uses this same gate and refuses to package a BLOCKED build. This closes the old GUI bypass where a structurally valid pack could be zipped before complete capture/current-build QA/regression evidence existed.

## Tools

- `rom_probe.py` — CLI ROM inspector and local CHR reference exporter.
- `prepare_workspace.py` — creates a local remaster workspace without copying the ROM.
- `validate_hdpack.py` — validates `hires.txt`, referenced PNG files and tile coordinates.
- `hdpack_pipeline.py` — capture analysis/diffing, ranked queue, preview and reports.
- `capture_mission_control.py` — explicit full-game capture mission tracking.
- `production_sync.py` — resume-safe repeated-capture synchronization.
- `art_production.py` — workboards, exact dedupe, near-duplicate hints and master propagation.
- `art_workspace.py` — persistent batch master-art workspace.
- `auto_art_pass.py` — automatic baseline modernization for untouched masters.
- `art_qa.py` / `bound_art_qa.py` — pixel-safe QA and exact-build fingerprint binding.
- `rapid_hd_playtest.py` — capture → sync → baseline → apply → QA → optional MesenCE deployment.
- `release_candidate.py` — single authoritative final release gate.
- `studio_command_center.py` — safe GUI-facing orchestration layer for evidence, playtest, audit and gated packaging.
- `TinyToonRemasterStudio.py` — GUI production command center.
- `windows/setup_mesence.ps1` — downloads/verifies the official MesenCE Windows build.
- `windows/launch_remaster.ps1` — verifies the ROM fingerprint and launches it locally.
- `windows/Start_Remaster.bat` — one-click Windows launcher.
- `windows/Build_HD_Playtest.bat` — one-click QA-gated HD playtest build/deploy.

## Python install

Python 3.11+ is recommended.

```bash
python -m pip install -r requirements.txt
```

Pillow is used for PNG export, validation, preview processing and QA.

## Copyright / repository rule

Do not commit ROMs, emulator save states, Mesen captures made from commercial graphics, ripped game artwork/audio, locally generated derivative preview/final packs, or downloaded emulator binaries. `reference_chr`, `captures`, `MesenPack`, `ModernizedPack`, `work`, `Release`, `Reports`, and `vendor` remain local/gitignored by design. The public repository contains tooling, tests using synthetic graphics, documentation and original project metadata only.
