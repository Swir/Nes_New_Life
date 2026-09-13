# Project #002 — Transactional Art Commit

`transactional_art_commit.py` makes the authoritative High-Impact 4x art finish fail-closed.

Before this milestone, a sprint finish imported edited PNGs into `Artwork/MasterWorkspace` first and only then composed the candidate HD pack and ran Pixel QA. A bad candidate could therefore leave the local master workspace changed even when QA failed.

## New authoritative flow

1. Read the active `ART_SPRINT_KIT.json` and identify only files actually edited by the artist.
2. Verify the real `MasterWorkspace` still matches each export SHA-256.
3. Clone the workspace into a local transaction directory under `.ArtTransactions/`.
4. Import sprint edits into the staged workspace only.
5. Compose a staged candidate HD pack.
6. Require **Pixel QA = PASS** and **`hires.txt` mapping preservation = true**.
7. Re-check the real workspace hashes after QA so a concurrent/stale edit cannot be overwritten.
8. Swap the validated candidate pack into place and atomically replace only the edited master PNGs.
9. Re-scan the real workspace.
10. On any commit-time exception, restore changed master files and the previous output pack from the transaction rollback area.

A failed Pixel QA or mapping-preservation check returns `BLOCKED_QA` and leaves both the authoritative MasterWorkspace and current output pack untouched.

## Integration

The transaction gate is now used by:

- `high_impact_art_sprint.py finish`, including the Windows High-Impact Art Sprint finish path;
- `art_session_controller.py`, so the continuous QA-gated art loop cannot archive a sprint or generate the next batch until the current batch has really committed.

`ART_SESSION_CONTROLLER.json` moves to schema `swir.project002.art-session-controller.v2` and includes `transaction_status`.

## Local-only safety

The temporary transaction directory can contain ROM-derived local art and is deleted after success, QA block, or exception. It must never be committed. No ROM, save state, captured PNG/JPG, emulator binary, ripped commercial art/audio, or local derivative output is added to the repository by this milestone.

## ROADMAP policy

Transactional safety is a production milestone, not gameplay/art evidence by itself. It never changes Gate A–D checkboxes automatically. The authoritative ROADMAP percentage changes only when real local capture/art/QA evidence proves the corresponding checklist item.
