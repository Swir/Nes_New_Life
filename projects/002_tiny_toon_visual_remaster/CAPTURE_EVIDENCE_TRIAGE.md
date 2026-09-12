# Project #002 — Capture Evidence Triage

`capture_evidence_triage.py` is the GitHub/CI-side consumer for privacy-safe evidence produced by Local Capture Bridge.

It does **not** consume ROMs, capture PNG/JPG files, save states or emulator binaries. It reads only validated `swir.project002.capture-evidence.v1` JSON snapshots under `evidence/capture/`.

## What it does

For the latest accepted safe snapshot it reports:

- HD Pack scale and structural evidence status,
- the canonical Capture Integrity Ledger fingerprint and admission state,
- mapping, tile-ID, palette and condition counts,
- PLAYER / BOSS / ENEMY / WORLD / UI / EFFECTS / UNASSIGNED mapping totals,
- Capture Mission Control done/total status,
- number of completed missions backed by fingerprint-bound `VERIFIED_IN_GAME` sessions,
- explicit capture regressions and at-risk verified mission evidence,
- missing referenced-image metadata,
- one ordered **DO THIS NEXT** action.

When more than one safe snapshot exists, it also computes history deltas:

- added / removed tile IDs,
- added / removed palettes,
- added / removed condition names,
- mapping-count growth,
- per-group mapping deltas,
- Capture Mission Control progress delta,
- fingerprint-bound verified-mission progress delta.

## Fingerprint provenance gate

A snapshot is no longer accepted merely because it says, for example, `3/11` capture missions complete. Triage now requires the safe handoff to prove that every completed mission points to a Capture Mission Control session with explicit `VERIFIED_IN_GAME` evidence and a valid SHA-256 capture fingerprint.

The handoff is blocked when:

- `capture_integrity` is missing,
- its fingerprint does not exactly match `hd_pack.capture_fingerprint`,
- Capture Integrity Ledger admission is not `PASS`,
- structural blockers, historical regressions or at-risk verified missions are present,
- completed mission count and fingerprint-bound mission evidence count disagree,
- any completed mission lacks trusted `VERIFIED_IN_GAME` session evidence.

The source fingerprint of an older verified mission is not required to equal a later, richer clean capture. Legitimate additive capture growth is allowed; the Capture Integrity Ledger remains responsible for proving that the newer capture has not structurally regressed below verified history.

## GitHub gate

`.github/workflows/project-002-capture-evidence.yml` validates every submitted evidence snapshot and then runs triage. The workflow writes a human-readable summary directly to the GitHub Actions job summary.

A snapshot is blocked when it is unsafe/invalid, not 4x, references missing capture images, explicitly reports `CAPTURE_REGRESSION`, or fails the fingerprint provenance gate above. Partial but structurally clean evidence may pass as `PASS_INCREMENTAL`; this does **not** mean the release capture gate is complete.

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