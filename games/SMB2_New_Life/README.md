# SMB2 New Life

Project #001 in **NES New Life**.

> Public-safe modernization experiment inspired by the gameplay structure of a classic NES platformer. Commercial ROMs, ripped graphics, music and Nintendo-owned assets are not included.

## Current milestone

**`0.4.0-progression-and-enemy-variety`**

The project now goes beyond a one-off development run: progress statistics persist locally, the character select screen can continue the last profile, repeat clears can increase encounter pressure, and the enemy roster includes patrol, hopping and proximity-chasing behaviors.

## Recommended editor

**Unity 6.3 LTS** (`6000.3.x`). The project pins `6000.3.0f1` as its minimum baseline; newer 6000.3 LTS patches can upgrade it.

## What is playable now

- start screen with four character choices: Mario / Luigi / Peach / Toad
- continue last character with `C`
- reset local progress with `N` on the character-select screen
- persistent best score, clear count and death count
- repeat-run difficulty hook after completed runs
- different speed, acceleration, jump, air control and throw power per character
- Peach-style temporary air float
- variable-height jumping
- coyote time and jump buffering
- crouch and charged crouch-jump
- pickup, carry and throw objects
- crouch + action plant-pulling mechanic
- thrown objects damage enemies
- standard patrol enemies
- hopping enemies that jump toward the player
- proximity chasers that switch from patrol to pursuit
- veteran-run extra encounter after the first clear
- contact damage
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
- runtime HUD with HP, lives, keys, score, best score, clears, deaths and world messages
- generated local placeholder sprite (no dependency on commercial art)
- one-click Windows x64 build command
- one-click scene structure validator

## Generated level flow

The current generated development level is structured as a real multi-room gameplay loop:

1. choose a character or continue the last one
2. traverse the opening surface section while dealing with multiple enemy behaviors
3. use the blue door to enter the underground room
4. fight through the underground room and collect the key
5. crouch + Shift near green plants to pull throwable items from the ground
6. use the key on the gold locked door
7. return to the late surface route behind the tall barrier
8. reach the checkpoint
9. defeat the miniboss
10. reach the goal
11. replay with persistent statistics and an additional veteran encounter after a clear

This remains a development stage rather than a claim that all original SMB2 stages have been recreated.

## Run it

1. Clone/download the repository.
2. In Unity Hub choose **Add project from disk**.
3. Select `games/SMB2_New_Life/UnityProject`.
4. Open it with Unity **6.3 LTS**.
5. If Unity reports that the legacy input API is disabled, set **Active Input Handling** to **Both** or **Input Manager (Old)** in Player settings and restart Unity if requested.
6. Wait until scripts finish compiling.
7. Select `NES New Life > SMB2 > Create PLAYABLE Level`.
8. Optional but recommended: select `NES New Life > SMB2 > Validate PLAYABLE Scene`.
9. Press **Play**.
10. Choose a character with `1`, `2`, `3` or `4`, or press `C` when a previous save exists.

The generator creates `Assets/NesNewLife/SMB2/Prototype/SMB2_Playable.unity`, generates its own white placeholder sprite and adds the scene to Build Settings automatically.

## Controls

| Action | Key |
|---|---|
| Select Mario / Luigi / Peach / Toad | 1 / 2 / 3 / 4 |
| Continue previous character | C |
| Reset local progress (character-select screen) | N |
| Move | A/D or Left/Right |
| Jump | Space |
| Crouch / charge jump | S or Down |
| Pick up / throw | Left Shift / Right Shift |
| Pull buried item | Crouch + Shift near a green plant |
| Enter door | W or Up Arrow |
| Pause / resume | P or Esc |
| Replay after win/game over | R |

## Build a Windows EXE

Choose `NES New Life > SMB2 > Build Windows x64`.

If the playable scene has not been generated yet, the build command creates it automatically first. Unity writes the local build to `Builds/Windows/NES_New_Life_SMB2.exe`.

`Builds/` and compiled executables are intentionally ignored by Git. A tested build can later be attached to a GitHub Release.

## Validation

Run `NES New Life > SMB2 > Validate PLAYABLE Scene` after generating the scene. The validator checks the critical player, manager, HUD, camera, boss, exit, door, key, checkpoint and carryable-object structure and reports errors/warnings in the Unity Console and a dialog.

## Current art state

`v0.4` still deliberately uses generated colored graybox shapes. The priority remains proving the complete game architecture before replacing the prototype presentation with modern original art, animation, VFX and audio.

## Next production milestones

- `0.5` reusable level-data architecture and multiple complete development stages
- `0.6` vertical rooms, climbable traversal, richer hazards and another boss archetype
- `0.7` modern original art pass, animation state machine, VFX and stronger camera feedback
- `0.8` audio, modern Input System/controller remapping, settings and accessibility
- `0.9` broader campaign content, balancing, QA and performance pass
- `1.0` first public-safe standalone release

## Validation status

Source and project structure are reviewed statically. A real Unity 6.3 LTS Editor compile/play-mode test is still required before treating any Windows binary as tested.

## Legal / repository hygiene

Do not commit ROMs or commercial asset dumps. The root `.gitignore` blocks common ROM/dump/archive/executable formats. Reference material should stay local.
