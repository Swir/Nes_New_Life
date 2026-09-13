# Full Capture → HD Production

`windows/Full_Capture_To_HD_Production.bat` is the highest-level Windows entry point for Project #002 when the goal is to move one real local MesenCE session as far toward HD production as current evidence safely allows.

## What it chains

1. Selects the user's legally supplied local Tiny Toon NES ROM and current MesenCE HD Pack capture.
2. Runs `Guided_Capture_Marathon.ps1` with verified-fullscreen gameplay and explicit `VERIFIED_IN_GAME` mission attestations.
3. Reuses the marathon's Local Capture Bridge handoff without asking for the same capture again.
4. Runs `Capture_To_Art_Pipeline.ps1` against the exact same current/previous capture pair.
5. Rebuilds fingerprint-bound Capture Coverage Acceptance.
6. Stops fail-closed on regression, integrity, structural or mission-provenance blockers.
7. If safe, lets Capture Promotion Director perform the allowed `SAFE_INCREMENTAL_ART` or full-capture production sync.
8. Optionally creates the next High-Impact Art Sprint via `-CreateSprint`.
9. Writes `Reports/CaptureToHDSession/CAPTURE_TO_HD_SESSION.json` and `.html` with one authoritative result and `DO THIS NEXT`.

## Decisions

The workflow preserves the Capture Production Director decisions rather than inventing another completion metric:

- `FIX_REGRESSION` → production is blocked until the newer capture stops losing previously verified coverage.
- `FIX_CAPTURE_INTEGRITY` → repair structure/provenance before any production mutation.
- `CAPTURE_MORE` → unfinished gameplay evidence remains; safe captured material may still enter incremental art production.
- `READY_FOR_GATE_A_REVIEW` → metadata/provenance blockers are clean, but a human still reviews the real MesenCE evidence before changing Gate A.

Production remains one of `BLOCK_PRODUCTION`, `SAFE_INCREMENTAL_ART` or `FULL_CAPTURE_READY`.

## Fail-closed contract

If Guided Capture Marathon returns a non-zero status, the production stage is never launched. If Capture Production Director returns `BLOCK_PRODUCTION`, the combined workflow exits with code 3 after writing the metadata-only decision report. This prevents a broken/regressed session from silently becoming the local production baseline.

## Resume mode

`-SkipGameplay` is an explicit operator mode for an already-recorded local capture. It skips launching the ROM but still runs fingerprint-bound acceptance and the guarded production path. This is useful after an interrupted art/capture work session; it does not bypass revalidation.

## Privacy and repository safety

The combined report contains only metadata. It never stores ROM bytes, save states, capture pixels, emulator binaries or absolute local paths. ROM-derived PNGs remain in the user's local production workspace and are never committed by this workflow.

## ROADMAP policy

This orchestrator never edits Gate A–D. Tooling progress is not release evidence. The authoritative Project #002 progress remains derived only from the 52 Gate A–D checkboxes in `ROADMAP.md`, and real capture/art/QA evidence is still required before any checkbox changes.
