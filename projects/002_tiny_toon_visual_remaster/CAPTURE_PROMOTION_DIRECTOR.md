# Project #002 — Capture Promotion Director

`capture_promotion_director.py` is the regression-safe bridge between a fresh local MesenCE capture and the existing HD-art production workspace.

## Why it exists

Before this milestone the toolchain could compare captures, synchronize art, build review dashboards and create an art sprint, but these steps still had to be run separately. The dangerous failure mode was promoting a newer capture that had accidentally lost previously observed gameplay states. That could retire useful queue/workspace targets before the regression was noticed.

The director makes capture promotion an explicit gate:

`candidate capture → validate → compare with previous → BLOCK on regression OR promote → resume-safe sync → Visual Context → Animation Families → Final Art Priority → Production Sprint → optional Top-N Art Sprint`

## Safety rule

If `CAPTURE_REGRESSION` is detected, the candidate is **not synchronized** into `Artwork/ART_QUEUE.csv` or `Artwork/MasterWorkspace`. Existing production work remains untouched.

Capture Mission Control remains manual and authoritative. Structural capture growth never auto-completes a gameplay mission and promotion does not mean full-game capture is complete.

## CLI

```bash
python tools/capture_promotion_director.py \
  "C:\\TinyToonWork" \
  "C:\\TinyToonWork\\Capture_Current" \
  --previous-capture "C:\\TinyToonWork\\Capture_Previous" \
  --top 20 \
  --create-sprint
```

Exit code `0` means the candidate was promoted. Exit code `2` means regression blocked promotion.

## Windows one-click

Double-click:

```text
windows\Promote_Capture_To_HD.bat
```

Select the current capture and, preferably, the previous accepted capture. When promotion succeeds the script can prepare `Artwork/CurrentArtSprint` immediately so the next highest-impact captured graphics are ready for local editing.

## Outputs

Metadata-only outputs are written to:

- `Reports/CapturePromotion/CAPTURE_PROMOTION.json`
- `Reports/CapturePromotion/CAPTURE_PROMOTION_NEXT.csv`
- `Reports/CapturePromotion/CAPTURE_PROMOTION.html`

The director also refreshes the existing Capture Gap, Visual Context, Animation Workbench, Final Art Priority and Production Sprint reports after a successful promotion.

No ROM, save state, capture PNG, commercial artwork/audio, emulator binary or derivative release pack is written into tracked repository content. Runtime/capture/art outputs remain local and gitignored.
