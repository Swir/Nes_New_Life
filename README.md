# NES New Life

A clean-room/tooling repository for **visual remaster workflows** that keep original NES gameplay, level data and game logic inside a user-supplied ROM while replacing presentation through emulator-supported HD texture packs.

## Roadmap model

NES New Life is a **multi-game repository**.

- [`docs/ROADMAP.md`](docs/ROADMAP.md) is the **Master Roadmap** for the whole NES collection.
- Every active game under `projects/` must have its **own `ROADMAP.md`** with the SWIR Roadmap Standard v1 dashboard.
- When the active game reaches verified **100%**, it stays recorded as complete and the Master Roadmap dashboard moves to the next game.
- New games must start from [`docs/GAME_ROADMAP_TEMPLATE.md`](docs/GAME_ROADMAP_TEMPLATE.md).
- GitHub Actions validates that every game project keeps its own standardized Roadmap.

## Active project

### #002 — Tiny Toon Visual Remaster

Goal: keep the original game flow intact and focus on a modern visual layer.

- same ROM-driven gameplay and levels
- same original game logic
- keyboard layout aimed at simple PC play: arrows + Z/X + Enter
- external HD graphics via Mesen HD Packs
- no ROMs or ripped commercial artwork stored in this repository

Project documentation:

- [`projects/002_tiny_toon_visual_remaster/README.md`](projects/002_tiny_toon_visual_remaster/README.md)
- [`projects/002_tiny_toon_visual_remaster/ROADMAP.md`](projects/002_tiny_toon_visual_remaster/ROADMAP.md)

## Project #001

The previous SMB2-from-scratch experiment is discontinued. Its old prototype code is intentionally not restored here and it is excluded from active completion tracking.
