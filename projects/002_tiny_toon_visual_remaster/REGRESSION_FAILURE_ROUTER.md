# Unified Regression Failure Router

`windows/Regression_Failure_Router.bat` is the single entry point for the current authoritative Final Regression state.

It reads the exact-build `FINAL_REGRESSION.json` state and dispatches the operator to the correct existing workflow instead of requiring manual category-to-tool decisions.

## Routes

- `MISSING_HD`, `WRONG_PALETTE`, `ANIMATION_SEAM`, `TRANSPARENCY`, `OTHER` → `Regression_Repair_Loop.bat`
- `CAPTURE_GAP` → `Regression_Capture_Gap_Recovery.bat`
- `MAPPING` → `Regression_Mapping_Repair.bat`
- `SCALE_OR_FILTER` → `Build_HD_Playtest.bat`
- no current-build FAIL → `Guided_Regression_Playtest.bat`
- 10/10 exact-build PASS → `Final_Release_Gate.bat`

The router never changes the failure category, clears evidence, records PASS or edits ROADMAP.

## Mapping repair workbench

`Regression_Mapping_Repair.bat` gives mapping defects a dedicated path instead of accidentally sending them into pixel replacement:

1. creates a timestamped local backup of `hires.txt` under `%LOCALAPPDATA%\Swir\TinyToonVisualRemaster\mapping-repair-backups`;
2. runs `validate_hdpack.py` before editing;
3. opens the exact runtime `hires.txt` locally for targeted correction;
4. requires the mapping file SHA-256 to change;
5. runs structural HD-pack validation again;
6. refuses success while the pack validator still reports an error.

A structurally valid edit is still not regression evidence. The exact failed gameplay case must be re-tested in verified-fullscreen MesenCE.

## Studio

Authoritative Production Studio exposes the router as:

```text
CTRL+ALT+F12  ROUTE CURRENT REGRESSION
```

This keeps the detailed specialist workflows available while giving normal production one safe default action.

## Safety

Routing reports are metadata-only. The workflow never commits ROMs, save states, capture pixels, screenshots, emulator binaries, ripped commercial assets or local derivative HD packs.

## ROADMAP policy

This is execution infrastructure only. Gate A-D progress remains unchanged until real local capture/art/QA evidence supports the authoritative checklist.
