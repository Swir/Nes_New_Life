# Capture Integrity Ledger — Project #002

The Capture Integrity Ledger protects explicit Guided Capture Marathon evidence from being silently trusted after a later MesenCE capture loses previously observed structural coverage.

## Why it exists

Capture Mission Control correctly requires explicit in-game verification, but a later local capture can still become structurally poorer. The ledger compares the current capture against every verified-session snapshot already stored in `CAPTURE_MISSIONS.json` and blocks new mission evidence when the current pack falls below verified history.

## Two gates

The ledger now exposes two deliberately different decisions:

- `admission_gate` — used while capture is still in progress. It requires 4x scale, all referenced images, no regression against verified structural history and no completed mission whose evidence is now at risk. Incomplete missions are allowed because the marathon must be able to continue.
- `integrity_gate` — final capture-integrity decision. It requires the same structural checks **plus all Capture Mission Control missions complete**.

This split prevents a circular blocker: a clean but unfinished marathon may continue, while a structurally regressed capture cannot record any additional mission as verified.

## Run

Full integrity audit:

```bash
python tools/capture_integrity_ledger.py \
  "C:\\TinyToonWork\\CAPTURE_MISSIONS.json" \
  "C:\\TinyToonWork\\MesenCapture" \
  --output "C:\\TinyToonWork\\Reports\\CaptureIntegrity\\CAPTURE_INTEGRITY.html"
```

Admission-only check for an in-progress capture:

```bash
python tools/capture_integrity_ledger.py \
  "C:\\TinyToonWork\\CAPTURE_MISSIONS.json" \
  "C:\\TinyToonWork\\MesenCapture" \
  --admission-only
```

The tool writes metadata-only HTML/JSON. It does not copy ROM data, save states, screenshots or capture PNG payloads into the report.

## What is checked

- current capture is 4x,
- all images referenced by `hires.txt` exist,
- current tile-rule, unique-tile, palette and image counts are not below the historical maxima from verified capture sessions,
- each completed mission still has a corresponding session record,
- missions whose verified session had more structural capture data than the current capture are listed as `at_risk_missions`,
- a SHA-256 capture fingerprint binds the report to the exact local `hires.txt` plus referenced PNG bytes.

## Guided Capture Marathon integration

`guided_capture_marathon.py confirm` now runs the admission gate **before** `record_session(...)`. A mission therefore cannot become `done` merely because the operator typed `VERIFIED_IN_GAME` while the capture itself is already structurally invalid or regressed. The capture fingerprint and admission result are also recorded into the mission audit note/result.

`windows/Guided_Capture_Marathon.ps1` performs the same admission preflight before launching gameplay, re-checks admission on every mission confirmation and stops recording further missions if the capture becomes inadmissible during the session. It then opens the metadata-only integrity dashboard so the blocking reason can be repaired before continuing.

## Important evidence rule

The ledger is deliberately one-way: it may **block** stale or regressed evidence, but it can never complete a mission. Mission completion still requires real gameplay and explicit `VERIFIED_IN_GAME` attestation through Capture Mission Control / Guided Capture Marathon.

A full `integrity_gate: PASS` therefore means only that all eleven missions are explicitly complete and the current local capture has not structurally regressed beneath their recorded evidence. Final HD readiness still requires art completion, Pixel QA, verified fullscreen and exact-build regression.
