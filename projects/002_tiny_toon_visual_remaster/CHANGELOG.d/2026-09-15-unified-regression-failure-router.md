## Unified Regression Failure Router

- added `regression_failure_router.py` and `Regression_Failure_Router.bat/.ps1` as one authoritative entry point for the current exact-build regression state
- art defects route to transactional Regression Repair Loop; CAPTURE_GAP routes to targeted capture recovery; SCALE_OR_FILTER routes to the runtime playtest path
- added dedicated `Regression_Mapping_Repair.bat/.ps1` with local hires.txt backup, before/after SHA-256 checks and fail-closed HD-pack structural validation
- no active FAIL routes back to Guided Exact-Build Regression; 10/10 exact-build PASS routes to Final Release Gate
- Authoritative Production Studio now exposes `CTRL+ALT+F12  ROUTE CURRENT REGRESSION`
- router never records PASS, changes failure categories or edits ROADMAP Gate A-D
- no ROM, save-state, capture pixels, screenshots, emulator binaries or local derivative packs are committed
