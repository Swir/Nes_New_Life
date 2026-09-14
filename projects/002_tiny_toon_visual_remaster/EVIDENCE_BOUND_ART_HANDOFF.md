# Evidence-bound Art Handoff v2

`windows/Evidence_Bound_Art_Handoff.bat` is the guarded bridge from current local capture review into real 4x production.

Version 2 hardens the first handoff by validating the **actual Gate A attestation ledger**, not only the Capture Review Director summary. A `FULL_GATE_A_HANDOFF` is accepted only when all 12 criteria have current-fingerprint `VERIFIED_GATE_A` evidence in both the review handoff and the attestation ledger.

The tool still never edits ROADMAP itself.

## One-click local flow

The Windows launcher now reuses the local-only capture state saved by the single-session capture workflow:

```text
%LOCALAPPDATA%\Swir\TinyToonVisualRemaster\capture-session.json
```

The file is never committed. If a current capture is not remembered, the launcher asks for the folder.

By default it refreshes `Capture_Review_Director.ps1` in `-SkipCapture` mode before the art handoff. This consumes the newest real gameplay evidence without unexpectedly launching another play session. Human review still requires the exact `VERIFIED_GATE_A` confirmation.

## Admission rules

The handoff blocks before production when any of the following is true:

- Capture Review Director fingerprint differs from current Capture Coverage Acceptance,
- Gate A review handoff or attestation ledger belongs to another capture fingerprint,
- a `VERIFIED_GATE_A` criterion has no matching ledger attestation,
- a ledger attestation has stale source fingerprint or lacks exact `VERIFIED_GATE_A`,
- Capture Review Director verified count disagrees with the ledger-backed review,
- Capture Review Director claims `GATE_A_REVIEW_COMPLETE` without all 12 ledger-backed criteria,
- capture integrity / structural / regression / at-risk mission / mission-provenance evidence is unsafe,
- Capture Production Director refuses production,
- guarded promotion is not `PROMOTED`,
- HD Art Autopilot detects stale/unsafe production state.

`-RequireFullGateA` provides an optional strict mode that refuses all art handoff until 12/12 Gate A criteria are explicitly verified.

Without strict mode, an incomplete but safe capture can still use the established `SAFE_INCREMENTAL_ART` path. This accelerates visible HD work without pretending the game has complete Gate A coverage.

## Canonical production chain

After evidence admission, v2 uses the existing authoritative orchestration instead of creating a parallel art path:

```text
Capture Production Director
→ acceptance-gated Capture Promotion
→ resume-safe production sync
→ Visual Context Audit
→ Animation Family Workbench
→ Visual Completion Matrix
→ HD Art Autopilot
→ exact family-aware CurrentImpactSprint
→ Active Family Workbench
```

The HD Art Autopilot preserves an existing sprint instead of blindly replacing artist work and re-checks the current capture fingerprint before preparing a new exact high-impact batch.

When a usable PLAYER / ENEMY / BOSS family exists, the handoff writes `ACTIVE_FAMILY_WORKBENCH.json` and the Windows launcher opens the exact local contact board plus `CurrentImpactSprint/editable`.

## Finish path

Edit only the active family in the sprint while preserving filenames, dimensions, alpha canvas and mapping assumptions.

Finish through the existing transactional path:

```text
master visual quality gate
→ animation-family consistency gate
→ candidate pack
→ hires.txt preservation
→ Pixel QA
→ stale-workspace re-check
→ atomic commit/rollback
→ verified-fullscreen MesenCE playtest
```

## Reports and privacy

The handoff writes:

```text
Reports/EvidenceBoundArtHandoff/
  EVIDENCE_BOUND_ART_HANDOFF.json
  EVIDENCE_BOUND_ART_HANDOFF.html
```

The v2 report contains only the capture fingerprint, Gate A review counts, production/promotion state, art-autopilot summary and relative Active Family Workbench metadata. It does not embed ROM bytes, save states, capture pixels, emulator binaries or absolute local paths.

The underlying `Artwork/` and `Reports/` directories remain gitignored because local sprint/reference/contact-board files can contain ROM-derived graphics.

## ROADMAP policy

A successful handoff is a production milestone, **not** a Gate A–D completion event.

`projects/002_tiny_toon_visual_remaster/ROADMAP.md` remains authoritative. Gate A–D progress changes only after real local capture/art/QA evidence has been reviewed under the existing rules, and `docs/ROADMAP.md` must mirror any real percentage change.
