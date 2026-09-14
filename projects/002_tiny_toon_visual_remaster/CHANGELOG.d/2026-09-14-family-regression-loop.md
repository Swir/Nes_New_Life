## Closed Family → Regression → Next-Family Loop

- added `family_regression_loop.py` to close the gap after transactional family QA/fullscreen playtest
- exact-build fullscreen evidence is required before regression evidence can drive the loop
- Final Regression Cockpit stays FAIL-first; PENDING/STALE cases never outrank a current-build FAIL
- failure categories route repair back to the correct production path, including `CAPTURE_GAP` → Capture Review Director
- 10/10 exact-build regression PASS can optionally trigger HD Art Autopilot and resolve the next highest-impact PLAYER/ENEMY/BOSS family
- added one-click `Family_Regression_Loop.bat/.ps1`, metadata-only dashboard, active-family opening and focused synthetic tests
- no regression PASS is auto-recorded, no Gate A-D checkbox is auto-edited, and no ROM/save/capture pixels/emulator binary is committed
- authoritative ROADMAP progress remains 0/52 until real local gameplay/art/QA evidence supports checklist changes
