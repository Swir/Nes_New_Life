## Regression CAPTURE_GAP Recovery Loop

- added `regression_capture_gap_recovery.py` to bind an authoritative `FAIL / CAPTURE_GAP` to the exact runtime/capture fingerprints and relevant Capture Mission Control missions
- reuses Capture Gap Planner + Route Capture Sequencer to choose the highest-affinity gameplay recovery pass instead of returning a generic `capture more` instruction
- added `Regression_Capture_Gap_Recovery.bat/.ps1` to run Guided Capture Marathon, re-validate the refreshed capture, then enter the existing evidence-bound HD art handoff
- recovery fails closed on unchanged capture fingerprint, structural capture blockers, `CAPTURE_REGRESSION`, stale mission provenance or missing `VERIFIED_IN_GAME` evidence
- a recovered capture never clears the regression FAIL automatically; the exact case still requires affected 4x art, transactional QA and a real verified-fullscreen same-case MesenCE retest
- no ROM, save-state, capture pixels, gameplay screenshots, emulator binaries or local derivative HD packs are committed
- ROADMAP Gate A-D remains unchanged by this tooling milestone
