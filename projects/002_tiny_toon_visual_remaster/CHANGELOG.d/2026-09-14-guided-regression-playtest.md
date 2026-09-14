## Guided Exact-Build Regression Playtest

- added `guided_regression_playtest.py` to turn the ten authoritative Final Regression Cockpit cases into a concrete case-by-case gameplay plan
- each case now has targeted route/cue guidance for short-lived states, palette contexts, animation seams, transparency and mixed-resolution fallback
- preserves FAIL-first cockpit ordering and refuses out-of-order evidence
- binds planning and result recording to the exact current runtime fingerprint; runtime drift invalidates the observation before it can be recorded
- added `windows/Guided_Regression_Playtest.bat/.ps1` with verified-fullscreen MesenCE launch before every PASS/FAIL decision
- explicit local PASS/FAIL remains mandatory; no case can auto-PASS
- failure categories route directly to capture, Visual Context, animation-family, alpha/Pixel QA, mapping or runtime-scale repair paths
- `CAPTURE_GAP` returns directly to Capture Review Director / Guided Capture Marathon instead of attempting to hide missing gameplay evidence with art
- optional `-RunAll` mode can work sequential PASS cases but stops immediately on the first FAIL
- wired `CTRL+SHIFT+F10` into Authoritative Production Studio
- added focused tests and metadata-only dashboard/documentation
- ROADMAP Gate A-D remains unchanged until real local gameplay/art/QA evidence exists
