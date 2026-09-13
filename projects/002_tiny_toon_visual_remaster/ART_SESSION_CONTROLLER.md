# Project #002 — Art Session Controller

`windows/Continue_HD_Art_Session.bat` closes the repetitive production loop after a High-Impact Art Sprint.

It performs one fail-closed cycle:

1. imports only the edited `CurrentImpactSprint` files through the existing stale-conflict checks,
2. composes `Build/HighImpactCandidate` while preserving `hires.txt`,
3. runs Pixel QA on that exact output,
4. rebuilds Visual Completion Matrix from the post-import MasterWorkspace,
5. blocks automatic continuation if Pixel QA fails, mapping changed, or the refreshed matrix reports invalid/classification blockers,
6. archives the finished local sprint kit under `Artwork/SprintArchive/`,
7. when captured unfinished work remains, creates the next exact matrix-selected High-Impact batch automatically.

The controller never edits ROADMAP Gate A–D. `CAPTURED_ART_COMPLETE` means only the currently captured art backlog is clear; it is not evidence that gameplay capture, regression, fullscreen validation or release are complete.

## Statuses

- `BLOCKED_QA` — Pixel QA failed or `hires.txt` mapping preservation failed.
- `BLOCKED_MATRIX` — refreshed Visual Completion Matrix still has invalid/classification blockers.
- `NEXT_BATCH_READY` — the previous sprint passed QA and the next exact high-impact batch is ready.
- `NEXT_BATCH_PARTIAL` — a batch was prepared but one or more workspace matches are missing and require review.
- `CAPTURED_ART_COMPLETE` — no captured unfinished art remains; continue Gate A capture or exact-build QA/regression as appropriate.

## Safety

The sprint archive, editable PNGs, candidate build and local reports are production material and remain local. Do not commit ROMs, save states, ROM-derived capture PNG/JPG, ripped commercial assets, emulator binaries or local sprint boards.
