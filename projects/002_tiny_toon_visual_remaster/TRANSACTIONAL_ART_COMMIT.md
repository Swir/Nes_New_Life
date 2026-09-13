# Project #002 — Transactional Art Commit

`transactional_art_commit.py` makes the authoritative High-Impact 4x art finish fail-closed.

Before this milestone, a sprint finish imported edited PNGs into `Artwork/MasterWorkspace` first and only then composed the candidate HD pack and ran Pixel QA. A bad candidate could therefore leave the local master workspace changed even when QA failed.

## Authoritative flow

1. Read the active `ART_SPRINT_KIT.json` and identify only files actually edited by the artist.
2. Verify the real `MasterWorkspace` still matches each export SHA-256.
3. Clone the workspace into a local transaction directory under `.ArtTransactions/`.
4. Import sprint edits into the staged workspace only.
5. Run the **master-tile visual quality gate** against staged `original/` vs `editable/` PNGs.
6. Block catastrophic single-master redraw failures such as full transparency, severe alpha/bounding-box collapse, color collapse, detail collapse, invalid PNG or changed dimensions.
7. Run the **animation-family consistency gate** across staged PLAYER/ENEMY/BOSS masters.
8. Block catastrophic family geometry drift: frame scale collapse/expansion, large canvas-center jumps, extreme alpha-coverage outliers and palette-variant silhouette mismatches.
9. Compose a staged candidate HD pack only when both master-level and family-level quality gates pass.
10. Require **Pixel QA = PASS** and **`hires.txt` mapping preservation = true**.
11. Re-check the real workspace hashes after QA so a concurrent/stale edit cannot be overwritten.
12. Swap the validated candidate pack into place and atomically replace only the edited master PNGs.
13. Re-scan the real workspace.
14. On any commit-time exception, restore changed master files and the previous output pack from the transaction rollback area.

A master-level failure returns `BLOCKED_VISUAL_QA`. A family-level failure returns `BLOCKED_ANIMATION_CONSISTENCY`. In both cases candidate-pack composition is skipped and the authoritative MasterWorkspace plus current output pack remain untouched. Failed Pixel QA or mapping preservation returns `BLOCKED_QA` with the same no-mutation guarantee.

## Integration

The transaction gate is used by:

- `high_impact_art_sprint.py finish`, including the Windows High-Impact Art Sprint finish path;
- `art_session_controller.py`, so the continuous QA-gated art loop cannot archive a sprint or generate the next batch until the current batch has really committed.

`TRANSACTIONAL_ART_FINISH.json` schema v3 embeds both `visual_quality_gate` and `animation_consistency_gate` in addition to Pixel QA and mapping-preservation state. Focused local reports are written as:

- `ART_VISUAL_QUALITY_GATE.json`
- `ART_ANIMATION_CONSISTENCY_GATE.json`

See `VISUAL_QUALITY_GATE.md` and `ANIMATION_CONSISTENCY_GATE.md` for thresholds, blocker semantics and privacy guarantees.

## Local-only safety

The temporary transaction directory can contain ROM-derived local art and is deleted after success, QA block or exception. It must never be committed. No ROM, save state, captured PNG/JPG, emulator binary, ripped commercial art/audio, or local derivative output is added to the repository by this milestone.

## ROADMAP policy

Transactional safety is a production milestone, not gameplay/art evidence by itself. It never changes Gate A–D checkboxes automatically. The authoritative ROADMAP percentage changes only when real local capture/art/QA evidence proves the corresponding checklist item.
