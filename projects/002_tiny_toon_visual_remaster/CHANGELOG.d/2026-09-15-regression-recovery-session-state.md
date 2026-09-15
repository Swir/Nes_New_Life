## Regression Recovery Session State

- added persistent local regression recovery state under `%LOCALAPPDATA%`
- remembered exact failed case survives Studio/router restarts
- runtime fingerprint drift after repair now forces the same failed case to be re-tested before normal regression ordering resumes
- added one-click `Resume_Regression_Recovery.bat/.ps1`
- same-case retest uses verified-fullscreen MesenCE and explicit PASS/FAIL only
- remaining FAIL is rebound to the repaired fingerprint and returned to the correct repair route
- Unified Regression Failure Router now respects the recovery lock
- Authoritative Production Studio surfaces active recovery automatically and adds `CTRL+ALT+F11`
- no ROM, capture pixels, screenshots, save states or emulator binaries are stored in recovery state
- no Gate A-D checkbox is changed by this tooling milestone
