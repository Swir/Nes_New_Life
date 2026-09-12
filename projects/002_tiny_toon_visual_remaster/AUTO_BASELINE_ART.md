# Automatic Baseline Art Pass

The automatic baseline exists to make a newly captured 4x MesenCE HD Pack **playable with a coherent modernized look as early as possible**, while preserving every manually finished master.

It is deliberately not treated as final artwork. The baseline is a production accelerator between capture and the final hand-finished pass.

## Recommended sprint workflow

1. Capture as much gameplay as possible in MesenCE HD Pack Builder at 4x Prescale.
2. Run the incremental production sync so new graphics are added without losing earlier art.
3. Seed untouched masters with the group-aware automatic baseline.
4. Apply all edited masters to build `ModernizedPack/final_art`.
5. Let the existing pixel QA gate verify that only authorized master rectangles changed.
6. Play-test the generated pack immediately.
7. Replace the most important baseline masters with final artwork in priority order: PLAYER → BOSS → ENEMY → WORLD → UI/EFFECTS.
8. Repeat after every larger capture. Existing manual master edits remain preserved.

## Command

```bash
python tools/auto_art_pass.py "work/.../Artwork/MasterWorkspace" --profile group-aware
```

Available profiles:

- `group-aware` — recommended; selects a style per art group.
- `balanced` — conservative global modernization.
- `cartoon` — smoother, richer character treatment.
- `dramatic` — stronger contrast/saturation for bosses.
- `painterly` — softer treatment for scenery/world tiles.
- `crisp` — sharp, restrained treatment for UI/text-like graphics.
- `vivid` — stronger color treatment for effects.

Use `--force` only when you intentionally want to replace already edited masters. The normal command protects them.

## Group-aware mapping

| Group | Baseline style |
|---|---|
| PLAYER | cartoon |
| ENEMY | cartoon |
| BOSS | dramatic |
| WORLD | painterly |
| UI | crisp |
| EFFECTS | vivid |
| UNASSIGNED | balanced |

## Safety guarantees

For every seeded master the tool:

- reads from `MasterWorkspace/original`,
- writes only to `MasterWorkspace/editable`,
- preserves exact PNG dimensions,
- preserves alpha/transparency byte-for-byte,
- skips an already edited master by default,
- writes `AUTO_BASELINE.json` with the exact files/styles/results,
- relies on the existing batch apply + pixel QA gate before the result becomes a final HD Pack.

## Important release boundary

A fully seeded baseline means **captured content has a fast modernized starting pass**. It does not prove the entire game was captured, and it does not mark art as final. A truthful release still requires complete local capture coverage, manual visual review/finishing and a full-game regression run in MesenCE.
