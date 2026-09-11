# Project #002 — Tiny Toon Visual Remaster

## Goal

This project does **not** rebuild the game from scratch. The user supplies their own NES ROM locally. The ROM remains responsible for gameplay, physics, level layouts, enemy behavior, scrolling and timing. Our work is the presentation layer: higher-resolution replacement graphics, optional audio replacement later, and simple PC controls.

The target workflow is **MesenCE HD Packs**. Mesen's HD-pack tooling records tile/palette combinations seen during gameplay into PNG sheets plus a `hires.txt` mapping. We redraw/replace the recorded graphics while the original game continues to run underneath.

> MesenCE is the actively maintained Community Edition successor. The old SourMesen/Mesen2 repository was archived in 2026, so Project #002 targets `nesdev-org/MesenCE` going forward.

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

## HD graphics workflow

1. Launch the ROM in MesenCE.
2. Configure the keyboard layout above once in the NES input settings.
3. Enable HD packs.
4. Use the **HD Pack Builder** to record gameplay and capture every animation, enemy, level, menu and effect you can reach.
5. Save/export the generated `hires.txt` and PNG sheets into a local work folder.
6. Use the tools in this repository to inspect the ROM, generate CHR reference sheets, prepare a workspace and validate the HD pack.
7. Replace recorded PNG graphics with new artwork while keeping all tile mappings intact.
8. Re-run the original ROM and visually verify every stage.

This keeps the original game logic and level data untouched; the remaster work lives in external HD-pack files.

## Tools

- `rom_probe.py` — CLI ROM inspector and CHR exporter.
- `prepare_workspace.py` — creates a local remaster workspace without copying the ROM itself.
- `validate_hdpack.py` — checks `hires.txt`, referenced PNG files and tile coordinates.
- `TinyToonRemasterStudio.py` — small Tkinter GUI wrapping the workflow.
- `windows/setup_mesence.ps1` — downloads/verifies the latest official MesenCE Windows build.
- `windows/launch_remaster.ps1` — verifies the ROM fingerprint and launches it in local MesenCE.
- `windows/Start_Remaster.bat` — one-click Windows wrapper.

## Python install

Python 3.11+ is recommended.

```bash
python -m pip install -r requirements.txt
```

Pillow is used for PNG export/validation.

## Examples

```bash
python tools/rom_probe.py "C:\\ROMs\\Tiny Toon Adventures (USA).nes"
python tools/rom_probe.py "C:\\ROMs\\Tiny Toon Adventures (USA).nes" --export-chr work/reference_chr --scale 4
python tools/prepare_workspace.py "C:\\ROMs\\Tiny Toon Adventures (USA).nes" --output work
python tools/validate_hdpack.py "work/Tiny Toon Adventures (USA)/MesenPack"
```

## Copyright / repository rule

Do not commit ROMs, emulator save states, Mesen captures made from commercial graphics, ripped game artwork, or locally downloaded emulator binaries. `reference_chr`, `captures`, `MesenPack`, `work`, and `vendor` are gitignored on purpose. The public repository contains tooling and original project metadata only.
