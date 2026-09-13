# Project #002 — Gate A Evidence Matrix

The Gate A Evidence Matrix turns the latest fingerprint-bound Capture Coverage Acceptance result into an exact twelve-row mirror of the authoritative Gate A checklist.

It exists to remove ambiguity between **mission evidence exists** and **a ROADMAP checkbox may be reviewed** without ever auto-completing the ROADMAP.

## What it checks

For the eleven gameplay capture criteria, the matrix requires:

- the matching Capture Mission Control mission to be `VERIFIED_IN_GAME`,
- a source capture fingerprint to exist,
- Capture Integrity Ledger admission to be `PASS`,
- no structural capture blocker,
- zero unresolved `CAPTURE_REGRESSION`,
- the mission not to be listed as at-risk.

The twelfth Gate A criterion is the repeated-capture regression requirement. It becomes evidence-ready only when the current acceptance manifest reports clean admission, no structural blocker, zero regressions and no at-risk verified missions.

## Outputs

`Reports/GateAEvidenceMatrix/` contains only metadata:

- `GATE_A_EVIDENCE_MATRIX.json`
- `GATE_A_EVIDENCE_MATRIX.csv`
- `GATE_A_EVIDENCE_MATRIX.html`

No ROM bytes, save states, emulator binaries, capture pixels or commercial assets are copied.

## One-click integration

`windows/Capture_Next_Best_Loop.bat` now runs one highest-impact MesenCE capture session, refreshes integrity/gap/route/evidence/acceptance, then automatically generates and opens the Gate A Evidence Matrix when an acceptance manifest exists.

This gives the operator one exact `DO THIS NEXT` criterion immediately after every gameplay pass.

## ROADMAP safety

`EVIDENCE_READY_FOR_REVIEW` does **not** mean `[x]`.

The tool never edits `ROADMAP.md`. A Gate A checkbox may be changed only after the real local MesenCE gameplay evidence has actually been reviewed. This keeps Project #002 compliant with the authoritative Gate A–D progress rule while making the first legitimate ROADMAP progress much faster to identify and verify.
