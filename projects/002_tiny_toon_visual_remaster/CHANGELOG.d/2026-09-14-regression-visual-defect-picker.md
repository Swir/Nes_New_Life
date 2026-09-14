# Local Visual Defect Picker for regression FAIL repair

- added `tools/regression_visual_picker.py` to render the ranked Regression Defect Locator candidates as actual local HD-pack tile previews instead of hexadecimal IDs only
- picker is bound to the exact locator/runtime fingerprint and fails closed when the HD runtime changes after candidate ranking
- each candidate can show up to four distinct visual variants/contexts on transparency checkerboards, with group, family, tile, palette, conditions, ranking reasons and repair-compatible `SWIR_TARGET`
- candidate cards are clickable and attempt to copy the selected rank to the clipboard for immediate return to the Guided Regression PowerShell prompt
- wired the visual board directly into `windows/Guided_Regression_Playtest.ps1` before target selection for art-related FAIL categories
- generated `Reports/RegressionDefectLocator/REGRESSION_VISUAL_PICKER_LOCAL_ONLY.html` deliberately contains ROM-derived HD-pack pixels and is therefore local-only under the existing gitignored `projects/**/Reports/` policy
- locator JSON/CSV, authoritative FAIL metadata and repair/retest evidence remain metadata-only; the visual board is never gameplay completion evidence
- added synthetic tests for real preview generation, multi-variant candidates, fingerprint drift rejection, gitignore protection and Windows integration
- ROADMAP Gate A-D checkboxes remain unchanged; this improves FAIL → target → repair throughput without claiming unverified gameplay/art completion
