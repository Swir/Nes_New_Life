## Guided Regression → automatic minimal repair handoff

- Guided Exact-Build Regression now prepares `Artwork/CurrentRepairSprint` immediately after an authoritative art-related FAIL is recorded instead of stopping at `SWIR_TARGET` metadata.
- the handoff reuses the existing authoritative `regression_repair_sprint.py prepare` engine; no parallel repair path was introduced.
- PLAYER/ENEMY/BOSS repairs open the generated family contact board when available, while WORLD/UI/EFFECTS fall back to the general repair board; `CurrentRepairSprint/editable` opens automatically.
- automatic preparation is fail-closed and never uses `--overwrite`; an unfinished repair sprint is preserved and the already-recorded FAIL remains authoritative.
- fixed a real target-resolution gap: an explicit visual-picker `SWIR_TARGET` can now resolve directly from `MasterWorkspace/MASTER_TILES.json` even when the target is outside the bounded `CurrentImpactSprint`.
- direct MasterWorkspace resolution follows exact-deduplicated master `targets`, so a selected tile/palette can still resolve when the master representative uses another tile/palette ID.
- the resulting sprint remains fresh-exported from current MasterWorkspace and still requires visual-quality QA, animation-family QA, unchanged `hires.txt`, Pixel QA, atomic commit/rollback and same-case verified-fullscreen re-test.
- `MAPPING`, `SCALE_OR_FILTER` and `CAPTURE_GAP` remain on their dedicated non-pixel repair routes.
- added regression tests for record-before-prepare ordering, no automatic overwrite, family-board opening, non-art routing and direct MasterWorkspace target resolution.
- no Gate A-D checkbox changes; tooling does not substitute for real local gameplay/art/QA evidence.
- no ROM, save state, ROM-derived capture payload, gameplay screenshot, ripped commercial art/audio or emulator binary is committed.
