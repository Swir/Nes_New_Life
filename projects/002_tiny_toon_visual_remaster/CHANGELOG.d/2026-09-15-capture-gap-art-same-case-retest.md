## Capture Gap Art → Same-Case Retest

- added `regression_capture_gap_retest.py` to bind verified capture recovery and rebuilt 4x runtime back to the exact original `FAIL / CAPTURE_GAP` case
- added `Finish_Capture_Gap_Art_And_Retest.bat/.ps1` to finish CurrentImpactSprint through transactional visual/family/Pixel QA, launch verified-fullscreen MesenCE, and require explicit same-case PASS/FAIL
- retest preparation requires authoritative original FAIL history, changed recovered capture fingerprint and changed repaired runtime fingerprint
- result recording refuses runtime fingerprint drift after the retest token is generated
- same-case PASS never waives other STALE/PENDING regression cases; Gate C still requires 10/10 PASS on one final exact runtime fingerprint
- remaining FAIL is recorded with the current defect category and returns to the existing repair/capture routing
- no ROM, save-state, capture pixel, screenshot, emulator binary or derivative local HD pack is committed
- ROADMAP Gate A-D remains unchanged by this tooling milestone
