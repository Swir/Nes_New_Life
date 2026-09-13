# Project #002 — Smart Guided Capture Marathon

`windows/Guided_Capture_Marathon.bat` is the fastest evidence-first path for completing **Gate A — Complete local capture** without pretending that structural tile growth proves gameplay coverage.

## What one run does

1. asks for the current MesenCE HD Pack capture folder and the user's legally supplied local ROM,
2. optionally asks for the previous accepted capture for regression comparison,
3. runs Capture Integrity Ledger before launch and classifies the session as `CLEAN`, `GAMEPLAY_RECOVERY_REQUIRED` or `HARD_BLOCKED`,
4. automatically refreshes Capture Gap Planner and shows the highest-impact missing/regressed families and states,
5. launches the ROM through the verified-fullscreen MesenCE launcher when gameplay is safe,
6. if verified history regressed, enters **Gameplay Recovery Mode** so the missing coverage can be recreated in the real game,
7. unlocks `VERIFIED_IN_GAME` mission recording only after the live capture returns to structural admission `PASS`,
8. loads the 11 explicit Capture Mission Control missions and adds current Capture Gap Planner focus items to each mission,
9. records a mission only after the user explicitly presses **V = verified in game**,
10. writes/refreshes the metadata-only Capture Marathon dashboard,
11. immediately runs Local Capture Bridge against the same capture and can optionally create the safe metadata-only GitHub evidence PR.

## Recovery Mode removes a real deadlock

Older versions failed closed before launching MesenCE whenever the current capture was below verified historical coverage. That correctly protected evidence, but it also made the normal repair path awkward: the user needed gameplay to recreate missing tiles/palettes/images while the guided gameplay launcher refused to start.

The new split is stricter and more useful:

- `HARD_BLOCKED` — wrong 4x scale or referenced capture images are missing. Gameplay recovery is not started because the capture/settings must be fixed first.
- `GAMEPLAY_RECOVERY_REQUIRED` — historical coverage regressed or verified mission evidence became structurally at risk. MesenCE may launch specifically to recover the missing gameplay coverage, but mission recording remains locked.
- `CLEAN` — structural admission is `PASS`; explicit mission evidence may be recorded.

Recovery targets contain the exact regressed metric, current value, verified historical minimum and deficit. The Windows runner also overlays current `CAPTURE_GAP_PLAN.json` priorities so the operator sees which PLAYER/BOSS/ENEMY/WORLD/UI/EFFECTS families or states are most valuable to revisit.

This does **not** weaken Capture Integrity Ledger. `confirm_mission()` still calls `assert_capture_admissible()` immediately before writing evidence. If the live capture is still regressed, `VERIFIED_IN_GAME` is rejected.

## Why explicit verification matters

A tile/palette/image count can grow while important animation or route states remain unseen. It can also stay unchanged when a newly verified gameplay state legitimately reuses existing graphics.

For that reason `guided_capture_marathon.py` requires the exact internal attestation `VERIFIED_IN_GAME` before it calls Capture Mission Control. The Windows launcher supplies that attestation only after the user explicitly chooses **V** for the displayed mission.

Skipping a mission records nothing. Quitting early records nothing for the remaining missions. No heuristic or GitHub workflow can mark a mission complete.

## Mission set

The marathon walks through the same authoritative Capture Mission Control areas used by the release gate:

- boot/title/menu states,
- player movement,
- player actions/damage/death,
- normal routes and scrolling boundaries,
- alternate routes/secrets/revisits,
- common enemies,
- rare/route-specific enemies,
- every boss/phase/attack/hit/death/effect,
- HUD/text/pause/status/result screens,
- projectiles/effects/transitions,
- ending/credits/post-game states.

Each mission contains targeted cues plus live Capture Gap Planner focus intended to make short-lived frames, regressions and alternate contexts harder to miss.

## Fullscreen contract

The launcher delegates ROM startup to `launch_remaster.ps1`. That path verifies MesenCE fullscreen against the active monitor and refuses a windowed-only session. The ROM is run from its current local path and is never copied into the repository.

## Safe handoff after the marathon

At the end, Guided Capture Marathon calls Local Capture Bridge with the already selected capture. The bridge can therefore generate `SAFE_CAPTURE_HANDOFF.json` without asking the user to select the same folder again.

The handoff still contains metadata only. It never includes ROM bytes, capture PNG/JPG pixels, save states, emulator binaries, ripped art/audio or absolute local paths.

If regression comparison still detects lost coverage, the safe handoff may be produced for diagnosis, but capture promotion remains blocked.

## ROADMAP rule

Completing a Capture Mission Control mission is meaningful local evidence, but this tool does not directly edit `ROADMAP.md`. Project #002's Gate A–D checkboxes remain governed by reviewed authoritative evidence and the SWIR Roadmap Standard.

This distinction prevents a tool launch, recovery attempt, tile-count increase or heuristic guess from inflating the release percentage.