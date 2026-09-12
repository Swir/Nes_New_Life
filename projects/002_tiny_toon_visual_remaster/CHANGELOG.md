# Changelog — Project #002 Tiny Toon Visual Remaster

## 1.0.0-rc3 — Visual context & animation-risk audit

- added `visual_context_audit.py` to group captured tile uses by tile ID and rank families that are visually risky across palettes, conditions and distinct captured RGBA variants
- high-risk scoring now highlights multi-palette, multi-condition, visual-variant, mixed-group, unassigned and rare families so final art review starts where mistakes are most likely to be visible
- added persistent `VISUAL_CONTEXT_REVIEW.csv` with explicit `REVIEW` / `REVIEWED` states and artist notes
- every family carries a stable fingerprint derived from palettes, conditions, exact visual hashes, art groups and usage count; later capture/art changes automatically make an older reviewed family stale
- added metadata-only HTML/JSON dashboard; reports do not embed captured commercial artwork
- added synthetic tests for high-risk detection, explicit review, stale-review invalidation after an art change and report privacy
- refreshed README and ROADMAP to place visual-context review before final polish/regression
- added `VISUAL_CONTEXT_AUDIT.md`
- no ROM, save state, ROM-derived capture, ripped commercial art/audio, emulator binary or derivative final pack is committed

## 1.0.0-rc2 — Remaster Studio production command center

- upgraded `TinyToonRemasterStudio.py` from the legacy readiness/package GUI into the authoritative HD production command center
- added `studio_command_center.py` as a safe orchestration layer for Capture Mission Control, exact-build Pixel QA, one-click playtest, unified release audit and gated packaging
- Studio workspace creation now initializes `CAPTURE_MISSIONS.json` and `FINAL_REGRESSION.json` automatically
- added GUI Capture Mission Control dashboard and capture-session recording with explicit mission completion only
- changed the batch-art action to run build-bound Pixel QA after composition; QA evidence is stored under `Reports/ArtQA` and tied to the exact runtime fingerprint
- added one-click QA-gated MesenCE playtest build/deploy directly to Studio while preserving backup behavior
- replaced the old GUI readiness action with the Unified Release Candidate Audit
- removed the old GUI packaging bypass: `GATED release ZIP` refuses to create an archive until complete capture, finished/classified art, current-build QA and current-build full-game regression all PASS
- refreshed README and roadmap so the unified gate is authoritative for GUI and CLI users alike
- added `STUDIO_COMMAND_CENTER.md` and synthetic command-center tests proving missing evidence blocks Studio packaging and complete current-build evidence permits it
- no ROM, save state, ROM-derived capture, ripped commercial art/audio, emulator binary or final derivative pack is committed

## 1.0.0-rc1 — Unified build-bound release candidate gate

- added `release_candidate.py` as the single authoritative final release gate for Project #002
- release PASS now requires structural validation, complete Capture Mission Control evidence, a fully finished/classified art queue, current-build pixel QA and current-build full-game visual regression
- added a stable SHA-256 runtime fingerprint derived from `hires.txt` plus every referenced HD PNG
- final regression evidence is bound to that exact fingerprint, so any later runtime art/mapping change automatically invalidates the older regression pass
- added `bound_art_qa.py` so the existing pixel-safe Art QA result can be bound to the exact output HD Pack fingerprint
- stale Art QA is explicitly blocked even when the older report itself says PASS
- added ten final regression cases covering boot/menu, player movement, actions/damage/death, primary and alternate routes, enemies, bosses, HUD/text, effects/transitions and ending/credits
- gated packaging refuses to create the final ZIP until every authoritative evidence source passes for the current build
- added local HTML + JSON `RELEASE_CANDIDATE` dashboard with exact blockers and stale-evidence reporting
- added synthetic CI tests proving a previously green build becomes BLOCKED after runtime art changes and proving TODO/UNASSIGNED art cannot pass release
- added `RELEASE_CANDIDATE_GATE.md` and advanced the roadmap from separate readiness indicators to one build-bound final gate
- no ROM, save state, ROM-derived capture, commercial art/audio, emulator binary or final derivative pack is committed

## 0.9.0 — One-click QA-gated MesenCE HD playtest

- added `rapid_hd_playtest.py` to turn a local MesenCE capture into an installed playable HD pack in one production command
- chains resume-safe capture sync, automatic baseline seeding, combined batch art apply, pixel QA, HD-pack validation and readiness reporting
- existing manual master edits remain protected because the automatic baseline only seeds still-untouched masters
- added atomic MesenCE `HdPacks/<ROM stem>` deployment with a timestamped backup of the previously installed pack
- deployment refuses ROM, save-state and patch payloads and excludes generated JSON/HTML/CSV reports from runtime assets
- verifies mapping preservation and requires pixel QA PASS before declaring the captured content playtest-ready
- added `windows/Build_HD_Playtest.bat` + PowerShell folder/ROM picker so the complete loop can be launched by double-clicking on Windows 11
- added synthetic CI tests for end-to-end build, backup deployment, prohibited-file blocking and runtime metadata filtering
- added `RAPID_HD_PLAYTEST.md` with the capture → build → install → reload workflow
- `PLAYTEST READY` remains intentionally different from `FULL GAME COMPLETE`: unseen game states still require real MesenCE capture and final art review

## 0.8.0 — Automatic baseline master-art pass

- added `auto_art_pass.py` to seed every still-untouched master graphic with a coherent automatic modernization pass
- existing manually edited masters are preserved by default and are never overwritten unless `--force` is explicitly used
- added group-aware styles for PLAYER, ENEMY, BOSS, WORLD, UI, EFFECTS and UNASSIGNED masters
- all baseline transforms preserve pixel dimensions and alpha/transparency exactly
- generated `AUTO_BASELINE.json` records every seeded/preserved/missing master and the style used
- automatic baseline output remains intentionally distinct from final hand-finished art; it is a fast playable starting pass, not a fake completion claim
- added synthetic regression tests proving TODO masters are modernized, alpha is unchanged and prior manual edits survive
- roadmap now places automatic baseline generation before final manual polish so the whole captured game can become testable much earlier

## 0.7.0 — Resume-safe incremental production sync

- added `production_sync.py` to turn repeated MesenCE captures into one resumable production workflow
- art queue regeneration now preserves existing non-TODO status, non-UNASSIGNED artist grouping and notes for matching tile+palette entries
- mappings that disappear from a newer capture are exported to `ART_QUEUE_RETIRED.csv` instead of being silently forgotten
- master-workspace synchronization now identifies existing artwork by exact source RGBA hash instead of fragile numeric filenames
- already edited master PNGs survive capture growth; only their target lists are refreshed against the newest `hires.txt`
- newly discovered graphics receive stable hash-based master filenames and are added without rebuilding the whole art workspace
- synchronization refreshes `ART_STATE.csv`, grouped workboards, capture report and HD-readiness report in one command
- added machine-readable `PRODUCTION_SYNC.json`, `WORKSPACE_SYNC.json` and queue sync evidence
- added synthetic regression tests proving artist state and edited master pixels survive a larger second capture
- added `INCREMENTAL_PRODUCTION.md` with the recommended capture → sync → redraw → QA loop

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
