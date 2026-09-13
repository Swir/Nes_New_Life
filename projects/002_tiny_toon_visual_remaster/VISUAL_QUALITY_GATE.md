# Project #002 — Master-Tile Visual Quality Gate

`visual_quality_gate.py` adds a fail-closed quality check for the **actual edited 4x master PNGs** before a High-Impact Art Sprint can be committed into the authoritative `MasterWorkspace`.

Pixel QA already proves that a candidate pack changes only authorized output regions and preserves mapping. That is necessary, but it cannot tell whether the artist accidentally made a sprite fully transparent, collapsed a silhouette to a tiny box, flattened a multi-color graphic into one color or destroyed nearly all local detail while still staying inside the authorized rectangle.

## Transaction order

The authoritative sprint finish is now:

`stale-workspace check → staged sprint import → master-tile visual quality gate → candidate composition → hires.txt preservation → Pixel QA → second stale check → atomic commit / rollback`

A visual-quality failure returns `BLOCKED_VISUAL_QA`. Candidate-pack composition is not attempted and the real `MasterWorkspace` plus current output pack remain untouched.

## Blocking regressions

For every changed master the gate compares `original/<master>.png` against staged `editable/<master>.png` and blocks catastrophic signals including:

- changed dimensions,
- fully transparent redraw where the source had visible content,
- severe alpha-coverage collapse,
- severe non-transparent bounding-box width/height collapse,
- collapse from a multi-color graphic to a single visible RGB color,
- near-total local luminance-detail collapse on a substantially changed graphic,
- missing or unreadable PNGs.

The thresholds are deliberately catastrophic rather than stylistic. A legitimate redesign may use different colors, detail density or a larger silhouette, so strong expansion/reduction signals that are not clearly destructive remain warnings instead of automatic failures.

## Metadata-only evidence

Each transaction writes `ART_VISUAL_QUALITY_GATE.json` inside the local sprint directory. It contains only filenames, dimensions, counts, ratios, warning/blocker codes and summary metrics. It does **not** serialize image pixels, ROM bytes, save states, emulator binaries or absolute local paths.

## Relationship to other QA

This gate does not replace:

- `art_qa.py` / Pixel QA — still authoritative for unauthorized runtime-sheet pixel changes,
- exact `hires.txt` preservation,
- visual-context and animation-family review,
- real MesenCE full-game regression.

It closes a different failure mode: a technically authorized redraw that is visibly catastrophic before that redraw can become authoritative production state.

## ROADMAP policy

The visual-quality gate improves the safety and quality of Gate B/C production, but tooling alone is not art evidence. It never checks a ROADMAP item automatically and does not change the Project #002 0–100% percentage without real local art/QA/gameplay evidence.
