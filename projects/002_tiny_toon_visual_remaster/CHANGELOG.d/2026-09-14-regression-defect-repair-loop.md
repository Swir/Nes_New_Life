## Regression Defect → Minimal Repair → Exact-Case Retest

- added `regression_repair_sprint.py` to turn the authoritative current-build Final Regression FAIL into a minimal local repair sprint
- repair files are re-exported from the current MasterWorkspace with fresh hashes instead of reusing stale sprint pixels/state
- active PLAYER/ENEMY/BOSS family targeting is preserved; WORLD/UI/EFFECTS fall back to the failed case's current production group
- optional `[SWIR_TARGET tile=... palette=...]` failure-note hints narrow the repair target and expand to selected family peers
- `CAPTURE_GAP`, `MAPPING` and `SCALE_OR_FILTER` route away before art mutation so missing gameplay/mapping/runtime defects cannot be hidden with pixels
- repair finish reuses transactional master visual QA, animation-family consistency QA, hires.txt preservation, Pixel QA and atomic rollback
- successful repair emits a fingerprint-bound `REPAIR_RETEST_TOKEN.json` linking the original FAIL fingerprint to the repaired runtime fingerprint
- same-case retest verifies the token against authoritative FAIL history before PASS/FAIL can be recorded on the repaired build
- a same-case PASS does not waive stale/pending cases; final Gate C still requires 10/10 PASS for one exact runtime fingerprint
- added `Regression_Repair_Loop.bat/.ps1`, focused tests and production documentation
- no ROM, save state, capture PNG/JPG, ripped commercial art/audio, emulator binary or local derivative pack is committed
- ROADMAP Gate A-D remains evidence-based and unchanged by this tooling milestone
