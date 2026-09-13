# Changelog — Project #002 Tiny Toon Visual Remaster

## 1.0.0-rc20 — Acceptance-gated capture production handoff

- wired `capture_coverage_acceptance.py` directly into `capture_promotion_director.py` before any `ART_QUEUE.csv` / `MasterWorkspace` mutation
- split full capture readiness from safe incremental art admission: `READY_FOR_GATE_A_REVIEW` still requires real gameplay review, while `INCREMENTAL_CAPTURE_READY` may continue iterative HD art when integrity/provenance is safe but missions/groups are still pending
- integrity admission failure, structural capture failure, `CAPTURE_REGRESSION`, at-risk verified missions and untrusted mission provenance now block promotion as `UNSAFE_CAPTURE`
- promotion reports now carry the exact capture fingerprint, full acceptance gate, production-admission mode, hard blockers and acceptance report paths
- Authoritative Remaster Studio now exposes **CHECK CAPTURE ACCEPTANCE** / Ctrl+F5 and displays the current fingerprint, verified mission count, hard blockers and exact `DO THIS NEXT`
- expanded promotion and Studio tests so unsafe evidence cannot silently mutate production state and acceptance reports remain metadata-only
- refreshed README, Capture Promotion Director documentation and authoritative Project #002 ROADMAP around the new capture → acceptance → promotion path
- ROADMAP Gate A–D remains 0/52 = 0.0%; this tooling milestone does not substitute for real local gameplay/capture/art/QA evidence
- no ROM, save state, ROM-derived capture PNG/JPG, ripped commercial art/audio or emulator binary is committed

## 1.0.0-rc19 — Guided Fullscreen Capture Marathon

- added `guided_capture_marathon.py` as an explicit evidence-first controller for the eleven authoritative Capture Mission Control areas
- each pending mission now has concrete in-game cues aimed at short-lived frames, alternate routes, boss phases, HUD states and effects that are easy to miss
- mission completion requires the exact `VERIFIED_IN_GAME` attestation; tile/palette/image growth and heuristics can never auto-complete another mission
- repeated mission sessions remain backed by real MesenCE capture snapshots and the existing Capture Mission Control manifest
- added metadata-only `CAPTURE_MARATHON.html` / JSON dashboard showing completed and pending capture work
- added `windows/Guided_Capture_Marathon.bat` + PowerShell one-click flow: verified-fullscreen ROM launch → mission-by-mission gameplay verification → safe evidence handoff
- upgraded `Local_Capture_Bridge.ps1` with scripted current/previous capture parameters so the marathon can hand off the exact same capture without forcing duplicate folder selection
- the marathon automatically runs Local Capture Bridge when the session ends and may optionally create the existing metadata-only GitHub evidence PR
- explicit capture regression still blocks promotion even when safe evidence is successfully generated
- added synthetic tests for mission ordering, attestation enforcement, real capture-session recording, no-growth behavior and report privacy
- added `GUIDED_CAPTURE_MARATHON.md`; ROADMAP/README advanced to make the marathon the fastest Gate A path
- ROADMAP Gate A–D remains unchanged until real local in-game evidence is actually recorded and reviewed; tooling itself earns no checkbox
- no ROM, save state, capture image payload, ripped commercial art/audio or emulator binary is committed

## 1.0.0-rc18 — GitHub Capture Evidence Triage

- added `capture_evidence_triage.py` as the GitHub/CI-side consumer for privacy-safe Local Capture Bridge snapshots
- evidence history now reports mapping growth, added/removed tile IDs, palettes and condition names, per-group mapping deltas and Capture Mission Control progress deltas
- latest safe snapshot receives an explicit `PASS_INCREMENTAL` / `BLOCKED` evidence gate and one ordered `DO THIS NEXT` action
- non-4x snapshots, missing referenced capture images, invalid metadata/privacy declarations and explicit `CAPTURE_REGRESSION` block the evidence baseline
- added Gate A `CANDIDATE_REVIEW` hints from condition-name signals while explicitly forbidding automatic ROADMAP checkbox completion
- upgraded `Project 002 Capture Evidence Guard` so evidence PRs are validated and triaged in CI with a human-readable GitHub Actions summary
- added synthetic tests for clean incremental evidence, explicit regression blocking, missing-image blocking, history deltas and ROADMAP non-auto-completion
- added `CAPTURE_EVIDENCE_TRIAGE.md` and advanced ROADMAP to include GitHub-side safe-evidence review before capture promotion
- ROADMAP Gate A–D remains 0/52 because tooling and heuristic signals are not local gameplay/art/QA proof
- no ROM, save state, capture image payload, ripped commercial art/audio or emulator binary is committed

## 1.0.0-rc17 — Privacy-safe Local Capture Bridge to GitHub evidence

- added `local_capture_bridge.py` to inspect a local MesenCE capture and emit a strict metadata-only `SAFE_CAPTURE_HANDOFF.json` / CSV / HTML dashboard
- handoff includes HD scale, capture fingerprint, mapping/tile/palette/condition counts, PLAYER/BOSS/ENEMY/WORLD/UI/EFFECTS grouping, image dimensions/sizes/hashes, Capture Mission Control state and capture-regression metadata without copying image pixels
- added `capture_evidence_validator.py` to reject unsupported schema, forbidden payload files, ROM/save/emulator/image payloads, absolute local paths and broken privacy declarations
- added `windows/Local_Capture_Bridge.bat` + PowerShell one-click flow with optional previous-capture comparison
- optional authenticated GitHub CLI path creates a remote evidence branch and PR containing only the validated JSON; the local ROM/capture directory is never staged into git
- added `.github/workflows/project-002-capture-evidence.yml` as a second server-side privacy guard for evidence PRs
- added the safe evidence inbox contract under `evidence/capture/`
- Authoritative Remaster Studio now exposes the bridge on F4 while F5 remains regression-safe capture promotion
- added synthetic privacy/regression tests plus Studio/Windows/workflow integration checks
- added `LOCAL_CAPTURE_BRIDGE.md`; README and ROADMAP now place safe evidence handoff before capture promotion
- ROADMAP Gate A–D remains 0/52 because tooling/evidence transport alone does not prove any local gameplay/art/QA checkbox complete
- no ROM, save state, capture image payload, ripped commercial art/audio or emulator binary is committed

## 1.0.0-rc16 — Authoritative Remaster Studio

- added `AuthoritativeRemasterStudio.py` as the production UI for the current Project #002 path instead of older mixed legacy flows
- directly exposes regression-safe capture promotion, Visual Completion Matrix, exact High-Impact Art Sprint preparation/finish, Pixel QA, verified-fullscreen playtest, Final Regression Cockpit and Final Release Gate
- added F1–F11 production shortcuts and `windows/Authoritative_Remaster_Studio.bat`
- added integration checks so authoritative Windows launchers and final gates remain wired into the Studio
- added `AUTHORITATIVE_REMASTER_STUDIO.md` and advanced the Project #002 milestone without inflating Gate A–D progress
- PR #42 merged only after Project 002 Tools and Roadmap Standard checks passed
- no ROM, save state, ROM-derived capture, commercial art/audio or emulator binary is committed

## 1.0.0-rc15 — Exact High-Impact Art Sprint execution

- added `high_impact_art_sprint.py` to turn the exact Visual Completion Matrix `NEXT_HIGH_IMPACT_ART_BATCH` into an immediately editable local production sprint
- removes the ranking-to-execution mismatch: the graphics measured as the highest-impact unfinished work are now the exact graphics exported for the next art session
- sprint manifest records impact score/reasons, dimensions and SHA-256 MasterWorkspace state while local editable/reference PNGs and contact board remain uncommitted
- finish path reuses stale-conflict protection, exact-dimension checks, byte-preserved `hires.txt`, candidate-pack composition and Pixel QA
- added `windows/High_Impact_Art_Sprint.bat` and `windows/Finish_High_Impact_Art_Sprint.bat` plus PowerShell orchestration for Windows one-click prepare/finish
- added synthetic tests for exact matrix-to-kit selection, safe Pixel-QA finish and protection against implicit overwrite of an existing artist sprint
- added `HIGH_IMPACT_ART_SPRINT.md` and advanced ROADMAP so the default art-production loop executes the matrix-selected batch directly
- PR #41 CI passes Python compile, full unit tests and PowerShell parse before merge
- no ROM, save state, ROM-derived capture, ripped commercial art/audio, emulator binary or local derivative PNG is committed

## 1.0.0-rc14 — Visual Completion Matrix + high-impact art batch

- added `visual_completion_matrix.py` to quantify captured-art completion by PLAYER / BOSS / ENEMY / WORLD / UI / EFFECTS / UNASSIGNED
- joins Mesen HD-pack mappings, `ART_QUEUE.csv` classification and `MasterWorkspace/ART_STATE.csv` without copying captured PNG payloads into reports
- added master-count, usage-weighted and production-weighted completion metrics so visible player/boss/enemy work carries more production importance than low-impact tiles
- invalid masters, UNASSIGNED classification blockers and high-reuse graphics are promoted automatically
- added bounded `NEXT_HIGH_IMPACT_ART_BATCH.csv` so each art session starts from the strongest visible-impact backlog instead of a flat TODO list
- added metadata-only JSON/CSV/HTML Visual Completion reports and Windows one-click `Visual_Completion_Matrix.bat` + PowerShell picker
- added synthetic tests for per-group completion, invalid-boss prioritization, bounded batches and report privacy
- advanced README/ROADMAP to insert Visual Completion Matrix between capture/review and final-art sprint execution
- PR #39 merged only after green Python compile, unit tests and PowerShell parse; post-merge main CI also passed
- no ROM, save state, ROM-derived capture, ripped commercial art/audio, emulator binary or local derivative artwork is committed

## 1.0.0-rc13 — Final Release Readiness Director

- added `final_release_director.py` as the final packaging-authoritative Project #002 decision layer
- final authorization now requires seven green gates: HD Pack structure, capture coverage, final art, Visual Context, current Pixel QA, verified fullscreen and 10/10 Final Regression Cockpit
- missing, failed or stale fullscreen evidence blocks packaging even when the earlier release candidate audit is otherwise green
- Pixel QA, fullscreen and regression evidence must all refer to the exact current runtime fingerprint
- added metadata-only `FINAL_RELEASE_READINESS.json` and HTML dashboard with one ordered `DO THIS NEXT` stage
- added `windows/Final_Release_Gate.bat` + PowerShell picker flow and gated ZIP creation after PASS
- added synthetic tests for fullscreen bypass prevention, stale evidence, all-green authorization, blocker ordering and dashboard privacy
- added `FINAL_RELEASE_READINESS_DIRECTOR.md` and advanced ROADMAP to the final exact-build release decision
- no ROM, save state, ROM-derived capture, ripped commercial art/audio, emulator binary or derivative pack is committed

## 1.0.0-rc12 — Verified fullscreen one-click HD playtest

- upgraded the QA-gated playtest to launch the user's local ROM in MesenCE automatically with fullscreen requested
- added Win32 active-monitor bounds verification and F11 retry; a windowed-only launch is rejected instead of silently accepted
- added exact-build `FULLSCREEN_PLAYTEST.json` evidence tied to the current `hires.txt + runtime PNG` fingerprint
- runtime-art changes make older fullscreen evidence stale automatically
- added synthetic fullscreen argument/evidence/staleness tests and Windows PowerShell validation
- added `FULLSCREEN_PLAYTEST.md` and advanced ROADMAP to fullscreen-by-contract finalization
- no ROM, save state, emulator binary or local gameplay capture is committed

## 1.0.0-rc11 — Regression-safe Capture Promotion Director

- added `capture_promotion_director.py` to turn a fresh local MesenCE capture into a safe high-speed production handoff
- candidate capture is validated and compared with the previous accepted capture before production state is touched
- any `CAPTURE_REGRESSION` blocks promotion and preserves the existing art queue/workspace
- a clean candidate can then run resume-safe sync, Visual Context, Animation Family, Final Art Priority and Production Sprint refresh in one pass
- optional sprint creation prepares the next Top-N art batch immediately
- added metadata-only Capture Promotion reports, Windows launcher, synthetic regression-protection tests and `CAPTURE_PROMOTION_DIRECTOR.md`
- no capture art, ROM, save state, ripped commercial asset or emulator binary is committed

## 1.0.0-rc10 — Authoritative Final Regression release gate

- unified the final release gate with Final Regression Cockpit PASS / FAIL / STALE / PENDING semantics
- current-build FAIL evidence now blocks release directly and retains failure category/notes
- runtime PNG/`hires.txt` changes invalidate earlier regression PASS evidence at the release layer
- upgraded legacy regression completion to schema-2 history instead of bypassing cockpit semantics
- release dashboard now exposes exact regression counts and the next blocking case
- added synthetic propagation/staleness/migration tests and `AUTHORITATIVE_FINAL_RELEASE_GATE.md`

## 1.0.0-rc9 — Exact-build Final Regression Cockpit

- added `final_regression_cockpit.py` with ten authoritative whole-game visual regression cases
- each case records PASS / FAIL / STALE / PENDING evidence tied to the exact runtime fingerprint
- added failed-case-first `DO THIS NEXT` ordering and defect categories for capture, mapping, palette, animation, transparency and coverage problems
- added standalone Tk GUI, Windows launcher and metadata-only HTML/JSON cockpit reports
- runtime-art changes automatically stale older passes
- added synthetic fail/retest/staleness/dashboard tests and `FINAL_REGRESSION_COCKPIT.md`

## 1.0.0-rc8 — Production Sprint Control Center

- added `production_sprint.py` to combine Capture Mission Control, Capture Gap, Visual Context, Animation Family, MasterWorkspace and Final Art Priority evidence into one metadata-only `DO THIS NEXT` dashboard
- added `Reports/ProductionSprint/PRODUCTION_SPRINT.html` + JSON output with ordered next actions instead of separate disconnected reports
- promoted capture regressions and incomplete capture missions above art work so a newer-but-poorer capture cannot silently become the production baseline
- upgraded the main `TinyToonRemasterStudio.py` GUI to expose Capture Gap Planner, Visual Context, Animation Families, Final Art Priority and Final Art Sprint actions directly
- added adjustable Top-N sprint size plus GUI `Create Top-N Art Sprint`, `Open CurrentArtSprint` and `Finish Sprint + Pixel QA`
- Studio workspace instructions now describe the actual capture → Production Sprint → art sprint → QA → playtest loop
- wired the unified Production Sprint dashboard through `studio_command_center.py`
- added synthetic tests for combined production status, actionable capture/art blockers, metadata-only output and Studio orchestration
- added `PRODUCTION_SPRINT_CONTROL_CENTER.md` and refreshed README/ROADMAP around the GUI-first workflow
- no ROM, save state, ROM-derived capture, ripped commercial art/audio, emulator binary, sprint graphic or derivative final pack is committed

## 1.0.0-rc7 — Final Art Sprint Kit

- added `art_sprint_kit.py` to turn the evidence-driven Top-N Final Art Priority list into a focused local batch-edit folder
- sprint export copies only the highest-priority unfinished masters into `editable/`, preserves untouched `reference/` copies and records exact dimensions plus SHA-256 workspace state
- added local `LOCAL_ART_SPRINT_BOARD.png` ordered by redraw priority so a real art session can work from one visual board instead of hunting across the full MasterWorkspace
- sprint import is stale-workspace aware: if the same master changed after export and the sprint also changed it, import blocks instead of silently overwriting newer work
- resized/missing sprint graphics are rejected before they can reach the authoritative MasterWorkspace
- added one-command `finish` path: safe import → combined HD composition → `hires.txt` preservation → structural validation → Pixel QA
- wired sprint creation/finalization into `studio_command_center.py`
- explicitly gitignored Project `Artwork/` and `Reports/` because sprint/contact-sheet/report folders can contain local ROM-derived graphics
- added synthetic tests for Top-N export, batch roundtrip, stale conflict blocking, dimension rejection and successful QA-gated finish
- added `FINAL_ART_SPRINT_KIT.md` and advanced README/ROADMAP from priority planning into repeatable real-art execution
- no ROM, save state, ROM-derived capture, ripped commercial art/audio, emulator binary, sprint graphic or derivative final pack is committed

## 1.0.0-rc6 — Final art priority board

- added `final_art_priority.py` to rank unfinished captured graphics by expected visible HD impact
- combines art-group importance, reuse count, Visual Context risk, Animation Family risk, MasterWorkspace state and classification blockers into one score
- already edited masters automatically disappear from the work queue; invalid masters and UNASSIGNED blockers are promoted
- added metadata-only `FINAL_ART_NEXT.csv`, `FINAL_ART_PRIORITY.json` and HTML dashboard
- added Studio orchestration through `final_art_priority_dashboard(...)`
- added synthetic tests proving edited masters are skipped, high-impact PLAYER/BOSS work is prioritized and reports contain no PNG payloads
- added `FINAL_ART_PRIORITY_BOARD.md` and advanced ROADMAP/README toward an evidence-driven redraw loop
- no ROM, save state, ROM-derived capture, ripped commercial art/audio, emulator binary or derivative pack is committed

## 1.0.0-rc5 — Capture gap planner + targeted capture queue

- added `capture_gap_planner.py` to compare repeated local MesenCE captures and build a ranked `CAPTURE NEXT` queue
- coverage present in an older capture but missing from the current one is promoted to `CAPTURE_REGRESSION` with the highest planner priority
- added advisory PLAYER / BOSS / ENEMY state-gap suggestions derived from semantic animation families and a generic state vocabulary
- pending Capture Mission Control items are merged into the same queue so manual whole-game coverage and structural animation evidence can be worked together
- mixed / UNASSIGNED families are promoted as classification-capture targets where a clearer gameplay context can improve grouping
- added `CAPTURE_NEXT.csv`, `CAPTURE_GAP_PLAN.json` and a metadata-only HTML dashboard; no captured artwork is embedded in reports
- explicitly kept state-gap suggestions advisory: they never prove a state exists and never auto-complete Capture Mission Control
- wired capture-gap reports into `studio_command_center.py`
- added synthetic tests for state-gap detection, new-state progress, capture-regression detection, mission prioritization, Studio orchestration and report privacy
- updated README/ROADMAP and added `CAPTURE_GAP_PLANNER.md`
- no ROM, save state, ROM-derived capture, ripped commercial art/audio, emulator binary or derivative pack is committed

## 1.0.0-rc4 — Animation family workbench + enforced visual-context release gate

- added `animation_workbench.py` to group Mesen condition-driven states into semantic animation families for player/enemy/boss production review
- added condition-cooccurrence sprite/metatile candidates without treating HD texture-sheet coordinates as on-screen geometry
- added local-only animation contact sheets for inspecting related captured frames together; these outputs remain gitignored and are never release assets
- added fingerprinted `ANIMATION_FAMILY_REVIEW.csv`; capture/art changes make prior family reviews stale
- added metadata-only HTML/JSON Animation Workbench dashboard and synthetic tests
- fixed the rc3 release-gate mismatch: `release_candidate.py` now actually requires a current `VISUAL_CONTEXT_REVIEW.csv` with no pending/stale high-risk families
- wired visual-context and animation-family dashboards into `studio_command_center.py`
- updated release CLI to require `--visual-review`
- updated README/ROADMAP and added `ANIMATION_WORKBENCH.md`
- no ROM, save state, ROM-derived capture, ripped commercial art/audio, emulator binary, local contact sheet or derivative final pack is committed

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
- added `bound_art_qa.py` so the existing pixel-safe Art QA result can be bound to the exact output build
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