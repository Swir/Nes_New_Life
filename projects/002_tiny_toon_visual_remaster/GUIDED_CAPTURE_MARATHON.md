# Project #002 — Guided Capture Marathon

`windows/Guided_Capture_Marathon.bat` is the fastest evidence-first path for completing **Gate A — Complete local capture** without pretending that structural tile growth proves gameplay coverage.

## What one run does

1. asks for the current MesenCE HD Pack capture folder and the user's legally supplied local ROM,
2. optionally asks for the previous accepted capture for later regression comparison,
3. launches the ROM through the existing verified-fullscreen MesenCE launcher,
4. loads the 11 explicit Capture Mission Control missions,
5. presents concrete in-game cues for each pending mission,
6. records a mission only after the user returns to the console and explicitly presses **V = verified in game**,
7. writes/refreshes the local metadata-only Capture Marathon dashboard,
8. immediately runs Local Capture Bridge against the same capture,
9. validates the safe handoff and can optionally create the metadata-only GitHub evidence PR.

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

Each mission contains targeted cues intended to make short-lived frames and alternate contexts harder to miss.

## Fullscreen contract

The launcher delegates ROM startup to `launch_remaster.ps1`. That path verifies MesenCE fullscreen against the active monitor and refuses a windowed-only session. The ROM is run from its current local path and is never copied into the repository.

## Safe handoff after the marathon

At the end, Guided Capture Marathon calls Local Capture Bridge with the already selected capture. The bridge can therefore generate `SAFE_CAPTURE_HANDOFF.json` without asking the user to select the same folder again.

The handoff still contains metadata only. It never includes:

- ROM bytes,
- capture PNG/JPG pixels,
- save states,
- emulator binaries,
- ripped art/audio,
- absolute local paths.

If regression comparison detects lost coverage, the safe handoff may still be produced for diagnosis, but capture promotion remains blocked.

## ROADMAP rule

Completing a Capture Mission Control mission is meaningful local evidence, but this tool does not directly edit `ROADMAP.md`. Project #002's Gate A–D checkboxes remain governed by reviewed authoritative evidence and the SWIR Roadmap Standard.

This distinction prevents a tool launch, tile-count increase or heuristic guess from inflating the release percentage.
