# SMB2 New Life

Project #001 in **NES New Life**.

> Public-safe modernization experiment inspired by the gameplay structure of a classic NES platformer. Commercial ROMs, ripped graphics, music and Nintendo-owned assets are not included.

## Current milestone

**`0.2.0-playable-vertical-slice`**

The repository now contains a self-contained Unity project baseline and a one-click level generator that creates a complete playable graybox level from start to finish.

## Recommended editor

**Unity 6.3 LTS** (`6000.3.x`). The project pins `6000.3.0f1` as its minimum baseline; newer 6000.3 LTS patches can upgrade it.

## What is playable now

- start screen with four character choices: Mario / Luigi / Peach / Toad
- different speed, acceleration, jump, air control and throw power per character
- Peach-style temporary air float
- variable-height jumping
- coyote time and jump buffering
- crouch and charged crouch-jump
- pickup, carry and throw objects
- thrown objects damage enemies
- patrol enemies and contact damage
- 3-point player health system
- invulnerability blink and knockback
- three lives, death and checkpoint respawn
- score collectibles and health pickups
- pits / fall death zones
- scrolling camera
- checkpoint halfway through the level
- final miniboss with 5 HP
- exit locked until the miniboss is defeated
- pause, win, game-over and replay states
- runtime HUD
- generated local placeholder sprite (no dependency on commercial art)
- one-click Windows x64 build command

## Run it

1. Clone/download the repository.
2. In Unity Hub choose **Add project from disk**.
3. Select:

   `games/SMB2_New_Life/UnityProject`

4. Open it with Unity **6.3 LTS**.
5. If Unity reports that the legacy input API is disabled, go to:

   `Edit > Project Settings > Player > Other Settings > Active Input Handling`

   and choose **Both** (or **Input Manager (Old)**), then restart Unity if requested.
6. Wait until scripts finish compiling.
7. From Unity's top menu select:

   `NES New Life > SMB2 > Create PLAYABLE Level`

8. Press **Play**.
9. Choose a character with `1`, `2`, `3` or `4` to begin.

The generator creates and saves:

`Assets/NesNewLife/SMB2/Prototype/SMB2_Playable.unity`

It also generates its own white placeholder sprite and adds the scene to Build Settings automatically.

## Controls

| Action | Key |
|---|---|
| Select Mario / Luigi / Peach / Toad | 1 / 2 / 3 / 4 |
| Move | A/D or Left/Right |
| Jump | Space |
| Crouch / charge jump | S or Down |
| Pick up / throw | Left Shift / Right Shift |
| Pause / resume | P or Esc |
| Replay after win/game over | R |

## Build a Windows EXE

Choose:

`NES New Life > SMB2 > Build Windows x64`

If the playable scene has not been generated yet, the build command creates it automatically first. Unity writes the local build to:

`Builds/Windows/NES_New_Life_SMB2.exe`

`Builds/` and compiled executables are intentionally ignored by Git. A tested build can later be attached to a GitHub Release.

## Current art state

`v0.2` deliberately uses generated colored graybox shapes. This proves the whole gameplay loop before we spend time replacing everything with modern original artwork, animation, VFX, lighting and audio.

## Next production milestones

- `0.3` modern original art pass and animation state machine
- `0.4` audio, VFX, particles and stronger camera feedback
- `0.5` richer enemy roster, doors, keys, vertical rooms and sub-areas
- `0.6` controller remapping / modern Input System
- `0.7` save/settings/menu flow
- `0.8` additional levels and bosses
- `0.9` QA, balancing and performance pass
- `1.0` first public-safe standalone release

## Legal / repository hygiene

Do not commit ROMs or commercial asset dumps. The root `.gitignore` blocks common ROM/dump/archive/executable formats. Reference material should stay local.
