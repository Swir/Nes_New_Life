# Project #002 — Route Capture Session Sequencer

`route_capture_sequencer.py` compresses the pending Capture Mission Control work and the current Capture Gap Planner queue into a small set of compatible gameplay passes.

It does **not** reconstruct levels from ROM data, does not invent stage names, does not mark capture missions complete and never edits `ROADMAP.md`. The original locally supplied ROM and real MesenCE gameplay remain authoritative.

## Why it exists

The eleven Gate A capture missions are deliberately strict, but treating each mission as a separate play session creates unnecessary restarts and repeated travel through the same gameplay. The sequencer groups work that can safely be observed together:

1. **Startup + core player-state sweep** — boot/title/menu plus core player movement.
2. **Primary route + common-enemy sweep** — normal traversal, scrolling boundaries and common enemy states.
3. **Alternate route + rare-state sweep** — alternate paths, secrets/revisits and uncommon enemies/states.
4. **Boss + player combat/damage sweep** — boss phases plus player actions, damage, invulnerability/death and related effects.
5. **HUD/result/effects + ending sweep** — status/result UI, short-lived transitions/effects and ending/credits/post-game states.

Only unfinished authoritative missions are included. Already verified missions disappear automatically.

## Live gap folding

When `Reports/CaptureGapPlanner/CAPTURE_GAP_PLAN.json` exists, the sequencer assigns every high-value gap to one best-fit gameplay pass instead of showing the same target repeatedly.

Priority remains fail-closed:

- `CAPTURE_REGRESSION` targets are promoted ahead of ordinary work;
- PLAYER/BOSS/ENEMY/WORLD/UI/EFFECTS gaps are attached to the most compatible pass;
- mixed/UNASSIGNED families are attached where a clearer gameplay context is most useful;
- duplicate gap targets are emitted once;
- the full Capture Gap Planner report remains authoritative for the complete advisory queue.

Generic state-gap vocabulary is still advisory only. It never proves that a state exists in Tiny Toon Adventures.

## Windows workflow

`windows/Guided_Capture_Marathon.bat` generates the route plan automatically after the live Capture Gap Planner refresh.

The operator sees a **PLAY ONCE — COVER TOGETHER** session card, plays the grouped objectives in the already running verified-fullscreen MesenCE instance, and then explicitly verifies the individual authoritative missions covered by that pass.

Every `V = VERIFIED_IN_GAME` still calls the existing capture-integrity admission immediately before evidence is written. One grouped session can therefore reduce gameplay restarts without weakening provenance.

## Outputs

Metadata-only outputs are written locally under:

```text
Reports/RouteCaptureSequencer/
  ROUTE_CAPTURE_SESSION_PLAN.json
  ROUTE_CAPTURE_SESSIONS.csv
  ROUTE_CAPTURE_SESSION_PLAN.html
```

The reports contain mission keys, workflow route modes, gap names/reasons and priorities only. They contain no ROM bytes, save states, capture PNG/JPG pixels, emulator binaries, ripped commercial art/audio or absolute local paths.

## ROADMAP rule

A shorter session plan earns **zero** Gate A–D progress by itself. Project #002 progress changes only after the actual in-game capture/art/QA evidence proves an authoritative checkbox and that checkbox is reviewed and updated.
