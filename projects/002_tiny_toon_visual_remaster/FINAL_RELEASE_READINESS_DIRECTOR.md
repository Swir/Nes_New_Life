# Final Release Readiness Director

Project #002 now has one final, exact-build release decision that includes the verified fullscreen requirement.

## Why this exists

The earlier release candidate gate already required structural validity, complete capture missions, a finished/classified art queue, Visual Context review, current-build Pixel QA and 10/10 Final Regression Cockpit PASS evidence. The verified-fullscreen playtest added exact-build fullscreen evidence, but that evidence still needed to become packaging-authoritative.

`tools/final_release_director.py` closes that gap. A public package is authorized only when **all seven production gates** are green for the same current HD pack:

1. HD Pack structure and 4x scale,
2. complete Capture Mission Control coverage,
3. zero TODO / zero UNASSIGNED final-art work,
4. Visual Context review complete and current,
5. Pixel QA PASS for the exact fingerprint,
6. verified fullscreen playtest PASS for the exact fingerprint,
7. Final Regression Cockpit 10/10 PASS for the exact fingerprint.

A runtime PNG or `hires.txt` change changes the pack fingerprint. That automatically makes old Pixel QA, fullscreen and regression evidence unusable for final authorization until the changed build is re-tested.

## Commands

Audit only:

```powershell
python tools/final_release_director.py audit <PACK> `
  --capture <CAPTURE_MISSIONS.json> `
  --queue <ART_QUEUE.csv> `
  --visual-review <VISUAL_CONTEXT_REVIEW.csv> `
  --art-qa <ART_QA_REPORT_OR_FOLDER> `
  --regression <FINAL_REGRESSION.json> `
  --fullscreen <FULLSCREEN_PLAYTEST.json> `
  --output <REPORT_FOLDER>
```

Gated packaging:

```powershell
python tools/final_release_director.py package <PACK> `
  --capture <CAPTURE_MISSIONS.json> `
  --queue <ART_QUEUE.csv> `
  --visual-review <VISUAL_CONTEXT_REVIEW.csv> `
  --art-qa <ART_QA_REPORT_OR_FOLDER> `
  --regression <FINAL_REGRESSION.json> `
  --fullscreen <FULLSCREEN_PLAYTEST.json> `
  --output <REPORT_FOLDER> `
  --zip <OUTPUT.zip>
```

The package command exits blocked and does **not** create a release ZIP unless every gate is PASS.

## Outputs

The director writes metadata-only reports:

- `FINAL_RELEASE_READINESS.json`
- `FINAL_RELEASE_READINESS.html`

The HTML dashboard presents every production gate in order and a single **DO THIS NEXT** action. This makes the final work queue explicit instead of forcing the artist/tester to reconcile several reports manually.

## Safety boundary

The director never packages or commits the ROM, save states, ROM-derived captures, commercial ripped art/audio or emulator binaries. The user's local ROM remains the gameplay source and is opened in place by the playtest workflow.
