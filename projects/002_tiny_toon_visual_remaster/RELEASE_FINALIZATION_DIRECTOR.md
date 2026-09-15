# Release Finalization Director

`windows/Finalize_Release_Candidate.bat` is the highest-level Project #002 release-finalization entry point.

It sits above the existing Final Release Readiness Director. It does not weaken any gate and does not infer missing evidence. Instead, it resolves the canonical local evidence files, audits the exact current HD-pack fingerprint, routes the first blocking stage to the correct authoritative workflow, and packages only when all seven release stages are green.

## Seven exact-build stages

1. HD Pack structure and 4x scale
2. Complete Capture Mission Control coverage
3. Final art queue complete and classified
4. Visual Context review complete/current
5. Pixel QA PASS on the exact runtime fingerprint
6. Verified fullscreen evidence on that same fingerprint
7. Final Regression 10/10 PASS on that same fingerprint

## Blocker routing

- HD Pack structure → `Regression_Mapping_Repair.bat`
- Capture coverage → `Guided_Capture_Marathon.bat`
- Final art → `High_Impact_Art_Sprint.bat`
- Visual Context → `Continue_HD_Art_Session.bat`
- Pixel QA → `Finish_High_Impact_Art_Sprint.bat`
- Verified fullscreen → `Build_HD_Playtest.bat`
- Final Regression → `Auto_Continue_Final_Regression.bat`

The finalizer stops after dispatching the real blocking workflow. Re-run it after that work is complete so all seven gates are audited again.

## Package-ready behavior

When all seven stages PASS, the Windows launcher immediately invokes `final_release_director.py package`, which performs the authoritative audit again immediately before creating the ZIP. This avoids trusting a stale earlier plan.

The public artifact is written under `Release/` with the first 12 characters of the exact HD-pack fingerprint in its filename. A companion manifest records:

- exact HD-pack fingerprint,
- ZIP filename,
- ZIP SHA-256,
- ZIP byte size,
- explicit `rom_included=false`,
- explicit `save_states_included=false`,
- explicit `emulator_binary_included=false`.

Packaging continues to use the existing safe HD-pack packager; the manifest is provenance metadata, not permission to include prohibited payloads.

## Studio

Authoritative Production Studio exposes:

`CTRL+ALT+F8 — FINALIZE RELEASE CANDIDATE`

## Evidence rule

This milestone changes no Gate A-D checkbox. A green tooling path is not release evidence. Real local capture, art QA, fullscreen and gameplay regression remain authoritative.
