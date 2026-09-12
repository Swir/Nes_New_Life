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

## Production workflow

The current high-impact path is:

`MesenCE capture → Capture Mission Control → Capture Promotion Director → incremental sync → Visual Context Audit → Animation Family Workbench → Final Art Priority Board → Final Art Sprint Kit → build-bound Pixel QA → one-click verified-fullscreen playtest → exact-build regression → Unified Release Candidate Gate → gated ZIP`

`tools/TinyToonRemasterStudio.py` is now the preferred end-to-end interface. The main window exposes the recent capture-gap, visual-context, animation-family, priority-board and Final Art Sprint tools directly instead of requiring separate CLI commands.

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

See also `FINAL_ART_SPRINT_KIT.md`, `FINAL_ART_PRIORITY_BOARD.md`, `ANIMATION_WORKBENCH.md` and `VISUAL_CONTEXT_AUDIT.md`.

## Art production

Generate the ranked/grouped art queue and persistent `MasterWorkspace`. For broad manual work, edit `Artwork/MasterWorkspace/editable/*.png`; for focused sessions, use `Artwork/CurrentArtSprint/editable/*.png` and finish through the sprint safety path.

- exact duplicates may be propagated safely,
- near duplicates remain review hints only,
- `UNASSIGNED` stays explicit until classified,
- automatic baseline art is only a fast playable starting point, not a claim of final artwork,
- Pixel QA blocks unauthorized changes outside approved master regions,
- sprint import blocks stale-workspace conflicts and resized assets.

## Final release gate

`release_candidate.py` is the authoritative final release decision. PASS requires the same current runtime build to have:

- structurally valid 4x HD Pack,
- complete Capture Mission Control evidence,
- zero TODO art-queue rows,
- zero UNASSIGNED art-queue rows,
- current Visual Context Review with no pending/stale high-risk families,
- current build-bound Pixel Art QA PASS,
- completed full-game visual regression for the current runtime fingerprint,
- no ROM/save-state/patch payloads.

Project acceptance additionally requires the final user-facing playtest to be run in verified fullscreen. `tools/fullscreen_launch.py status` detects stale fullscreen evidence after a runtime art/mapping change.

```bash
python tools/release_candidate.py audit "C:\\TinyToonWork\\ModernizedPack\\final_art" \
  --capture "C:\\TinyToonWork\\CAPTURE_MISSIONS.json" \
  --queue "C:\\TinyToonWork\\Artwork\\ART_QUEUE.csv" \
  --visual-review "C:\\TinyToonWork\\Artwork\\VISUAL_CONTEXT_REVIEW.csv" \
  --art-qa "C:\\TinyToonWork\\Reports\\ArtQA\\ART_QA_RESULT.json" \
  --regression "C:\\TinyToonWork\\FINAL_REGRESSION.json" \
  --output "C:\\TinyToonWork\\Reports\\ReleaseCandidate"
```

## Main tools

- `rom_probe.py` — local ROM inspector and CHR reference exporter
- `prepare_workspace.py` — local workspace preparation without copying the ROM
- `validate_hdpack.py` — `hires.txt`, PNG and coordinate validation
- `hdpack_pipeline.py` — structural capture analysis/diffing, queue, preview and reports
- `capture_mission_control.py` — explicit full-game capture mission tracking
- `capture_gap_planner.py` — repeated-capture regression detection and ranked `CAPTURE NEXT` planning
- `production_sprint.py` — unified metadata-only `DO THIS NEXT` dashboard across capture/review/art evidence
- `production_sync.py` — resume-safe repeated-capture synchronization
- `art_production.py` — workboards, exact dedupe, near-duplicate hints and master propagation
- `visual_context_audit.py` — palette/condition/visual-variant family risk audit
- `animation_workbench.py` — semantic animation-family grouping, condition-cooccurrence candidates and local contact sheets
- `final_art_priority.py` — evidence-driven `FINAL ART NEXT` ranking for highest-impact unfinished captured graphics
- `art_sprint_kit.py` — Top-N local editing kit, stale-safe import and one-step compose/Pixel-QA finish
- `art_workspace.py` — persistent batch master-art workspace
- `auto_art_pass.py` — automatic baseline modernization for untouched masters
- `art_qa.py` / `bound_art_qa.py` — pixel-safe QA and exact-build binding
- `rapid_hd_playtest.py` — capture → sync → baseline → apply → QA → optional MesenCE deploy
- `fullscreen_launch.py` — verified-fullscreen exact-build evidence and stale-evidence checks
- `release_candidate.py` — authoritative final release gate
- `studio_command_center.py` — GUI-facing orchestration layer
- `TinyToonRemasterStudio.py` — main Production Sprint / art / QA / release GUI
- `windows/Start_Remaster.bat` — one-click Windows launcher
- `windows/Build_HD_Playtest.bat` — one-click QA-gated build/deploy + verified-fullscreen MesenCE launch

## Python

Python 3.11+ is recommended.

```bash
python -m pip install -r requirements.txt
```

Pillow is used for PNG processing, workboards, validation and QA.

## Copyright / repository rule

Do not commit ROMs, emulator save states, Mesen captures made from commercial graphics, ripped game artwork/audio, locally generated derivative preview/final packs, local animation contact sheets, Final Art Sprint Kit graphics or downloaded emulator binaries. `Artwork/` and `Reports/` are explicitly gitignored because they may contain ROM-derived local production assets. Public commits contain tooling, synthetic tests, documentation and original project metadata only.
