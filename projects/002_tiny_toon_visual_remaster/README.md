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

It will:

1. download the latest official Windows build of MesenCE from `nesdev-org/MesenCE` if needed,
2. verify the downloaded ZIP SHA-256 when GitHub supplies a digest,
3. install it locally under the gitignored `vendor/MesenCE` folder,
4. ask you to choose your `.nes` file,
5. verify the Project #002 SHA-1 fingerprint,
6. launch the ROM directly from its existing location.

The ROM is never copied into the repository.

## Fast HD workflow

The fastest route is now:

1. Launch the ROM in MesenCE.
2. Configure the keyboard layout above once in NES input settings.
3. Open **Tools → HD Pack Builder**.
4. Record gameplay and trigger every animation, enemy, level, menu and effect you can reach.
5. For the first pass use a **4x scale** with a Prescale-style capture so tile coordinates stay clean and editing is comfortable.
6. Save/export the generated `hires.txt` and PNG sheets into a local work folder.
7. Open `TinyToonRemasterStudio.py` and choose **Select Mesen capture**.
8. Run **Instant HD Preview**. Choose `clean`, `vibrant`, `smooth` or `illustrated`.
9. Studio creates a separate modernized pack and preserves `hires.txt` mapping coordinates exactly.
10. Re-run the original ROM with that pack, then replace important PNG regions with final hand-made artwork over time.

The automatic preview is a **baseline**, not a claim of finished modern artwork. Its purpose is to make the game visually improved immediately while letting us spend manual art time only on the characters, enemies, bosses and scenery that matter most.

## Instant HD Preview

`tools/hdpack_pipeline.py` can also be used directly:

```bash
python tools/hdpack_pipeline.py analyze "C:\\TinyToonWork\\MesenCapture" --json
python tools/hdpack_pipeline.py preview "C:\\TinyToonWork\\MesenCapture" "C:\\TinyToonWork\\ModernizedPack\\vibrant" --style vibrant --overwrite
python tools/hdpack_pipeline.py report "C:\\TinyToonWork\\ModernizedPack\\vibrant"
```

The preview pipeline:

- parses current Mesen HD Pack format metadata,
- counts PNG sheets, tile rules, conditions, unique tile IDs and palettes,
- verifies referenced PNG files exist,
- processes PNGs non-destructively into a separate folder,
- preserves alpha transparency,
- keeps image dimensions and `hires.txt` coordinates unchanged,
- writes `NES_NEW_LIFE_PREVIEW.json` with hashes and processing metadata,
- can generate a local HTML capture report.

## Tools

- `rom_probe.py` — CLI ROM inspector and CHR exporter.
- `prepare_workspace.py` — creates a local remaster workspace without copying the ROM itself.
- `validate_hdpack.py` — checks `hires.txt`, referenced PNG files and tile coordinates.
- `hdpack_pipeline.py` — capture analysis, Instant HD Preview and HTML report generator.
- `TinyToonRemasterStudio.py` — GUI for ROM inspection, workspace, capture analysis, preview generation and validation.
- `windows/setup_mesence.ps1` — downloads/verifies the latest official MesenCE Windows build.
- `windows/launch_remaster.ps1` — verifies the ROM fingerprint and launches it in local MesenCE.
- `windows/Start_Remaster.bat` — one-click Windows wrapper.

## Python install

Python 3.11+ is recommended.

```bash
python -m pip install -r requirements.txt
```

Pillow is used for PNG export, validation and preview processing.

## Copyright / repository rule

Do not commit ROMs, emulator save states, Mesen captures made from commercial graphics, ripped game artwork, locally generated derivative preview packs, or downloaded emulator binaries. `reference_chr`, `captures`, `MesenPack`, `ModernizedPack`, `work`, and `vendor` are gitignored/local by design. The public repository contains tooling and original project metadata only.
