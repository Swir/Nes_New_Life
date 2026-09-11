# SMB2 New Life

Project #001 in **NES New Life**.

> Public-safe modernization experiment inspired by the gameplay structure of a classic NES platformer. Commercial ROMs, ripped graphics, music and Nintendo-owned assets are not included.

## Current milestone

**`0.8.0-persistent-checkpoints-and-settings`**

The project has a complete campaign-scale progression framework with **7 worlds and 20 stage slots**, plus persistent in-stage checkpoints, settings/accessibility controls and a build-time campaign validation gate.

This is not a claim that the original commercial levels have been recreated 1:1. The twenty generated scenes remain original/public-safe development stages built from reusable systems so future handcrafted levels have real progression, save, validation and build infrastructure.

## Recommended editor

**Unity 6.3 LTS** (`6000.3.x`). The project pins `6000.3.0f1` as its baseline.

## Campaign architecture

- 7 worlds
- 20 generated campaign stages
- world structure: `3 + 3 + 3 + 3 + 3 + 3 + 2`
- stage IDs from `1-1` through `7-2`
- scenes `SMB2_Stage_01` through `SMB2_Stage_20`
- persistent current stage and highest unlocked stage
- selected character, lives and score preserved between stages
- persistent per-stage checkpoint position
- Continue returns to the unfinished stage and latest saved checkpoint
- unlocked-stage selector (`Q/E`, then `Enter`)
- world finales and final Stage 20 guardian configuration
- Windows build includes all twenty scenes in progression order

## Gameplay systems

- Mario / Luigi / Peach / Toad profiles with distinct movement, jump, air control and throw power
- Peach-style temporary air float
- variable-height jumping, coyote time and jump buffering
- crouch and charged crouch-jump
- climbable traversal and jump-off support
- pickup, carry, throw and crouch+action plant pulling
- thrown-object combat
- patrol, hopping and proximity-chasing enemies
- jumping and charge guardian archetypes
- contact damage, HP, knockback and invulnerability
- moving platforms, respawning crumble platforms and spike hazards
- lives, death, persistent checkpoint respawn and pits
- score collectibles and healing
- room-specific camera bounds
- connected doors, keys, locked doors and underground sub-areas
- boss-gated exits
- pause, game-over and campaign-complete states
- persistent best score, clear count and total deaths
- runtime HUD and contextual messages

## Settings & accessibility

Press **F10** from the title flow, gameplay or pause state.

Available persistent settings:

- master volume
- HUD text scale from 80% to 150%
- reduced flashing after damage
- assist health: +2 HP on newly loaded players
- extra lives: new campaigns start with at least 5 lives
- reset settings to defaults

Settings use PlayerPrefs and are independent from campaign progress.

## Generate and run

1. Open `games/SMB2_New_Life/UnityProject` in Unity 6.3 LTS.
2. Wait for scripts to compile.
3. Select `NES New Life > SMB2 > Create 20-Stage Campaign`.
4. Run `NES New Life > SMB2 > Validate 20-Stage Campaign`.
5. Open/play `Assets/NesNewLife/SMB2/Campaign/SMB2_Stage_01.unity`.
6. Choose a character with `1`, `2`, `3` or `4`.

The generator registers all twenty scenes in Build Settings automatically.

## Start-screen controls

| Action | Key |
|---|---|
| Select Mario / Luigi / Peach / Toad | 1 / 2 / 3 / 4 |
| Continue unfinished campaign | C |
| Previous unlocked stage | Q or `[` |
| Next unlocked stage | E or `]` |
| Start selected unlocked stage | Enter |
| Reset local campaign progress | N |
| Settings / accessibility | F10 |

## Gameplay controls

| Action | Key |
|---|---|
| Move | A/D or Left/Right |
| Jump | Space |
| Crouch / charge jump | S or Down |
| Climb | W/S or Up/Down in climbable zone |
| Jump away from climbable | Space |
| Pick up / throw | Left Shift / Right Shift |
| Pull buried item | Crouch + Shift near plant |
| Enter door | W or Up Arrow |
| Pause / resume | P or Esc |
| Settings / accessibility | F10 |
| New campaign after win/game over | R |

## Save / checkpoint behavior

The campaign save stores character, score, remaining lives, current stage and highest unlocked stage. Reaching a checkpoint additionally stores its world position for the current stage. Closing the game and choosing Continue restores that checkpoint when the stage loads again.

Checkpoint data is cleared when advancing to the next stage, starting a new campaign, abandoning a campaign, completing the campaign or resetting progress, preventing stale positions from leaking into another stage.

## Build Windows x64

Choose `NES New Life > SMB2 > Build Windows x64`.

If campaign scenes are missing, the builder generates all twenty first. Before invoking Unity's `BuildPipeline`, it runs the structural campaign validator. Any validation error aborts the build instead of producing a knowingly incomplete executable.

Output:

`Builds/Windows/NES_New_Life_SMB2.exe`

Compiled builds are ignored by Git and should only be published after a real Unity compile/play/build smoke test.

## Validation status

Source and project structure were reviewed statically. **A real Unity 6.3 LTS Editor compile, Play Mode pass, checkpoint persistence test and Windows executable launch were not performed in this run.** The repository therefore does not claim a tested binary yet.

## Next production milestones

- replace generated development layouts with richer handcrafted original rooms while retaining the 20-stage framework
- add additional enemy families, projectile/bomb interactions and boss archetypes
- modern original art, animation, VFX and camera feedback
- modern controller/Input System layer and remapping
- audio implementation that uses the persistent volume setting
- automated Unity CI compile/test/build once repository secrets are configured
- balancing, QA and first tested standalone release

## Legal / repository hygiene

Do not commit ROMs or commercial asset dumps. Public builds must use original or properly licensed assets.
