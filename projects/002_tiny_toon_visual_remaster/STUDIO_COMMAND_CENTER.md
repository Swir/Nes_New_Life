# Remaster Studio — HD Production Command Center

Project #002 now treats `TinyToonRemasterStudio.py` as a safe front end for the same evidence-bound pipeline used by the CLI tools.

## Why this milestone matters

The backend had already gained Capture Mission Control, build-bound Pixel QA and the Unified Release Candidate Gate, but the older Studio still exposed a legacy readiness dashboard and direct structural ZIP packaging. That created a dangerous split: CLI users could be protected by the new final gate while GUI users could still create a ZIP without current-build capture/QA/regression evidence.

The command-center milestone removes that bypass.

## GUI production path

1. **Open ROM** — the ROM stays local and is never copied into the repository.
2. **Prepare workspace** — creates local production folders and initializes `CAPTURE_MISSIONS.json` plus `FINAL_REGRESSION.json`.
3. **Select Mesen capture** — points Studio at the user's local MesenCE HD Pack Builder output.
4. **Capture Mission Control** — opens the local coverage dashboard.
5. **Record capture session** — records structural growth and only marks explicitly named missions complete.
6. **Group art queue / MasterWorkspace** — prepares deduplicated art production.
7. **Apply + build-bound QA** — composes edited masters and runs Pixel QA bound to the exact runtime fingerprint.
8. **One-click HD Playtest** — runs incremental sync, baseline for untouched art, batch apply, validation and optional local MesenCE deployment with backup.
9. **Release Candidate Audit** — uses the single authoritative final gate.
10. **GATED release ZIP** — refuses packaging unless the current build has a full PASS.

## Evidence layout

A Studio workspace uses these authoritative local files:

```text
CAPTURE_MISSIONS.json
FINAL_REGRESSION.json
Artwork/ART_QUEUE.csv
Reports/ArtQA/ART_QA_RESULT.json
Reports/CAPTURE_MISSION_CONTROL.html
Reports/ReleaseCandidate/RELEASE_CANDIDATE.html
Release/RELEASE_PACKAGE.json
```

All of these are local production evidence. ROM-derived capture sheets and final derivative art packs remain outside the public repository.

## Stale-evidence protection

The final runtime fingerprint is calculated from `hires.txt` plus every referenced runtime PNG. After Pixel QA or regression verification, changing any of those files causes old evidence to stop matching the current build. Studio shows the resulting blocker instead of silently accepting the older PASS.

## What Studio still cannot do automatically

Studio cannot invent coverage for gameplay states that were never exercised in the user's local MesenCE session, and it cannot honestly mark final visual regression complete without a human playthrough of the exact current build. Those remain the two deliberate manual evidence boundaries.
