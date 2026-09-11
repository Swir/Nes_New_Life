# Changelog — Project #002 Tiny Toon Visual Remaster

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
