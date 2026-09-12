# Changelog — Project #002 Tiny Toon Visual Remaster

## 0.6.0 — Pixel-safe batch art QA gate

- added `art_qa.py` to compare the original MesenCE capture against the composed `final_art` pack at pixel level
- derives authorized edit rectangles from the exact changed master PNG dimensions and every target in `MASTER_TILES.json`
- detects RGB **and alpha/transparency** changes outside authorized master targets
- blocks batch apply when even a single unauthorized output pixel is detected
- verifies `hires.txt` is preserved byte-for-byte and sheet names/dimensions remain unchanged
- detects edited masters that unexpectedly produce no output difference
- emits `ART_QA_RESULT.json`, a local HTML QA report and marker-only diff overlays
- diff overlays do not reproduce source artwork: green marks authorized changes and magenta marks unauthorized changes
- integrated QA directly into `apply_workspace`, so Remaster Studio's existing Apply all master edits action automatically runs the safety gate
- added synthetic tests for a clean authorized batch edit and deliberate one-pixel corruption outside the authorized region

## 0.5.0 — Batch master-art workspace

- added persistent `MasterWorkspace/original` and `MasterWorkspace/editable` folders for real multi-asset production sessions
- added SHA-256 scan that automatically marks master graphics as TODO, EDITED or INVALID
- added strict dimension checks so an edited master cannot overwrite neighboring HD tiles
- added batch apply that composes all edited masters into one combined HD Pack instead of rebuilding from the original pack once per tile
- preserved `hires.txt` byte-for-byte during batch art composition
- generated `ART_STATE.csv`, `WORKSPACE.json` and `ART_APPLY_RESULT.json` for reproducible local progress tracking
- integrated Create master workspace, Scan art progress and Apply all master edits directly into Remaster Studio
- added synthetic CI tests for multiple simultaneous edits, mapping preservation and resized-master rejection

## 0.4.0 — HD readiness, art grouping and safe release packaging

- added evidence-based HD release gate instead of a guessed whole-game completion percentage
- added `HD_READINESS_CHECKLIST.json` template covering boot/menu, player animations, routes, enemies, bosses, HUD/text, effects, ending/credits, final art and full-game regression
- added automatic art-queue grouping into PLAYER / ENEMY / BOSS / WORLD / UI / EFFECTS when Mesen condition names provide evidence
- unknown tiles remain explicitly `UNASSIGNED` for local inspection
- added HTML + JSON readiness dashboard combining structural validation, 4x scale target, art queue progress and manual full-game evidence
- added safe HD Pack ZIP builder that validates the pack and refuses ROM/save/patch files
- upgraded Remaster Studio with grouped art queue, readiness dashboard and one-click release ZIP actions
- expanded local workspace with `Release` and readiness checklist files
- added synthetic CI coverage for grouping, readiness blockers, dashboard generation and packaging safety

## 0.3.0 — Capture coverage and ranked art queue

- added capture-to-capture diffing for rule growth/regression
- added new tile/palette discovery reporting
- added ranked art queue generation based on tile/palette reuse
- added capture sprint workflow so repeated play sessions produce measurable progress

## 0.2.0 — Instant HD Preview foundation

- added Mesen HD Pack analyzer for format version, scale, PNG sheets, tile rules, conditions, unique tile IDs and palettes
- added non-destructive Instant HD Preview pipeline with `clean`, `vibrant`, `smooth` and `illustrated` processing styles
- preserved PNG dimensions, transparency and all `hires.txt` coordinates/mappings
- added SHA-256 manifest for source/output preview sheets
- added local HTML capture report generator
- upgraded Remaster Studio with capture selection, preview generation, validation and reporting
- expanded workspace layout for `MesenCapture`, `ModernizedPack`, `Artwork` and `reference_chr`
- added automated preview/analysis tests using synthetic assets only
- expanded gitignore rules so captures and derivative commercial graphics stay local

## 0.1.0 — HD-pack foundation

- switched the project direction from a from-scratch remake to a ROM-driven visual remaster
- verified the user-supplied ROM fingerprint and MMC3/iNES profile locally
- added CHR reference exporter and workspace preparation tools
- added `hires.txt`/PNG validator
- added Remaster Studio GUI
- added MesenCE one-click Windows setup/launcher
- added safe CI tests without distributing the ROM or ROM-derived graphics
