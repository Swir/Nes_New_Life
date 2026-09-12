# Local Capture Bridge — Project #002

The Local Capture Bridge closes the practical gap between a legally supplied local MesenCE session and the GitHub-hosted development workflow.

## What stays local

The following never belongs in GitHub:

- NES ROM or ROM patch payloads
- save states / SRAM
- MesenCE capture PNGs or screenshots
- ripped commercial artwork/audio
- emulator executables or DLLs
- absolute local filesystem paths

## What the bridge may send

`tools/local_capture_bridge.py` reads the local HD Pack capture and creates a metadata-only evidence envelope:

- HD Pack scale and validation warnings
- `hires.txt` SHA-256 and combined capture fingerprint
- mapping, tile-ID, palette and condition counts
- PLAYER / BOSS / ENEMY / WORLD / UI / EFFECTS / UNASSIGNED mapping counts
- referenced image names, dimensions, byte sizes and SHA-256 hashes — never image pixels
- Capture Mission Control done/total/gate state
- capture-regression count and the next metadata-only capture targets

The default local output is:

```text
Reports/LocalCaptureBridge/SAFE_CAPTURE_HANDOFF.json
Reports/LocalCaptureBridge/SAFE_CAPTURE_HANDOFF.csv
Reports/LocalCaptureBridge/LOCAL_CAPTURE_BRIDGE.html
```

## Windows one-click flow

Run:

```text
windows/Local_Capture_Bridge.bat
```

The launcher:

1. asks for the current MesenCE capture,
2. optionally asks for the previous accepted capture,
3. generates safe evidence,
4. runs `capture_evidence_validator.py`,
5. opens the local dashboard,
6. optionally sends only the validated JSON to GitHub as a new evidence PR when GitHub CLI (`gh`) is installed and authenticated.

The optional GitHub upload creates a new branch through the GitHub API and never stages the user's ROM/capture directory in git.

## GitHub guard

`.github/workflows/project-002-capture-evidence.yml` validates every evidence PR under:

```text
projects/002_tiny_toon_visual_remaster/evidence/capture/
```

The guard rejects forbidden binary/image payloads, absolute local paths, unsupported evidence schemas and broken privacy declarations.

## ROADMAP rule

A safe evidence PR is an **input to review**, not automatic completion. It never auto-checks Gate A–D. Project #002 release progress changes only when the authoritative evidence genuinely proves the corresponding roadmap checkbox.

## Studio

The Authoritative Remaster Studio exposes the bridge on **F4**. F5 remains regression-safe capture promotion. This keeps the responsibilities separate:

`F4 local evidence → optional safe GitHub PR → evidence review`

`F5 accepted capture → regression-safe production promotion`
