# Project #002 — Capture Promotion Director

`capture_promotion_director.py` is the regression-safe, acceptance-gated bridge between a fresh local MesenCE capture and the existing HD-art production workspace.

## Why it exists

A newer capture must never be allowed to overwrite production state merely because its `hires.txt` parses. The production handoff now consumes the same fingerprint-bound Capture Coverage Acceptance model used by Guided Capture Marathon / Local Capture Bridge evidence, so integrity, provenance and regression failures are rejected before `Artwork/ART_QUEUE.csv` or `Artwork/MasterWorkspace` can be mutated.

The authoritative path is now:

`candidate capture → validate → Capture Coverage Acceptance → promotion admission → compare with previous → BLOCK unsafe evidence/regression OR promote → resume-safe sync → Visual Context → Animation Families → Final Art Priority → Production Sprint → optional Art Sprint`

## Two different acceptance levels

Full capture acceptance and production admission intentionally answer different questions:

- `READY_FOR_GATE_A_REVIEW` means all hard capture coverage/provenance checks are clean and real gameplay evidence can be manually reviewed for Gate A.
- `INCREMENTAL_CAPTURE_READY` means the capture is integrity-safe and provenance-safe enough to continue iterative HD art production even though some full-game missions/groups are still pending.
- `UNSAFE_CAPTURE` blocks production mutation. Integrity admission failure, structural capture failure, capture regression, at-risk verified missions or untrusted completed mission provenance are hard blockers.

Pending missions and not-yet-seen production groups do **not** authorize Gate A, but they also do not unnecessarily stop safe incremental art work. Capture Mission Control remains explicit/manual and authoritative.

## Safety rule

Before promotion the director writes a fresh metadata-only Capture Coverage Acceptance report bound to the current capture fingerprint. If promotion admission is blocked, the existing production workspace remains untouched.

If `CAPTURE_REGRESSION` is detected by the capture comparison, the candidate is also **not synchronized** into `Artwork/ART_QUEUE.csv` or `Artwork/MasterWorkspace`.

Structural growth, mapping counts or group signals never auto-complete a gameplay mission, Gate A checkbox or final release gate.

## CLI

```bash
python tools/capture_promotion_director.py \
  "C:\\TinyToonWork" \
  "C:\\TinyToonWork\\Capture_Current" \
  --previous-capture "C:\\TinyToonWork\\Capture_Previous" \
  --top 20 \
  --create-sprint
```

Exit code `0` means the candidate passed promotion admission and was promoted. Exit code `2` means promotion was blocked by capture acceptance and/or capture regression.

## Windows one-click

Double-click:

```text
windows\Promote_Capture_To_HD.bat
```

Select the current capture and, preferably, the previous accepted capture. The director automatically runs Capture Coverage Acceptance first; a separate manual acceptance run is no longer required before promotion. When promotion succeeds the script can prepare `Artwork/CurrentArtSprint` immediately so the next highest-impact captured graphics are ready for local editing.

Authoritative Remaster Studio also exposes **CHECK CAPTURE ACCEPTANCE** (Ctrl+F5) so the exact fingerprint-bound blockers can be inspected before launching promotion.

## Outputs

Metadata-only acceptance outputs are refreshed first:

- `Reports/CaptureCoverageAcceptance/CAPTURE_COVERAGE_ACCEPTANCE.json`
- `Reports/CaptureCoverageAcceptance/CAPTURE_COVERAGE_MATRIX.csv`
- `Reports/CaptureCoverageAcceptance/CAPTURE_COVERAGE_ACCEPTANCE.html`

Promotion outputs are then written to:

- `Reports/CapturePromotion/CAPTURE_PROMOTION.json`
- `Reports/CapturePromotion/CAPTURE_PROMOTION_NEXT.csv`
- `Reports/CapturePromotion/CAPTURE_PROMOTION.html`

The promotion report includes the coverage acceptance gate, production admission mode, exact capture fingerprint, hard blockers and next action. After a successful promotion the director also refreshes Capture Gap, Visual Context, Animation Workbench, Final Art Priority and Production Sprint reports.

No ROM, save state, capture PNG/JPG payload, commercial artwork/audio, emulator binary or derivative release pack is written into tracked repository content. Runtime/capture/art outputs remain local and gitignored.
