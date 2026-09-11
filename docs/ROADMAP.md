# NES New Life Roadmap

## Project #002 — Tiny Toon Visual Remaster

### Phase 1 — HD-pack foundation — COMPLETE
- validate user-supplied ROM fingerprint and mapper
- local CHR reference exporter
- local workspace generator
- MesenCE Windows one-click launcher
- Mesen HD Pack validator
- Remaster Studio GUI
- safe repository rules: no ROM/capture distribution
- CI tests for Python tooling and PowerShell launch scripts

### Phase 2 — capture acceleration — ACTIVE
- configure MesenCE HD Pack Builder around a 4x Prescale workflow
- analyze capture sheets and `hires.txt` automatically
- report tile rules, conditions, unique tile IDs and palettes
- Instant HD Preview generator with non-destructive styles
- compare any two capture sessions and quantify rule/tile/palette growth
- flag removed mappings so a newer capture cannot silently regress coverage
- generate a ranked CSV art queue from real tile/palette usage
- infer PLAYER / ENEMY / BOSS / WORLD / UI / EFFECTS groups only when condition names provide evidence
- leave unknown tiles explicitly `UNASSIGNED` instead of inventing semantics
- keep generated derivative packs local/gitignored
- next: record every world, menu, animation, boss and effect
- next: use capture diffs after each play session until growth approaches zero
- next: manually resolve remaining UNASSIGNED art-queue entries from local visual inspection

### Phase 3 — modern art pass — ACTIVE TOOLING READY
- work from the ranked/grouped art queue so the highest-reuse graphics are modernized first
- player animation replacements first
- common enemies and projectiles
- foreground tilesets and scenery
- backgrounds and parallax where conditions allow it
- bosses, UI and effects
- consistent 4x art direction across the complete game
- mark art-queue entries complete as final replacements are verified locally

### Phase 4 — release readiness and polish — TOOLING READY
- evidence-based `HD_READINESS_CHECKLIST.json`; no fake automatic whole-game percentage
- release dashboard combines validator results, 4x target, art queue status and manual full-game evidence
- visual regression checklist covers boot/menu, player actions, all routes, enemies, bosses, HUD/text, effects and ending/credits
- safe ZIP packager refuses ROM/save/patch files and structurally invalid packs
- optional audio replacement
- controller profile documentation
- final local full-game verification against the original ROM behavior

### Current hard blocker to a truthful "complete HD" release
The repository can now automate capture measurement, prioritization, grouping, preview processing, validation, readiness reporting and safe packaging. The remaining content-critical work requires a **local complete MesenCE capture and real full-game visual verification**. Tooling must never infer unseen bosses, routes, animation states or ending screens as complete.

The ROM remains the gameplay source throughout all phases. We do not rebuild or redesign its levels, physics or enemy logic.
