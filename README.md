# NES New Life

**NES New Life** is a long-term Unity project focused on rebuilding the feel of classic 8-bit console games with modern presentation, controls, tooling and accessibility.

> This repository does **not** distribute commercial ROM files, original game assets, music or copyrighted dumps. Reference ROMs stay local and are used only for research/testing where legally permitted. Public builds should use original or properly licensed assets.

## Project #001

### SMB2 New Life

First research target: **Super Mario Bros. 2 (USA) (Rev 1)**.

Current milestone: **`0.3.0-world-flow-foundation`**

Already implemented:
- self-contained Unity 6.3 LTS project baseline
- four selectable character profiles
- responsive movement, jumping, crouch-charge and Peach-style float
- object pickup / carry / throw combat
- crouch + action pullable plants / buried items
- health, lives, score, checkpoints and respawn
- patrol enemies and contact damage
- collectibles and healing
- pits / kill zones
- connected surface and underground rooms
- key inventory and key-gated doors
- room-specific camera bounds
- mandatory sub-area progression route
- final miniboss and locked goal
- pause, win, game-over and replay states
- runtime HUD with contextual world messages
- generated public-safe placeholder visuals
- one-click playable level generation
- one-click Windows x64 build command

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

Each game gets its own version stream and GitHub Releases. Release tags should use the game prefix, for example:

- `smb2-v0.3.0`
- `smb2-v0.5.0-beta`
- `smb2-v1.0.0`

A binary Release should only be published after the corresponding Unity build has been compiled and smoke-tested.

## Development rule

The goal is **faithful game feel, modern implementation**. Systems that are useful across multiple games should move into `shared/` instead of being duplicated.

## Status

🚧 Active development — Project #001 now has connected rooms, sub-areas, keys, locked doors, pullable plants and a complete development-level progression loop. Work continues toward multiple full stages and a public-safe standalone release.
