# Project #002 — Capture Evidence Triage

`capture_evidence_triage.py` is the GitHub/CI-side consumer for privacy-safe evidence produced by Local Capture Bridge.

It does **not** consume ROMs, capture PNG/JPG files, save states or emulator binaries. It reads only validated `swir.project002.capture-evidence.v1` JSON snapshots under `evidence/capture/`.

## What it does

For the latest accepted safe snapshot it reports:

- HD Pack scale and structural evidence status,
- mapping, tile-ID, palette and condition counts,
- PLAYER / BOSS / ENEMY / WORLD / UI / EFFECTS / UNASSIGNED mapping totals,
- Capture Mission Control done/total status,
- explicit capture regressions,
- missing referenced-image metadata,
- one ordered **DO THIS NEXT** action.

When more than one safe snapshot exists, it also computes history deltas:

- added / removed tile IDs,
- added / removed palettes,
- added / removed condition names,
- mapping-count growth,
- per-group mapping deltas,
- Capture Mission Control progress delta.

## GitHub gate

`.github/workflows/project-002-capture-evidence.yml` validates every submitted evidence snapshot and then runs triage. The workflow writes a human-readable summary directly to the GitHub Actions job summary.

A snapshot is blocked when it is unsafe/invalid, not 4x, references missing capture images, or explicitly reports `CAPTURE_REGRESSION`. Partial but structurally clean evidence may pass as `PASS_INCREMENTAL`; this does **not** mean the release capture gate is complete.

## ROADMAP safety

Triage produces `CANDIDATE_REVIEW` hints for Gate A categories using condition-name signals. These hints are intentionally advisory.

**No GitHub workflow or triage result may automatically convert a Gate A–D checkbox to `[x]`.** Real local gameplay/capture/art/QA evidence must still be reviewed before the authoritative Project #002 ROADMAP changes.

This preserves the SWIR rule that tooling and metadata transport cannot inflate release progress.

## Local CLI

```bash
python tools/capture_evidence_triage.py evidence/capture \
  --output Reports/CaptureEvidenceTriage
```

For GitHub Actions-style Markdown output:

```bash
python tools/capture_evidence_triage.py evidence/capture \
  --github-summary summary.md
```

Generated triage reports are metadata-only.
