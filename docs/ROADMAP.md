# NES New Life — Master Roadmap

<!-- SWIR-ROADMAP-STANDARD:v1 -->
<!-- ROADMAP-PROGRESS:START -->
<p align="center">
  <img alt="Roadmap standard" src="https://img.shields.io/badge/ROADMAP%20STANDARD-SWIR%20v1-1f6feb?style=for-the-badge">
  <img alt="Completed games" src="https://img.shields.io/badge/GAMES%20COMPLETE-0-6b7280?style=for-the-badge">
  <img alt="Current game" src="https://img.shields.io/badge/CURRENT-%23002%20TINY%20TOON-8b5cf6?style=for-the-badge">
  <img alt="Status" src="https://img.shields.io/badge/STATUS-IN%20PROGRESS-f59e0b?style=for-the-badge">
</p>

## 🎮 Current game progress

**Project #002 — Tiny Toon Visual Remaster**

```text
░░░░░░░░░░░░░░░░░░░░ 0.0%
```

| 🎮 Current game | ✅ Completed gates | ⏳ Remaining | 🎯 Progress |
|---|---:|---:|---:|
| **#002 Tiny Toon Visual Remaster** | **0** | **52** | **0.0%** |

> **Master rule:** the bar above mirrors the currently active NES game's own `ROADMAP.md`. When that game's roadmap reaches a verified **100%**, the game remains recorded below as **COMPLETE 100%**, and this dashboard moves to the next NES game. The next game's progress starts from its own roadmap; completed games never lose their 100% state.
<!-- ROADMAP-PROGRESS:END -->

## 🕹️ NES game queue

| ID | Game / project | State | Progress | Roadmap |
|---:|---|---|---:|---|
| #001 | SMB2 from-scratch experiment | **ARCHIVED / DISCONTINUED** | — | Excluded from completion tracking |
| #002 | Tiny Toon Visual Remaster | **ACTIVE** | **0.0%** | [`projects/002_tiny_toon_visual_remaster/ROADMAP.md`](../projects/002_tiny_toon_visual_remaster/ROADMAP.md) |

## Repository completion model

NES New Life is a **multi-game repository**. The repository does not use one giant checklist that mixes every game's tasks together.

Each active NES game must have its own folder and its own roadmap:

```text
projects/
  002_tiny_toon_visual_remaster/
    README.md
    ROADMAP.md
  003_next_game/
    README.md
    ROADMAP.md
  004_another_game/
    README.md
    ROADMAP.md
```

Every game's `ROADMAP.md` owns that game's real 0–100% completion state. A game may be marked **COMPLETE** only after its own acceptance/release gates are genuinely finished and verified.

The master roadmap does four things only:

1. keeps the ordered list of NES projects,
2. records completed games permanently at 100%,
3. identifies the single current active game,
4. mirrors the current game's progress bar until that game reaches 100%, then advances to the next game.

## Mandatory roadmap rule for every future game

Before implementation of a new NES game begins, its project directory must contain a `ROADMAP.md` created from [`docs/GAME_ROADMAP_TEMPLATE.md`](GAME_ROADMAP_TEMPLATE.md).

A valid game roadmap must include:

- `<!-- SWIR-ROADMAP-STANDARD:v1 -->`,
- CI / ROADMAP / DONE / STATUS badges,
- a 20-segment progress bar,
- the Completed / Remaining / Total / Progress table,
- explicit measurable `[x]` / `[ ]` deliverables,
- a clear completion/acceptance rule,
- project-specific release or verification gates.

Progress must always be calculated from real measurable deliverables. It must never be guessed from version numbers, commit counts, elapsed time or subjective estimates.

## Game lifecycle

### 1. NEW
Create the project folder, `README.md` and standardized `ROADMAP.md` before major coding/art work begins.

### 2. ACTIVE
The game's own roadmap is authoritative. The master dashboard mirrors its percentage and current completed/remaining counts.

### 3. RELEASE CANDIDATE
All implementation items may be done, but the project remains below COMPLETE until its stated QA/playtest/release acceptance gates pass.

### 4. COMPLETE
The game's own roadmap reaches verified 100%. Its row in this master roadmap becomes permanent **COMPLETE — 100%**.

### 5. NEXT GAME
The next queued game's roadmap becomes the master dashboard source and its own 0–100% progress is displayed at the top.

## Current focus

The current active game is **Project #002 — Tiny Toon Visual Remaster**. Its detailed tooling, art, capture, QA and final-release requirements remain exclusively in its own roadmap. This master document must not duplicate or absorb Tiny Toon's internal checklist.
