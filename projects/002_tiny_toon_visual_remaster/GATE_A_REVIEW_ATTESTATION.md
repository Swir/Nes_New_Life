# Gate A Review & Attestation Handoff

This workflow is the boundary between **evidence-ready local gameplay capture** and any future repository change to the authoritative Gate A checklist.

## Why it exists

`GATE_A_EVIDENCE_MATRIX.json` can prove that a row has fingerprint-bound `VERIFIED_IN_GAME` provenance and clean capture integrity. That is still not the same thing as human confirmation that the real local gameplay actually satisfies the ROADMAP criterion.

`gate_a_review_attestation.py` therefore adds a second, explicit layer:

1. consume only `swir.project002.gate-a-evidence-matrix.v1`,
2. bind the review ledger to the exact capture SHA-256 fingerprint,
3. expose only `EVIDENCE_READY_FOR_REVIEW` rows for attestation,
4. require the exact confirmation token `VERIFIED_GATE_A`,
5. reject stale ledgers from another capture fingerprint,
6. generate a metadata-only ROADMAP patch preview,
7. **never edit `ROADMAP.md` automatically**.

## Windows path

Run:

```text
windows\Gate_A_Review_Attestation.bat
```

With no arguments it opens/refreshes the review dashboard. To attest one specific evidence-ready row after real local MesenCE inspection:

```text
windows\Gate_A_Review_Attestation.bat -AttestIndex 1
```

The launcher asks for the exact token `VERIFIED_GATE_A`. Any other input cancels the attestation.

Authoritative Production Studio also exposes **CTRL+SHIFT+F12 — GATE A REVIEW**.

## Automatic capture handoff

`Capture_Next_Best_Loop.ps1` now performs:

```text
single best local MesenCE session
→ capture integrity / gap / route refresh
→ Capture Coverage Acceptance
→ Gate A Evidence Matrix
→ Gate A Review Handoff
```

This means a capture pass ends on the exact criterion that can be reviewed next, instead of stopping at an abstract evidence report.

## Local outputs

`Reports/GateAReviewAttestation/` contains:

- `GATE_A_ATTESTATIONS.json` — explicit fingerprint-bound local attestations,
- `GATE_A_REVIEW_HANDOFF.json` — machine-readable review state,
- `GATE_A_REVIEW_HANDOFF.html` — operator dashboard.

These files contain metadata only. They must not contain ROM bytes, emulator binaries, save states, capture images, commercial art/audio, or absolute local paths.

## Fail-closed rules

An attestation is refused when:

- the matrix schema is unexpected,
- the capture fingerprint is missing,
- there are not exactly 12 Gate A criteria,
- the selected criterion is not `EVIDENCE_READY_FOR_REVIEW`,
- the ledger belongs to a different fingerprint,
- the exact `VERIFIED_GATE_A` token was not supplied,
- reviewer identity/label is empty.

The dashboard may show a projected `N/52` and percentage, but it is a **preview only**. The authoritative Project #002 ROADMAP and Master Roadmap remain unchanged until a reviewed repository update is deliberately created and passes `roadmap-standard.yml`.
