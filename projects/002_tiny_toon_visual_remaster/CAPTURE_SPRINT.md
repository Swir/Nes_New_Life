# Project #002 — Capture Sprint

This is the fastest practical path from a local Tiny Toon NES ROM to a high-coverage MesenCE HD Pack without changing gameplay or level logic.

## Session loop

1. Launch the user-supplied ROM with `windows/Start_Remaster.bat`.
2. Open MesenCE HD Pack Builder and record a focused gameplay session.
3. Save that session as a separate local capture folder, for example `captures/session_01_world1`.
4. Compare the previous capture with the new capture:

```bash
python tools/hdpack_pipeline.py compare captures/session_01_world1 captures/session_02_world2 --output captures/session_02_diff.json
```

5. Continue recording while `added_rule_count`, `new_tile_ids` or `new_palettes` keep growing.
6. If a newer capture reports removed mappings, inspect it before replacing the older baseline. A capture should normally grow, not shrink.
7. Generate the art queue from the best/highest-coverage capture:

```bash
python tools/hdpack_pipeline.py art-queue captures/master --output work/art_queue.csv
```

8. Work down the queue from priority 1. Fill the `status`, `art_group` and `notes` columns while producing final 4x artwork.
9. Build a fast visual baseline when needed:

```bash
python tools/hdpack_pipeline.py preview captures/master work/ModernizedPack/vibrant --style vibrant --overwrite
```

10. Validate after every mapping/art batch:

```bash
python tools/validate_hdpack.py work/ModernizedPack/vibrant
```

## Recommended capture order

Use this order to maximize visual coverage quickly:

- title screen, intro, menus and HUD
- Buster standing/running/jumping/attacking/hurt/death animation states
- World 1 full traversal including all enemy types and pickups
- every remaining world from start to boss
- boss intros, attacks, damage and death states
- doors, transitions, checkpoints, special rooms and endings
- deliberately revisit rare animations/effects that may have been skipped during normal play

## Stop condition for capture

A capture is not considered complete just because the game was finished once. Treat coverage as mature only when repeated focused play sessions add no meaningful tile/palette rules and no known animation, enemy, boss, menu or effect is still missing.

`compare` does not claim a percentage of the entire commercial game because no authoritative complete-rule denominator exists without first seeing all runtime states. Instead it provides honest session-to-session growth and regression detection.

## Copyright boundary

Keep ROMs, save states, Mesen capture PNGs, generated derivative packs and ripped commercial assets local. They are intentionally gitignored and must not be committed to this repository.
