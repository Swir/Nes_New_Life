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
- keep generated derivative packs local/gitignored
- next: record every world, menu, animation, boss and effect
- next: measure coverage gaps and conflicting/reused tile contexts
- next: group capture sheets into player/enemy/world/UI art sets

### Phase 3 — modern art pass
- player animation replacements first
- common enemies and projectiles
- foreground tilesets and scenery
- backgrounds and parallax where conditions allow it
- bosses, UI and effects
- consistent 4x art direction across the complete game

### Phase 4 — polish
- visual regression screenshots/checklist per world
- optional audio replacement
- controller profile documentation
- packaged HD Pack installer that contains no ROM
- final local full-game verification against the original ROM behavior

The ROM remains the gameplay source throughout all phases. We do not rebuild or redesign its levels, physics or enemy logic.
