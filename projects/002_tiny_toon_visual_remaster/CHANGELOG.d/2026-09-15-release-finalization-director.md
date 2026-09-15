# Release Finalization Director

- Added `release_finalization_director.py` to route the first blocking exact-build release stage.
- Added `Finalize_Release_Candidate.bat/.ps1` as the highest-level release finalization workflow.
- Resolves canonical local evidence without copying ROM/capture payloads into the repository.
- Routes structure, capture, final art, Visual Context, Pixel QA, fullscreen and final regression blockers to their existing authoritative workflows.
- Re-audits all seven gates immediately before public packaging.
- Creates the ROM-free gated HD Pack ZIP only after exact-build PASS across all seven stages.
- Adds a companion release manifest with HD-pack fingerprint, ZIP SHA-256 and explicit ROM/save-state/emulator exclusion flags.
- Added Authoritative Production Studio `CTRL+ALT+F8 — FINALIZE RELEASE CANDIDATE`.
- Added focused routing, packaging-manifest and Studio integration tests.
- No Gate A-D checkbox changes; true roadmap progress remains evidence-driven.
