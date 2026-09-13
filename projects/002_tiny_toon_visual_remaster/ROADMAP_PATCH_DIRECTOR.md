# Gate A ROADMAP Patch Director

`roadmap_patch_director.py` closes the last safe handoff between **fingerprint-bound local Gate A review** and a repository-ready roadmap change.

It does **not** edit the repository roadmaps. It generates an exact, reviewable patch preview only after the current local evidence has passed the explicit Gate A review/attestation step.

## Authoritative input chain

```text
real MesenCE gameplay
→ Gate A Evidence Matrix
→ explicit VERIFIED_GATE_A review
→ fingerprint-bound attestation ledger
→ ROADMAP Patch Director
→ reviewed feature branch / PR
→ Roadmap Standard CI
```

## What is validated

The director fails closed unless all of these are true:

- `GATE_A_REVIEW_HANDOFF.json` uses `swir.project002.gate-a-review-attestation.v1`;
- `GATE_A_ATTESTATIONS.json` uses the same schema and exact capture fingerprint;
- every applied Gate A index carries the exact `VERIFIED_GATE_A` confirmation;
- every attestation source fingerprint exactly matches its reviewed evidence row;
- the Project #002 ROADMAP still contains exactly **52** authoritative Gate A–D checkboxes;
- Gate A still contains exactly **12** checkboxes;
- both Project and Master roadmaps still contain `<!-- SWIR-ROADMAP-STANDARD:v1 -->`;
- any Gate A item already checked in the repository is also backed by the exact current fingerprint ledger.

That last rule deliberately rejects a stale or partial ledger instead of silently preserving an older completion claim.

## Output

Run:

```text
windows\Roadmap_Patch_Director.bat
```

The local-only `Reports/RoadmapPatchDirector/` folder receives:

- `ROADMAP_PATCH_DIRECTOR.json` — metadata-only decision and projected counts;
- `ROADMAP_PATCH_PREVIEW.diff` — exact unified diff for Project #002 + Master roadmap;
- `PATCHED_PROJECT_ROADMAP.md` — preview copy only;
- `PATCHED_MASTER_ROADMAP.md` — preview copy only.

No ROM, save state, capture image, emulator binary, commercial artwork/audio or absolute local capture path is included.

## SWIR ROADMAP STANDARD v1 preservation

When a verified Gate A item is projected into the preview, the director recalculates the authoritative project-wide values from the actual 52 Gate A–D checkboxes:

- `[x] / ([x] + [ ])`,
- completed / remaining / total,
- one-decimal percentage,
- 20-segment ASCII progress bar,
- Project `ROADMAP` badge,
- Project `DONE N/52` badge,
- Project progress table,
- Master current-game dashboard,
- Master `#002` queue row.

Gate B–D checkbox lines are byte-stable guarded. The tool refuses the patch if they would change.

## Normal operator path

`Gate_A_Review_Attestation.ps1` now refreshes the ROADMAP Patch Director automatically after the review dashboard is written. This means each successful local attestation immediately produces the exact repository diff that *could* be proposed next.

The preview is still not completion by itself. The final repository change must be deliberately reviewed, committed on a feature branch, opened as a PR and merged only after **Project 002 Tools** and **Roadmap Standard** are green.

## Why this improves real completion speed

Previously, even after real gameplay was reviewed, the operator still had to hand-edit two roadmap dashboards and manually recalculate the global 52-item percentage. That manual step was error-prone and discouraged frequent evidence-backed progress updates.

The director makes the path deterministic without weakening the evidence rule: **real gameplay first, explicit attestation second, exact roadmap diff third**.
