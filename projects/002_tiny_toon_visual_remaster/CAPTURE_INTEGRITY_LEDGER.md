# Capture Integrity Ledger — Project #002

The Capture Integrity Ledger protects explicit Guided Capture Marathon evidence from being silently trusted after a later MesenCE capture loses previously observed structural coverage.

## Why it exists

Capture Mission Control correctly requires explicit in-game verification, but a later local capture can still become structurally poorer. The ledger compares the current capture against every verified-session snapshot already stored in `CAPTURE_MISSIONS.json` and blocks the integrity gate when the current pack falls below verified history.

## Run

```bash
python tools/capture_integrity_ledger.py \
  "C:\\TinyToonWork\\CAPTURE_MISSIONS.json" \
  "C:\\TinyToonWork\\MesenCapture" \
  --output "C:\\TinyToonWork\\Reports\\CaptureIntegrity\\CAPTURE_INTEGRITY.html"
```

The tool writes metadata-only HTML/JSON. It does not copy ROM data, save states, screenshots or capture PNG payloads into the report.

## What is checked

- current capture is 4x,
- all images referenced by `hires.txt` exist,
- current tile-rule, unique-tile, palette and image counts are not below the historical maxima from verified capture sessions,
- each completed mission still has a corresponding session record,
- missions whose verified session had more structural capture data than the current capture are listed as `at_risk_missions`,
- a SHA-256 capture fingerprint binds the report to the exact local `hires.txt` plus referenced PNG bytes.

## Important evidence rule

The ledger is deliberately one-way: it may **block** stale or regressed evidence, but it can never complete a mission. Mission completion still requires real gameplay and explicit `VERIFIED_IN_GAME` attestation through Capture Mission Control / Guided Capture Marathon.

A PASS therefore means only that all eleven missions are explicitly complete and the current local capture has not structurally regressed beneath their recorded evidence. Final HD readiness still requires art completion, Pixel QA, verified fullscreen and exact-build regression.
