# Authoritative Final Release Gate

Project #002 now treats the Final Regression Cockpit as the single authoritative source of full-game visual regression evidence used by the release gate.

## Why this exists

The project previously had two compatible but not identical views of regression evidence: the older release-candidate helper and the newer Final Regression Cockpit. rc10 removes that ambiguity. A public HD Pack ZIP cannot be authorized unless the same exact-build cockpit evidence is green.

## Required final evidence

A release PASS requires all of the following at the same time:

- structurally valid MesenCE HD Pack with the Project 4x target,
- complete Capture Mission Control evidence,
- zero unfinished or UNASSIGNED art-queue rows,
- current Visual Context Review,
- current-build Pixel QA PASS,
- Final Regression Cockpit at 10/10 PASS for the exact current `hires.txt` + referenced PNG fingerprint.

The regression status exposed by `release_candidate.py` now preserves and reports cockpit states directly: `PASS`, `FAIL`, `STALE`, and `PENDING`, including failure category/notes and the next blocking case.

## Exact-build rule

Every regression result is bound to the SHA-256 fingerprint of `hires.txt` and every referenced runtime PNG. Changing any runtime mapping or image makes prior PASS evidence `STALE`. The final gate remains BLOCKED until those cases are re-tested in MesenCE.

## Compatibility

Older regression manifests are loaded without losing their existing evidence. The legacy `complete-regression` command remains available for compatibility, but it now writes schema-2 PASS evidence plus history and exact-build fingerprinting. The recommended workflow is still the Final Regression Cockpit GUI/CLI because it records explicit FAIL categories and retest history.

## Safety boundary

No gameplay case is auto-passed. Tooling can detect stale/missing evidence, but only a real local MesenCE playthrough can establish PASS. ROMs, save states, ROM-derived captures, ripped commercial art/audio, emulator binaries and final derivative packs remain local and must not be committed.
