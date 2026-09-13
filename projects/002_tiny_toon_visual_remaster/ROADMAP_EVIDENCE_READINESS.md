# ROADMAP Evidence Readiness Director

`roadmap_evidence_readiness.py` is a **read-only evidence-to-checklist review surface** for Project #002.

It exists to solve the last bookkeeping gap between local, fingerprint-bound production evidence and the authoritative Gate A–D checklist in `ROADMAP.md`. It never changes `[ ]` to `[x]` and never treats tooling status as completion.

## Windows one-click

Run:

```text
windows/Roadmap_Evidence_Readiness.bat
```

The same action is exposed in Authoritative Remaster Studio as **Ctrl+F9 — ROADMAP EVIDENCE READINESS**.

## What it reads

The director consumes only metadata-only local reports when present:

- Capture Coverage Acceptance,
- Capture → HD Session,
- HD Art Autopilot,
- QA-gated Art Session Controller,
- Visual Completion Matrix,
- Final Release Readiness.

It also parses the current authoritative `ROADMAP.md` directly, so the panel always follows the actual Gate A–D checkbox set instead of keeping a second copied checklist.

## Evidence states

Each ROADMAP item is classified as one of:

- `READY_FOR_HUMAN_REVIEW` — supporting evidence is present and clean enough that a human may inspect the real local gameplay/art/QA evidence for that checkbox;
- `BLOCKED` — current evidence contains an explicit blocker, stale/failing exact-build gate, capture regression or incomplete requirement;
- `WAITING_LOCAL_EVIDENCE` — the required local gameplay/art/QA action has not produced trustworthy evidence yet;
- `ALREADY_CHECKED` — the authoritative ROADMAP already records the item as complete.

`READY_FOR_HUMAN_REVIEW` is deliberately **not** equivalent to complete. The user must still verify the real local evidence and manually update the ROADMAP only when the checkbox is genuinely proven.

## Fail-closed rules

- no Capture Coverage Acceptance report means Gate A remains waiting;
- capture regression/integrity failure remains blocking;
- exact-build Pixel QA, fullscreen and regression checks must be PASS before related Gate C/D items can become review candidates;
- local art workflow steps that cannot be proven safely from metadata remain waiting rather than guessed;
- local packaging/media actions remain manual;
- no ROM, save state, capture pixels, emulator binaries or absolute local paths are written into the report.

## Outputs

The tool writes:

```text
Reports/RoadmapEvidenceReadiness/ROADMAP_EVIDENCE_READINESS.json
Reports/RoadmapEvidenceReadiness/ROADMAP_EVIDENCE_READINESS.html
```

The HTML dashboard lists all authoritative Gate A–D rows, their current evidence state, reason and source report, plus one ordered **DO THIS NEXT** action.

## Why this matters

Before this milestone, the pipeline could determine capture safety, art state, Pixel QA, fullscreen and final regression independently, but the operator still had to manually translate those reports back into the 52-item authoritative roadmap. The Evidence Readiness Director closes that gap without weakening the evidence standard or inflating progress.

The authoritative percentage therefore remains calculated only from actual `[x]` Gate A–D items. Tooling alone earns no ROADMAP progress.
