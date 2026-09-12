# Project #002 — Production Sprint Control Center

`1.0.0-rc8` moves the recent capture/art intelligence directly into the main Remaster Studio instead of requiring separate CLI commands.

## Goal

The Studio should answer one practical question during a local remaster session:

**What is the highest-impact thing to do next to make the currently captured game look more complete in HD?**

The new **PRODUCTION SPRINT** action combines the current evidence from:

- Capture Mission Control,
- Capture Gap Planner,
- Visual Context Review,
- Animation Family Review,
- MasterWorkspace progress,
- Final Art Priority.

It writes a metadata-only `Reports/ProductionSprint/PRODUCTION_SPRINT.html` dashboard and ranks actions such as capture regressions, unfinished capture missions, invalid masters, pending visual review and the next Final Art Sprint.

## Main Studio loop

1. Open the user-supplied ROM and prepare the local workspace.
2. Capture gameplay in MesenCE HD Pack Builder at 4x Prescale.
3. Select that capture in Remaster Studio.
4. Record verified Capture Mission Control progress.
5. Click **PRODUCTION SPRINT**.
6. Resolve any capture regression before promoting a newer capture.
7. Group/sync art and create the MasterWorkspace.
8. Run Visual Context and Animation Family review where the dashboard points to risk.
9. Run **Final Art Priority**.
10. Set Sprint size (default 20) and click **Create Top-N Art Sprint**.
11. Edit only `Artwork/CurrentArtSprint/editable/*.png`, without changing image dimensions.
12. Click **Finish Sprint + Pixel QA**.
13. Refresh **PRODUCTION SPRINT**; completed masters fall out of the art queue.
14. Use **One-click HD Playtest** to test the exact current build in MesenCE.
15. Repeat until captured art is complete, then perform exact-build full-game regression and the gated release audit.

## Why this is safer

The Studio does not declare unseen content complete. The Production Sprint dashboard only ranks evidence already available locally. Capture Mission Control remains the source of truth for whole-game capture coverage, Visual Context Review remains a release requirement, and full-game regression remains tied to the exact final pack fingerprint.

Final Art Sprint import still rejects resized/missing files and stale-workspace conflicts. Finishing a sprint preserves `hires.txt`, validates the generated pack and requires Pixel QA PASS.

## Local-only material

The following may contain ROM-derived graphics and must remain local/gitignored:

- `MesenCapture/`
- `Artwork/`
- `Reports/AnimationWorkbench/LocalContactSheets/`
- `ModernizedPack/`
- `Release/`

The repository continues to contain only tooling, documentation, synthetic tests and project metadata — never the ROM, save states, commercial captures, ripped artwork/audio or emulator binaries.
