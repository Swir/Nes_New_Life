# Project #002 — Capture Gap Planner

The Capture Gap Planner turns repeated MesenCE sessions into a focused **CAPTURE NEXT** list. It is intended to reduce wasted playthrough time by showing what changed, what disappeared, and which player/enemy/boss families still look thin from the metadata we have actually captured.

## What it does

`tools/capture_gap_planner.py` can:

- compare a previous and current MesenCE HD Pack capture,
- detect newly discovered semantic animation families and states,
- flag coverage that existed in the previous capture but disappeared from the current one,
- rank PLAYER / BOSS / ENEMY families with advisory missing-state suggestions,
- lift unresolved Capture Mission Control items into the same priority queue,
- flag mixed / UNASSIGNED families where a clearer in-game context would help classification,
- write `CAPTURE_NEXT.csv`, `CAPTURE_GAP_PLAN.json` and a metadata-only HTML dashboard.

No capture PNG is copied into the report.

## Important boundary

The missing-state vocabulary is intentionally **advisory**. For example, a generic boss vocabulary may suggest `intro`, `attack`, `hit`, `phase` and `death`; that does not prove every specific boss in this game exposes every named state through Mesen conditions.

The planner therefore never auto-completes Capture Mission Control and never claims whole-game completeness. Real coverage still requires explicit local in-game verification.

## Recommended loop

Keep one prior capture folder when doing a new targeted run, then execute:

```bash
python tools/capture_gap_planner.py \
  "C:\\TinyToonWork\\Capture_Current" \
  --previous "C:\\TinyToonWork\\Capture_Previous" \
  --queue "C:\\TinyToonWork\\Artwork\\ART_QUEUE.csv" \
  --capture-manifest "C:\\TinyToonWork\\CAPTURE_MISSIONS.json" \
  --output "C:\\TinyToonWork\\Reports\\CaptureGapPlanner"
```

Open `CAPTURE_GAP_PLAN.html` and work from the top of **CAPTURE NEXT**.

Highest priority is deliberately assigned to capture regressions: if a state/family was present before but is absent now, restore that coverage before treating the newer capture as the production baseline.

## Studio orchestration

`studio_command_center.capture_gap_dashboard(...)` exposes the same planner for Remaster Studio integration. Reports go to:

```text
Reports/CaptureGapPlanner/
```

## Safety

The repository contains only the planner, synthetic tests and documentation. ROMs, Mesen captures, save states, commercial artwork/audio and local derivative reports remain outside git/release assets.
