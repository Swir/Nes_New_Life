# NES New Life

**NES New Life** is a long-term Unity project focused on rebuilding the feel of classic 8-bit console games with modern presentation, controls, tooling and accessibility.

> This repository does **not** distribute commercial ROM files, original game assets, music or copyrighted dumps. Reference ROMs stay local and are used only for research/testing where legally permitted. Public builds should use original or properly licensed assets.

## Project #001

### SMB2 New Life

First research target: **Super Mario Bros. 2 (USA) (Rev 1)**.

Current milestone: `0.1.0-foundation`

Planned foundation:
- Unity 2D gameplay framework
- responsive horizontal movement
- variable jump
- crouch state
- object pickup / carry / throw loop
- reusable game-state architecture
- 16:9 presentation and modern camera support
- controller-ready input layer
- documentation for reverse-engineered gameplay observations

## Repository layout

```text
Nes_New_Life/
├─ docs/                  # shared roadmap and standards
├─ games/                 # one folder per remake/reimagining
│  └─ SMB2_New_Life/
│     ├─ Research/        # notes from gameplay/ROM research; no ROMs
│     └─ UnityProject/    # Unity source
└─ shared/                # reusable systems for future projects
```

## Release policy

Each game gets its own version stream and GitHub Releases. Release tags should use the game prefix, for example:

- `smb2-v0.1.0`
- `smb2-v0.5.0-beta`
- `smb2-v1.0.0`

Future projects will use their own prefixes.

## Development rule

The goal is **faithful game feel, modern implementation**. Systems that are useful across multiple games should move into `shared/` instead of being duplicated.

## Status

🚧 Active development — Project #001 foundation in progress.
