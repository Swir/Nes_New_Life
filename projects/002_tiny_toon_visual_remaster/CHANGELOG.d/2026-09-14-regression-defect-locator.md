## Regression Defect Target Locator

- added `regression_defect_locator.py` to rank metadata-only tile/palette candidates immediately after a real Guided Regression FAIL
- ranking uses regression-case production groups, actual runtime reuse, Mesen condition/context count, palette variants and current family-aware sprint membership/priority
- art-related FAILs now offer up to twelve ranked targets directly in `Guided_Regression_Playtest.ps1`
- a human-selected target is recorded as repair-compatible `[SWIR_TARGET tile=... palette=...]` plus `SWIR_CONTEXT` metadata
- existing Regression Repair Loop can therefore jump directly to the selected tile/palette and expand only to family peers instead of relying on manual transcription or broad fallback
- selecting `0 = unknown` remains valid; candidate ranking never auto-selects a defect and never creates gameplay evidence
- locator JSON/CSV/HTML outputs are metadata-only and contain no ROM bytes, save states, capture pixels, emulator binaries or absolute local paths
- added synthetic ranking/selection/privacy/PowerShell integration tests and refreshed Guided Regression + Repair Loop documentation
- ROADMAP Gate A-D remains unchanged; this tooling milestone improves Gate C repair precision without claiming completion
