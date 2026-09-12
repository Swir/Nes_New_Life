# Project #002 — Tiny Toon Visual Remaster

## Goal

Project #002 is a **visual remaster workflow**, not a rewrite of the game. The user supplies their own NES ROM locally; that ROM remains the source of gameplay, physics, level layouts, enemies, scrolling, timing and logic. The project builds a higher-resolution presentation layer through **MesenCE HD Packs**.

MesenCE records tile/palette combinations seen during gameplay into PNG sheets plus `hires.txt`. We modernize only the captured presentation data while preserving the original ROM-driven game underneath.

> Project #002 targets the actively maintained `nesdev-org/MesenCE` Community Edition workflow.

## Verified local ROM profile

- iNES: valid
- PRG ROM: 128 KiB
- CHR ROM: 128 KiB
- mapper: 4 (MMC3)
- mirroring: horizontal
- trainer: no
- battery flag: no
- SHA-1: `110796622e50c2e8c20b1430acadc5bae5f36586`
- SHA-256: `688fe19096d8060decf9581165d52400a6d9b1cab79e7ef4cf9a66a794baf45f`

The hashes identify the user's local ROM only. The ROM itself must never be committed.

## Recommended controls

| PC key | NES control |
|---|---|
| Arrow keys | D-pad |
| Z | A |
| X | B |
| Enter | Start |
| Right Shift | Select |
| F11 | Fullscreen toggle |
| Esc | Emulator/menu |

Gamepads are configured through MesenCE. The remaster does not alter the original control logic.

## Windows 11 quick start

From `projects/002_tiny_toon_visual_remaster/windows/`:

```text
Start_Remaster.bat
```

This installs/verifies MesenCE locally, asks for the user-supplied ROM, verifies the Project #002 fingerprint and launches it without copying the ROM into the repository.

For the fastest capture-to-playtest loop:

```text
Build_HD_Playtest.bat
```

The playtest builder creates a QA-gated HD Pack, deploys it into the user's local MesenCE `HdPacks/<ROM stem>` folder while backing up the previously installed pack, then launches the user's local ROM automatically. Fullscreen is a Project #002 playtest requirement: the launcher requests native MesenCE fullscreen, checks the actual emulator window against the active monitor and retries with F11 before accepting the launch. Exact-build fullscreen evidence is written under `Reports/FullscreenPlaytest/`.

See `FULLSCREEN_PLAYTEST.md`.

### Local Capture Bridge — safe local → GitHub handoff

To move capture **evidence** into the GitHub workflow without moving the ROM or capture images, run:

```text
windows/Local_Capture_Bridge.bat
```

The bridge reads the current MesenCE capture locally, optionally compares it with the previous accepted capture, and writes only metadata under `Reports/LocalCaptureBridge/`: mapping/tile/palette/condition counts, PLAYER/BOSS/ENEMY/WORLD/UI/EFFECTS group counts, image dimensions/sizes/SHA-256 hashes, Capture Mission Control state and capture-regression metadata. It does **not** copy image pixels, ROM bytes, save states, emulator binaries or absolute local paths into the handoff.

`capture_evidence_validator.py` validates the privacy contract. If GitHub CLI (`gh`) is installed and authenticated, the Windows bridge can optionally send only `SAFE_CAPTURE_HANDOFF.json` to a new GitHub evidence PR through the API. `.github/workflows/project-002-capture-evidence.yml` validates the evidence again before it can be trusted. Evidence arrival never auto-completes ROADMAP Gate A–D.

See `LOCAL_CAPTURE_BRIDGE.md`.

## Production workflow

The current high-impact path is:

`MesenCE capture → Local Capture Bridge → Capture Mission Control → Capture Promotion Director → incremental sync → Visual Context Audit → Animation Family Workbench → Visual Completion Matrix → Final Art Priority / high-impact batch → Final Art Sprint Kit → build-bound Pixel QA → one-click verified-fullscreen playtest → Final Regression Cockpit → Final Release Readiness Director → gated ZIP`

`tools/AuthoritativeRemasterStudio.py` is the preferred current production interface. F4 launches the Local Capture Bridge, F5 runs regression-safe capture promotion, and the remaining Studio actions follow the current high-impact art / QA / release path. The older `TinyToonRemasterStudio.py` remains available for compatibility.

### Production Sprint Control Center

The **PRODUCTION SPRINT** button is the normal starting point after selecting a current MesenCE capture. It writes `Reports/ProductionSprint/PRODUCTION_SPRINT.html` and combines:

- Capture Mission Control completion,
- capture regressions / next capture targets,
- Visual Context pending/stale review,
- Animation Family review,
- MasterWorkspace TODO/INVALID progress,
- highest-impact Final Art Priority items.

The dashboard produces one ordered **DO THIS NEXT** list. It remains evidence-driven: it never marks unseen game states complete and does not replace the final full-game regression gate.

See `PRODUCTION_SPRINT_CONTROL_CENTER.md`.

## Capture coverage

Capture at **4x Prescale** with MesenCE HD Pack Builder and deliberately trigger every relevant menu, route, movement/action state, enemy, boss phase, HUD/text state, effect, transition and ending screen.

`capture_mission_control.py` tracks explicit gameplay coverage. Structural capture growth alone never auto-completes a mission.

```bash
python tools/capture_mission_control.py init "C:\\TinyToonWork\\CAPTURE_MISSIONS.json"
python tools/capture_mission_control.py record "C:\\TinyToonWork\\CAPTURE_MISSIONS.json" "C:\\TinyToonWork\\MesenCapture" --complete player_idle_walk_run
```

### Capture Gap Planner

Between targeted play sessions, compare the previous and current capture:

```bash
python tools/capture_gap_planner.py \
  "C:\\TinyToonWork\\Capture_Current" \
  --previous "C:\\TinyToonWork\\Capture_Previous" \
  --queue "C:\\TinyToonWork\\Artwork\\ART_QUEUE.csv" \
  --capture-manifest "C:\\TinyToonWork\\CAPTURE_MISSIONS.json" \
  --output "C:\\TinyToonWork\\Reports\\CaptureGapPlanner"
```

The planner creates `CAPTURE_NEXT.csv` and a metadata-only dashboard. It puts lost previous coverage at the top as `CAPTURE_REGRESSION`, then combines pending Capture Mission Control items with advisory PLAYER/BOSS/ENEMY state gaps and classification targets.

The generic missing-state vocabulary is **advisory only**. It never proves that a specific state exists in this game and never marks Capture Mission Control complete. See `CAPTURE_GAP_PLANNER.md`.

## Visual Context Audit

`visual_context_audit.py` groups captured uses by tile ID and ranks families that are likely to cause visible HD mistakes across multiple palettes, Mesen conditions or distinct captured variants. Reviews are fingerprinted, so later capture/art changes can invalidate old evidence.

```bash
python tools/visual_context_audit.py sync \
  "C:\\TinyToonWork\\ModernizedPack\\final_art" \
  "C:\\TinyToonWork\\Artwork\\VISUAL_CONTEXT_REVIEW.csv" \
  --queue "C:\\TinyToonWork\\Artwork\\ART_QUEUE.csv"
```

The authoritative release gate **requires** this review file to exist and have no pending/stale high-risk families.

## Animation Family Workbench

`animation_workbench.py` groups condition-driven states into semantic families such as player/enemy/boss animation sets. It also emits condition-cooccurrence candidates for tiles that should be inspected together in MesenCE.

```bash
python tools/animation_workbench.py dashboard \
  "C:\\TinyToonWork\\ModernizedPack\\final_art" \
  --queue "C:\\TinyToonWork\\Artwork\\ART_QUEUE.csv" \
  --review "C:\\TinyToonWork\\Artwork\\ANIMATION_FAMILY_REVIEW.csv" \
  --output "C:\\TinyToonWork\\Reports\\AnimationWorkbench"
```

Optional local contact sheets can be generated with `animation_workbench.py contact-sheets`. They may contain ROM-derived captured graphics and therefore must stay local/gitignored. The normal dashboard is metadata-only.

Important boundary: HD texture-sheet coordinates are **not** treated as on-screen sprite coordinates. Assembly candidates are review hints only and require in-game verification.

## Visual Completion Matrix

After a capture is promoted and MasterWorkspace is synchronized, run:

```text
windows/Visual_Completion_Matrix.bat
```

or from Python:

```bash
python tools/visual_completion_matrix.py \
  "C:\\TinyToonWork\\ModernizedPack\\final_art" \
  "C:\\TinyToonWork\\Reports\\VisualCompletion" \
  --queue "C:\\TinyToonWork\\Artwork\\ART_QUEUE.csv" \
  --workspace "C:\\TinyToonWork\\Artwork\\MasterWorkspace" \
  --batch-size 40
```

The matrix reports captured-art completion separately for PLAYER, BOSS, ENEMY, WORLD, UI, EFFECTS and UNASSIGNED, plus usage-weighted and production-weighted progress. It generates `NEXT_HIGH_IMPACT_ART_BATCH.csv`, promoting invalid masters, PLAYER/BOSS work, classification blockers and high-reuse graphics so art sessions target visible game impact first.

The percentage is intentionally **capture-bounded**. It never means the whole game is complete unless Capture Mission Control is complete too. Reports are metadata-only and do not copy captured PNG artwork.

See `VISUAL_COMPLETION_MATRIX.md`.

## Final Art Priority Board

After capture sync and review passes, generate a ranked list of the captured graphics whose completion should produce the largest visible HD improvement:

```bash
python tools/final_art_priority.py \
  "C:\\TinyToonWork\\ModernizedPack\\final_art" \
  "C:\\TinyToonWork\\Reports\\FinalArtPriority" \
  --queue "C:\\TinyToonWork\\Artwork\\ART_QUEUE.csv" \
  --workspace "C:\\TinyToonWork\\Artwork\\MasterWorkspace" \
  --visual-review "C:\\TinyToonWork\\Artwork\\VISUAL_CONTEXT_REVIEW.csv" \
  --animation-review "C:\\TinyToonWork\\Artwork\\ANIMATION_FAMILY_REVIEW.csv" \
  --top 20
```

`FINAL_ART_NEXT.csv` combines reuse, PLAYER/BOSS/ENEMY importance, context/animation risk, MasterWorkspace state and classification blockers. Already edited masters disappear automatically. The HTML/JSON reports are metadata-only and contain no captured artwork.

## Final Art Sprint Kit

Turn the priority ranking directly into a focused batch-edit folder:

```bash
python tools/art_sprint_kit.py export \
  "C:\\TinyToonWork\\ModernizedPack\\final_art" \
  "C:\\TinyToonWork\\Artwork\\MasterWorkspace" \
  "C:\\TinyToonWork\\Artwork\\CurrentArtSprint" \
  --queue "C:\\TinyToonWork\\Artwork\\ART_QUEUE.csv" \
  --visual-review "C:\\TinyToonWork\\Artwork\\VISUAL_CONTEXT_REVIEW.csv" \
  --animation-review "C:\\TinyToonWork\\Artwork\\ANIMATION_FAMILY_REVIEW.csv" \
  --top 20 --overwrite
```

The sprint contains `editable/`, untouched `reference/`, a manifest with exact hashes/dimensions and a local priority contact board. Edit only the sprint `editable/*.png`, keep dimensions unchanged and do not rename files.

Finish the batch in one command:

```bash
python tools/art_sprint_kit.py finish \
  "C:\\TinyToonWork\\ModernizedPack\\final_art" \
  "C:\\TinyToonWork\\Artwork\\MasterWorkspace" \
  "C:\\TinyToonWork\\Artwork\\CurrentArtSprint" \
  "C:\\TinyToonWork\\ModernizedPack\\sprint_output" \
  --overwrite
```

The finish path is conflict-safe and performs `safe import → composition → hires.txt preservation → validation → pixel QA`. If the same workspace master changed after sprint export, import blocks instead of overwriting newer work. In Studio these are the **Create Top-N Art Sprint** and **Finish Sprint + Pixel QA** buttons.

See also `FINAL_ART_SPRINT_KIT.md`, `FINAL_ART_PRIORITY_BOARD.md`, `VISUAL_COMPLETION_MATRIX.md`, `ANIMATION_WORKBENCH.md` and `VISUAL_CONTEXT_AUDIT.md`.

## Art production

Generate the ranked/grouped art queue and persistent `MasterWorkspace`. For broad manual work, edit `Artwork/MasterWorkspace/editable/*.png`; for focused sessions, use `Artwork/CurrentArtSprint/editable/*.png` and finish through the sprint safety path.

- exact duplicates may be propagated safely,
- near duplicates remain review hints only,
- `UNASSIGNED` stays explicit until classified,
- automatic baseline art is only a fast playable starting point, not a claim of final artwork,
- Pixel QA blocks unauthorized changes outside approved master regions,
- sprint import blocks stale-workspace conflicts and resized assets.

## Final release gate

`final_release_director.py` is the packaging-authoritative final release decision. PASS requires the same current runtime build to have all seven gates green:

- structurally valid 4x HD Pack,
- complete Capture Mission Control evidence,
- zero TODO and zero UNASSIGNED final-art work,
- current Visual Context Review with no pending/stale high-risk families,
- current build-bound Pixel Art QA PASS,
- verified fullscreen playtest PASS for the exact current runtime fingerprint,
- Final Regression Cockpit 10/10 PASS for the exact current runtime fingerprint.

Any late `hires.txt` or runtime-PNG change invalidates old exact-build QA/fullscreen/regression evidence. Packaging remains blocked until the changed build is re-tested.

Windows one-click final gate:

```text
windows/Final_Release_Gate.bat
```

See `FINAL_RELEASE_READINESS_DIRECTOR.md` and `FINAL_REGRESSION_COCKPIT.md`.

## Main tools

- `rom_probe.py` — local ROM inspector and CHR reference exporter
- `prepare_workspace.py` — local workspace preparation without copying the ROM
- `validate_hdpack.py` — `hires.txt`, PNG and coordinate validation
- `hdpack_pipeline.py` — structural capture analysis/diffing, queue, preview and reports
- `capture_mission_control.py` — explicit full-game capture mission tracking
- `capture_gap_planner.py` — repeated-capture regression detection and ranked `CAPTURE NEXT` planning
- `local_capture_bridge.py` — privacy-safe local capture → metadata-only GitHub evidence handoff
- `capture_evidence_validator.py` — schema/privacy guard that rejects paths and forbidden payloads
- `capture_promotion_director.py` — regression-safe fresh-capture promotion into production
- `production_sprint.py` — unified metadata-only `DO THIS NEXT` dashboard across capture/review/art evidence
- `production_sync.py` — resume-safe repeated-capture synchronization
- `art_production.py` — workboards, exact dedupe, near-duplicate hints and master propagation
- `visual_context_audit.py` — palette/condition/visual-variant family risk audit
- `animation_workbench.py` — semantic animation-family grouping, condition-cooccurrence candidates and local contact sheets
- `visual_completion_matrix.py` — per-group captured-art completion plus next high-impact art batch
- `final_art_priority.py` — evidence-driven `FINAL ART NEXT` ranking for highest-impact unfinished captured graphics
- `art_sprint_kit.py` — Top-N local editing kit, stale-safe import and one-step compose/Pixel-QA finish
- `art_workspace.py` — persistent batch master-art workspace
- `auto_art_pass.py` — automatic baseline modernization for untouched masters
- `art_qa.py` / `bound_art_qa.py` — pixel-safe QA and exact-build binding
- `rapid_hd_playtest.py` — capture → sync → baseline → apply → QA → optional MesenCE deploy
- `fullscreen_launch.py` — verified-fullscreen exact-build evidence and stale-evidence checks
- `final_regression_cockpit.py` — exact-build 10-case full-game visual regression evidence
- `final_release_director.py` — authoritative seven-gate release/package decision
- `studio_command_center.py` — GUI-facing orchestration layer
- `AuthoritativeRemasterStudio.py` — current F4–F11 privacy/capture/art/QA/release production GUI
- `TinyToonRemasterStudio.py` — legacy-compatible broader production GUI
- `windows/Start_Remaster.bat` — one-click Windows launcher
- `windows/Local_Capture_Bridge.bat` — one-click privacy-safe local evidence + optional GitHub PR
- `windows/Build_HD_Playtest.bat` — one-click QA-gated build/deploy + verified-fullscreen MesenCE launch
- `windows/Visual_Completion_Matrix.bat` — one-click captured-art completion dashboard and high-impact batch
- `windows/Final_Release_Gate.bat` — one-click seven-gate final audit/package flow

## Python

Python 3.11+ is recommended.

```bash
python -m pip install -r requirements.txt
```

Pillow is used for PNG processing, workboards, validation and QA.

## Copyright / repository rule

Do not commit ROMs, emulator save states, Mesen captures made from commercial graphics, ripped game artwork/audio, locally generated derivative preview/final packs, local animation contact sheets, Final Art Sprint Kit graphics or downloaded emulator binaries. `Artwork/` and `Reports/` are explicitly gitignored because they may contain ROM-derived local production assets. Public commits contain tooling, synthetic tests, documentation, original project metadata and validator-approved metadata-only capture evidence — never the capture image payload itself.
