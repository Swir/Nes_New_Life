# Project #002 — Safe Capture Evidence Inbox

This directory accepts **metadata-only** Local Capture Bridge handoffs.

Allowed:
- `SAFE_CAPTURE_HANDOFF_*.json` produced by `tools/local_capture_bridge.py`
- tile/palette/condition counts
- capture mission counts and gate state
- capture regression metadata
- image file names, dimensions, byte sizes and SHA-256 hashes
- metadata-only capture fingerprints

Never commit here:
- ROMs or patches containing ROM data
- save states or SRAM
- MesenCE capture PNG/JPG/WebP/BMP/GIF files
- ripped commercial artwork/audio
- emulator executables/DLLs
- absolute local filesystem paths
- base64/raw image payloads

Every evidence PR is checked by `.github/workflows/project-002-capture-evidence.yml` and `tools/capture_evidence_validator.py`.

Evidence arrival **does not automatically mark ROADMAP Gate A–D checkboxes complete**. The authoritative Project #002 roadmap remains evidence-reviewed and release-gated.
