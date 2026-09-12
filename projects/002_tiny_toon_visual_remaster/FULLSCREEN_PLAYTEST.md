# Project #002 — Fullscreen-by-Contract HD Playtest

Project #002 treats fullscreen gameplay as a required playtest condition, not a cosmetic preference.

## One-click path

Run:

`windows/Build_HD_Playtest.bat`

The Windows flow now performs the production playtest chain:

`capture sync → baseline only for untouched masters → compose current HD pack → mapping validation → Pixel QA → install into MesenCE HdPacks → launch local ROM → verify fullscreen`

The original ROM remains the source of gameplay, level data, physics, timing and logic. The launcher opens the user's local ROM from its current path and never copies it into the project, report folders or release package.

## Fullscreen contract

`windows/launch_remaster.ps1` launches MesenCE with the native `/fullscreen` switch. After the emulator exposes its main window, the launcher compares its real Win32 window rectangle against the active monitor bounds.

If command-line fullscreen is not confirmed, the launcher activates MesenCE, sends the normal F11 fullscreen toggle, waits for the display transition and checks the bounds again.

If the window still does not match the monitor, the playtest is rejected instead of silently continuing in windowed mode.

## Exact-build evidence

When the launcher is given the runtime pack, it writes:

`Reports/FullscreenPlaytest/FULLSCREEN_PLAYTEST.json`

The report contains only metadata:

- exact HD-pack fingerprint,
- whether fullscreen was verified,
- launch method,
- number of attempts,
- emulator executable path,
- ROM filename only,
- timestamp and verification details.

It does not contain the ROM, capture PNGs, screenshots, save states or commercial art/audio.

`tools/fullscreen_launch.py status <pack> <evidence>` can verify that the fullscreen evidence still belongs to the exact current runtime build. Any change to `hires.txt` or referenced runtime PNGs makes older evidence stale.

## Controls

Recommended simple keyboard controls remain:

- Arrow keys — D-pad
- Z — NES A
- X — NES B
- Enter — Start
- Right Shift — Select
- F11 — fullscreen toggle
- Esc — emulator/menu

A gamepad may be configured through MesenCE normally; Project #002 does not alter original gameplay input logic.

## Boundary

Fullscreen PASS is not whole-game completion. Final acceptance still requires complete local capture, final-quality HD artwork, Pixel QA and 10/10 exact-build in-game verification in Final Regression Cockpit.
