# Project #002 — Pixel-safe Art QA

The goal of this gate is simple: **modernize the graphics aggressively without silently changing unrelated parts of an HD sheet**.

## What is authorized

`MasterWorkspace/MASTER_TILES.json` records every location where each unique master graphic is used. During batch apply, only masters whose editable PNG differs from the immutable original are considered changed. The QA tool reads the real dimensions of those original master PNGs and creates an allow-list of exact rectangles on each MesenCE HD sheet.

A generated `final_art` pack passes only when:

- `hires.txt` is byte-for-byte identical to the source capture,
- every source/output `<img>` mapping still points to the same sheet name,
- every sheet keeps exactly the same pixel dimensions,
- all RGB and alpha/transparency changes are inside authorized edited-master rectangles,
- every edited master produces a real output difference,
- normal HD Pack structural validation still passes.

Even one changed pixel outside an authorized target blocks the batch.

## Normal workflow

1. Capture locally with MesenCE HD Pack Builder at 4x Prescale.
2. Generate/group the art queue.
3. Create `MasterWorkspace`.
4. Edit PNGs only in `MasterWorkspace/editable/` and never resize them.
5. Run **Scan art progress**.
6. Run **Apply all master edits** in Remaster Studio.
7. Batch apply composes all edited masters into `ModernizedPack/final_art`.
8. Pixel QA runs automatically before the batch is accepted.
9. Review `MasterWorkspace/qa_latest/ART_QA_REPORT.html` when desired.
10. Continue to HD readiness only after QA passes.

## QA outputs

`MasterWorkspace/qa_latest/` contains:

- `ART_QA_RESULT.json` — machine-readable gate result and pixel counts,
- `ART_QA_REPORT.html` — human-readable sheet-by-sheet report,
- `diff_*.png` — marker-only overlays.

The diff overlays intentionally do **not** reproduce the captured artwork. They contain transparent background plus markers:

- green = changed pixel inside an authorized edited-master target,
- magenta = changed pixel outside authorized targets.

## CLI

```bash
python tools/art_qa.py SOURCE_PACK FINAL_ART MasterWorkspace MasterWorkspace/qa_manual
```

Exit code `0` means PASS. Exit code `2` means BLOCKED.

## Why this matters for the sprint

A full-game 4x art pass can touch hundreds or thousands of master graphics. Manual sheet inspection alone does not scale safely. This QA gate lets the project batch-apply large editing sessions while mathematically restricting differences to the areas the artist intentionally edited.

This is not a substitute for playing the full game. Final readiness still requires the local complete MesenCE capture and real visual regression through every route, animation, enemy, boss, HUD state, effect and ending screen.
