# Evidence-bound Art Handoff

`windows/Evidence_Bound_Art_Handoff.bat` is the guarded bridge from current local capture review into real 4x production.

It deliberately does **not** treat tooling as Gate A completion. It first rebuilds Capture Coverage Acceptance for the selected local capture, then requires the exact SHA-256 capture fingerprint to match `CAPTURE_REVIEW_DIRECTOR.json`. A stale review from an older capture is rejected before production state is touched.

## Admission rules

The handoff blocks when the current acceptance evidence contains unsafe integrity, structural capture, capture-regression, at-risk mission or mission-provenance blockers. A safe but incomplete capture may still enter `SAFE_INCREMENTAL_ART_HANDOFF`, matching the existing Capture Promotion Director policy; Gate A stays incomplete until real gameplay review is complete.

A fully reviewed capture enters `FULL_GATE_A_HANDOFF`, but ROADMAP still changes only through the separate attestation/patch process.

## What happens after admission

1. rebuild fingerprint-bound Capture Coverage Acceptance;
2. verify Capture Review Director fingerprint equality;
3. run acceptance-gated Capture Promotion Director;
4. verify the promotion fingerprint still matches the same capture;
5. refresh MasterWorkspace / Visual Context / Animation Family / production priority through promotion;
6. build Visual Completion Matrix;
7. export the exact family-aware highest-impact batch into `Artwork/CurrentImpactSprint`;
8. write metadata-only `Reports/EvidenceBoundArtHandoff/EVIDENCE_BOUND_ART_HANDOFF.{json,html}`.

The exported editable/reference PNGs and family contact boards are local ROM-derived production material and remain outside git. `hires.txt` is not rewritten by this handoff.

## Finish path

Edit only `Artwork/CurrentImpactSprint/editable/*.png`, preserving filenames, dimensions and alpha canvas. Finish with `windows/Finish_High_Impact_Art_Sprint.bat`; the existing transactional path blocks stale workspace conflicts, visual/animation QA failures, mapping changes and Pixel QA failures before committing local production state.

This reduces the capture → art transition to one fingerprint-bound operation while preserving all existing safety gates.