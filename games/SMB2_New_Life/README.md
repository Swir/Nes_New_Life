# SMB2 New Life

Project #001 in **NES New Life**.

> Public-safe modernization experiment inspired by the gameplay structure of a classic NES platformer. Commercial ROMs, ripped graphics, music and Nintendo-owned assets are not included.

## Current milestone

**`0.3.0-world-flow-foundation`**

The Unity project now supports connected rooms and sub-areas instead of only one horizontal test strip. The generated playable level contains a mandatory underground route, a key, a locked exit, room-specific camera bounds and pullable buried items.

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
- crouch + action plant-pulling mechanic
- thrown objects damage enemies
- patrol enemies and contact damage
- 3-point player health system
- invulnerability blink and knockback
- three lives, death and checkpoint respawn
- score collectibles and health pickups
- pits / fall death zones
- scrolling camera with room-specific world bounds
- connected doors between surface and underground rooms
- player key inventory
- locked doors that consume keys
- mandatory underground key route in the generated level
- checkpoint after the locked route
- final miniboss with 5 HP
- exit locked until the miniboss is defeated
- pause, win, game-over and replay states
- runtime HUD with HP, lives, keys, score and world messages
- generated local placeholder sprite (no dependency on commercial art)
- one-click Windows x64 build command

## Generated level flow

The current generated test level is intentionally structured like a real multi-room platform level:

1. choose a character
2. traverse the opening surface section
3. use the blue door to enter the underground room
4. fight through the underground room and collect the key
5. crouch + Shift near green plants to pull throwable items from the ground
6. use the key on the gold locked door
7. return to the late surface route behind the tall barrier
8. reach the checkpoint
9. defeat the miniboss
10. reach the goal

This is still a development level, not a claim that all original SMB2 stages have been recreated.

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
| Pull buried item | Crouch + Shift near a green plant |
| Enter door | W or Up Arrow |
| Pause / resume | P or Esc |
| Replay after win/game over | R |

## Build a Windows EXE

Choose:

`NES New Life > SMB2 > Build Windows x64`

If the playable scene has not been generated yet, the build command creates it automatically first. Unity writes the local build to:

`Builds/Windows/NES_New_Life_SMB2.exe`

`Builds/` and compiled executables are intentionally ignored by Git. A tested build can later be attached to a GitHub Release.

## Current art state

`v0.3` still deliberately uses generated colored graybox shapes. The priority is to prove the complete gameplay architecture first: connected rooms, item interactions, keys, progression gates, combat and reliable level flow. Modern original visuals will replace the graybox later.

## Next production milestones

- `0.4` richer enemy roster, vertical rooms, ladders / climbable traversal and more sub-area patterns
- `0.5` reusable level-data architecture and multiple complete development stages
- `0.6` modern original art pass, animation state machine, VFX and stronger camera feedback
- `0.7` audio, controller remapping / modern Input System, settings and save flow
- `0.8` additional bosses, level-select progression and broader content pass
- `0.9` QA, balancing, accessibility and performance pass
- `1.0` first public-safe standalone release

## Validation status

Source and project structure are reviewed statically in ChatGPT. A real Unity 6.3 LTS Editor compile/play-mode test is still required before treating any Windows binary as tested.

## Legal / repository hygiene

Do not commit ROMs or commercial asset dumps. The root `.gitignore` blocks common ROM/dump/archive/executable formats. Reference material should stay local.
