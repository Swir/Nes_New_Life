## Evidence-bound Art Handoff v2 hardening

- upgraded the freshly merged Capture Review → HD Art bridge to validate the real `GATE_A_ATTESTATIONS.json` ledger in addition to the Capture Review Director summary
- `FULL_GATE_A_HANDOFF` now requires 12/12 current-fingerprint `VERIFIED_GATE_A` attestations; stale/missing/phantom ledger evidence fails closed
- switched the production leg to the authoritative `capture_production_director.run_director(..., promote_safe=True)` + `hd_art_autopilot.run_autopilot(...)` path instead of maintaining a second direct sprint path
- HD Art Autopilot now preserves/resumes an existing CurrentImpactSprint, revalidates fingerprint continuity and prepares the exact family-aware Visual Completion Matrix batch only when safe
- added Active Family Workbench resolution so a successful handoff can open the exact PLAYER/ENEMY/BOSS contact board and editable folder immediately
- upgraded the Windows launcher to reuse local-only `%LOCALAPPDATA%\Swir\TinyToonVisualRemaster\capture-session.json`, refresh current review in `-SkipCapture` mode and optionally require full 12/12 Gate A
- wired the hardened handoff into Authoritative Production Studio on `CTRL+SHIFT+F11`
- expanded tests for ledger-backed review, strict pre-mutation blocking, director/autopilot orchestration, production fingerprint drift and metadata-only output
- ROADMAP Gate A–D remains unchanged; no tooling milestone is treated as gameplay/art/QA completion
