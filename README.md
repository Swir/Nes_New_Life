# NES New Life

**NES New Life** is a long-term Unity project focused on rebuilding the feel of classic 8-bit console games with modern presentation, controls, tooling and accessibility.

> This repository does **not** distribute commercial ROM files, original game assets, music or copyrighted dumps. Reference ROMs stay local and are used only for research/testing where legally permitted. Public builds should use original or properly licensed assets.

## Project #001

### SMB2 New Life

First research target: **Super Mario Bros. 2 (USA) (Rev 1)**.

Current milestone: **`0.8.0-persistent-checkpoints-and-settings`**

Already implemented:
- self-contained Unity 6.3 LTS project baseline
- four selectable character profiles
- responsive movement, jumping, crouch-charge and Peach-style float
- climbable vertical traversal with jump-off behavior
- object pickup / carry / throw combat
- crouch + action pullable plants / buried items
- health, lives, score, persistent checkpoints and respawn
- patrol, hopping and proximity-chasing enemies
- jumping and charge guardian archetypes
- moving platforms, respawning crumble platforms and spike hazards
- connected surface and underground rooms
- key inventory and key-gated doors
- room-specific camera bounds
- persistent best score, clears, deaths and active campaign state
- **7-world / 20-stage campaign framework** from `1-1` through `7-2`
- generated scenes `SMB2_Stage_01` through `SMB2_Stage_20`
- persistent highest-unlocked-stage progression
- unlocked stage selector for rapid testing/replay
- per-world visual/traversal/hazard scaling
- automatic world-finale detection and stronger later guardians
- pause, game-over, campaign-complete and Continue flows
- Continue restores the latest saved checkpoint inside the active stage
- persistent F10 settings/accessibility menu with volume, HUD scaling, reduced flashing and assist options
- runtime HUD with world/stage progress
- one-click 20-stage campaign generation
- 20-scene structural validator
- Windows x64 builder blocked automatically when structural campaign validation fails

## Repository layout

```text
Nes_New_Life/
├─ docs/                  # shared roadmap and standards
├─ games/                 # one folder per remake/reimagining
│  └─ SMB2_New_Life/
│     ├─ Research/        # notes from gameplay/ROM research; no ROMs
│     └─ UnityProject/    # self-contained Unity project source
└─ shared/                # reusable systems for future projects
```

## Release policy

Each game gets its own version stream and GitHub Releases, for example `smb2-v0.8.0-beta` and `smb2-v1.0.0`.

A binary Release should only be published after the corresponding Unity build has been compiled and smoke-tested.

## Development rule

The goal is **faithful game feel, modern implementation**. Systems useful across multiple games should move into `shared/` instead of being duplicated.

## Status

🚧 Active development — Project #001 now has campaign-scale progression infrastructure for 7 worlds / 20 stage slots plus persistent in-stage checkpoints, settings/accessibility infrastructure, connected sub-areas, doors/keys, pullable items, multiple enemy behaviors, vertical traversal, environmental hazards and guardian encounters. The next major work is richer handcrafted original rooms, more enemy/boss families, modern controller input/remapping, original presentation/audio and real Unity CI/build validation.
