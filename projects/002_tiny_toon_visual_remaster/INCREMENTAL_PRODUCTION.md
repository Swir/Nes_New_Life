# Incremental HD Production — Project #002

Project #002 is designed for a real production loop where the MesenCE capture grows over time. A newer capture must **not** erase artwork that was already drawn or reset artist decisions back to TODO.

## One command after every newer capture

```bash
python tools/production_sync.py all "C:\\TinyToon\\MesenCapture" "C:\\TinyToon\\ProjectWorkspace"
```

The command validates the capture and then performs a resume-safe synchronization:

1. regenerates the art queue from the newest `hires.txt`,
2. preserves existing non-TODO statuses, manual/non-UNASSIGNED groups and notes for matching tile+palette entries,
3. moves mappings that disappeared from the newest capture into `ART_QUEUE_RETIRED.csv` instead of silently forgetting them,
4. refreshes the master target manifest against the newest capture,
5. preserves existing editable master PNGs by exact source-pixel SHA identity,
6. adds newly discovered masters without rebuilding the whole workspace,
7. refreshes `ART_STATE.csv`, workboards, capture report and HD-readiness report,
8. writes `Reports/PRODUCTION_SYNC.json` and `Artwork/MasterWorkspace/WORKSPACE_SYNC.json` as evidence of what changed.

## Why master preservation uses pixel identity

Master file numbering can change when a capture grows. A filename therefore is not a safe identity for artwork.

`production_sync.py` matches existing work using the source graphic's exact RGBA hash. If the same source graphic appears in a later/larger capture, the edited master is retained and only its target list is refreshed. This means a redraw can survive newly discovered levels, enemies or conditions without being redone.

New masters receive hash-based names such as:

```text
MASTER_H1a2b3c4d5e6f_PLAYER_2F_FF16360F.png
```

## Queue preservation

For a tile+palette entry already present in `Artwork/ART_QUEUE.csv`, synchronization preserves:

- `status` when it is not `TODO`,
- a non-`UNASSIGNED` art group,
- artist notes.

Newly captured entries are added as normal TODO work. Entries absent from the new capture are written to `ART_QUEUE_RETIRED.csv` for inspection instead of being destroyed.

## Safe loop for the HD sprint

```text
MesenCE capture more states
        ↓
production_sync.py all
        ↓
open Artwork/MasterWorkspace/editable
        ↓
redraw only new/TODO masters
        ↓
art_workspace.py scan
        ↓
art_workspace.py apply
        ↓
pixel QA gate
        ↓
HD readiness dashboard
        ↓
repeat until full-game capture + art + manual verification are complete
```

## Important safety boundary

The synchronization tool does not invent unseen game content and does not mark the game complete automatically. It only protects already completed production work while the local capture becomes more complete.

ROM files, save states, ROM-derived capture sheets, final derivative art packs and emulator binaries remain local and gitignored. Only tooling, synthetic tests and documentation belong in the public repository.
