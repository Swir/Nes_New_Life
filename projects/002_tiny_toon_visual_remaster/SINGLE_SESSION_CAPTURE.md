# Project #002 — Single Best Capture Session

This workflow is the shortest safe path from a local MesenCE capture to the next authoritative capture decision.

## One-click entry

Run `windows/Capture_Next_Best_Loop.bat` or use `CTRL+F12` in Authoritative Production Studio.

The launcher now performs exactly **one highest-impact route-aware gameplay pass** per invocation instead of walking the entire marathon queue. This keeps the operator focused on the capture pass most likely to improve real Gate A coverage.

## Local-only remembered paths

After the first successful selection, the ROM path, current capture folder, and optional previous capture folder are stored only in:

`%LOCALAPPDATA%\Swir\TinyToonVisualRemaster\capture-session.json`

This file is outside the repository. It must never be committed. Use `-ForgetSavedPaths` to clear it and force fresh selection.

## Safety and evidence flow

1. Run the authoritative capture preflight.
2. Refresh Capture Gap Planner and Route Capture Sequencer.
3. Select only the highest-ranked route session.
4. Launch the original local ROM through the verified fullscreen MesenCE launcher.
5. Require explicit `VERIFIED_IN_GAME` confirmation for every authoritative mission before recording it.
6. If capture admission is blocked by recoverable regression, run recovery only and record no mission evidence.
7. Refresh gap and route plans after gameplay.
8. Generate privacy-safe Local Capture Bridge evidence.
9. Run Capture Coverage Acceptance.
10. Generate the next best action dashboard for the following invocation.

No ROM, save state, emulator binary, ROM-derived PNG/JPG, or local absolute path is written to the repository by this workflow.

## ROADMAP policy

Tooling completion is not Gate A completion. The Project #002 ROADMAP remains driven only by its Gate A–D checkboxes and may be changed only when real capture/art/QA evidence satisfies the authoritative requirement.
