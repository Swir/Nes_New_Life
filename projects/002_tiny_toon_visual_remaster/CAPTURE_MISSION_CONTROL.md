# Capture Mission Control

This milestone turns full-game MesenCE capture from an open-ended playthrough into an explicit evidence-driven mission list.

## Why

Tile-count growth proves that a session discovered *something*, but it cannot prove that every route, animation, boss phase, menu state, effect or ending screen has been seen. Project #002 therefore keeps two kinds of evidence separate:

1. **automatic capture growth** — tile rules, unique tile IDs, palettes and image sheets;
2. **manual mission evidence** — what parts of the game were intentionally exercised.

A release must never infer unseen content from a large tile count.

## Initialize

```bash
python tools/capture_mission_control.py init "C:\TinyToonWork\CAPTURE_MISSIONS.json"
```

The manifest contains high-priority missions for title/menu states, all player actions, normal and alternate routes, common/rare enemies, every boss phase, HUD/text, effects/transitions and ending/credits.

## Record a capture session

After a MesenCE capture session:

```bash
python tools/capture_mission_control.py record ^
  "C:\TinyToonWork\CAPTURE_MISSIONS.json" ^
  "C:\TinyToonWork\MesenCapture" ^
  --complete player_idle_walk_run ^
  --complete common_enemies ^
  --notes "Completed route 1 and forced damage/death states"
```

The session records the current structural snapshot and deltas from the previous capture:

- tile rules,
- unique tile IDs,
- unique palettes,
- image-sheet count.

Mission completion is always explicit. The tool does not auto-complete missions from deltas.

## Dashboard

```bash
python tools/capture_mission_control.py dashboard ^
  "C:\TinyToonWork\CAPTURE_MISSIONS.json" ^
  "C:\TinyToonWork\Reports\CAPTURE_MISSION_CONTROL.html"
```

The dashboard shows:

- capture mission completion count,
- the five highest-priority unfinished missions,
- latest capture deltas,
- a stagnation warning when a session adds no rules/tiles/palettes/images,
- a separate capture gate that remains `BLOCKED` until every mission is explicitly verified.

## Recommended sprint loop

1. Open the mission dashboard.
2. Perform the highest-priority unfinished mission in MesenCE.
3. Save/refresh the HD Pack Builder capture.
4. Record the session and completed mission keys.
5. If the dashboard reports stagnation, deliberately change route, player state, enemy/boss state or screen instead of repeating the same traversal.
6. Run the existing incremental production sync.
7. Build the QA-gated HD playtest.
8. Repeat until the capture mission gate passes.

This controller is deliberately ROM-agnostic and stores only project metadata and numeric capture statistics. ROMs, save states, capture sheets and derivative artwork remain local and must not be committed.
