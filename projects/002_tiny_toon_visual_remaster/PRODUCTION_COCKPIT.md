# Project #002 — Authoritative Production Cockpit

`windows/Authoritative_Remaster_Studio.bat` now opens `AuthoritativeProductionStudio.py`, which keeps the existing Authoritative Remaster Studio controls and adds the highest-level production automation directly to the main UI.

## Main actions

- **CTRL+F6 — FULL CAPTURE → HD AUTOPILOT** launches `Full_Capture_To_HD_Autopilot.bat`.
- **CTRL+F7 — CONTINUE QA-GATED ART SESSION** launches `Continue_HD_Art_Session.bat`.
- **CTRL+F8 — REFRESH PRODUCTION COCKPIT** rebuilds the metadata-only `Reports/ProductionCockpit/PRODUCTION_COCKPIT.json/.html` decision surface.

The cockpit reads the latest local metadata reports from:

1. Capture → HD Session,
2. HD Art Autopilot,
3. Art Session Controller,
4. Final Release Readiness.

It then chooses one authoritative `DO THIS NEXT` action instead of requiring the operator to remember which layer owns the current blocker.

## Decision priority

The resolver is fail-closed and intentionally ordered:

1. exact-build Final Release PASS,
2. Pixel QA / Visual Completion blocker,
3. active exact High-Impact Art Sprint,
4. HD Art Autopilot blocker,
5. safe admitted capture that still needs exact art routing,
6. capture regression/integrity/provenance blocker,
7. start the full guided Capture → HD Autopilot path.

A later successful report cannot hide a higher-priority current QA blocker. An active `CurrentImpactSprint` is resumed rather than replaced. A safe incremental capture can enter art production without pretending Gate A is complete.

## Privacy and release progress

The Production Cockpit is metadata-only. It never embeds ROM bytes, save states, capture pixels, emulator binaries or absolute local paths. It never modifies `hires.txt` and never edits Gate A–D.

`CAPTURED_ART_COMPLETE` remains capture-bounded. It means the currently captured art backlog is clear; it does **not** mean the whole game is captured, regression-tested or release-ready.

The authoritative Project #002 ROADMAP percentage therefore remains based only on the real Gate A–D checkboxes and real local gameplay/art/QA evidence.
