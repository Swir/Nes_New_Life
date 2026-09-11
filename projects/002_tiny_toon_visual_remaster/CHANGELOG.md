# Changelog — Project #002 Tiny Toon Visual Remaster

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
