# SMB2 New Life

Project #001 in **NES New Life**.

> Public-safe modernization experiment inspired by the gameplay structure of a classic NES platformer. Commercial ROMs, ripped graphics, music and Nintendo-owned assets are not included.

## Current milestone

**`0.5.0-multi-stage-campaign`**

The project now has a reusable campaign layer instead of one isolated development scene. A single editor command generates a three-stage campaign, saves run state between scenes, restores the selected character/lives/score on transitions, unlocks progress, and builds all campaign scenes into the Windows executable.

## Recommended editor

**Unity 6.3 LTS** (`6000.3.x`). The project pins `6000.3.0f1` as its minimum baseline; newer 6000.3 LTS patches can upgrade it.

## Campaign architecture now playable

- generated three-stage campaign: `SMB2_Stage_01`, `SMB2_Stage_02`, `SMB2_Stage_03`
- persistent active-stage save
- selected character preserved between scenes
- lives and accumulated score preserved between scenes
- highest unlocked stage stored locally
- Continue returns to the saved campaign stage
- stage completion bonuses
- final-stage campaign completion and persistent clear statistics
- per-stage visual treatment
- later stages reshape platform heights and increase boss durability
- later stages inject progressively denser Hopper/Chaser encounters
- Windows build automatically generates missing campaign scenes and includes all three in order
- campaign-wide structural validator

## Existing gameplay systems

- Mario / Luigi / Peach / Toad profiles with different movement, jump, air control and throw power
- Peach-style temporary air float
- variable-height jumping, coyote time and jump buffering
- crouch and charged crouch-jump
- pickup, carry, throw and crouch+action plant pulling
- thrown-object combat
- patrol, hopping and proximity-chasing enemies
- contact damage, 3-point health, knockback and invulnerability
- lives, death, checkpoint respawn and pits
- score collectibles and healing
- room-specific camera bounds
- connected doors, keys and locked doors
- underground sub-area route
- miniboss/guardian encounter and boss-gated exit
- pause, game-over and campaign-complete states
- persistent best score, clear count and total deaths
- runtime HUD and contextual messages
- generated public-safe placeholder sprite

## Generate and run the campaign

1. Clone/download the repository.
2. In Unity Hub choose **Add project from disk**.
3. Select `games/SMB2_New_Life/UnityProject`.
4. Open it with Unity **6.3 LTS**.
5. If Unity reports that the legacy input API is disabled, set **Active Input Handling** to **Both** or **Input Manager (Old)** in Player settings and restart Unity if requested.
6. Wait until scripts finish compiling.
7. Select `NES New Life > SMB2 > Create 3-Stage Campaign`.
8. Run `NES New Life > SMB2 > Validate 3-Stage Campaign`.
9. Open/play `Assets/NesNewLife/SMB2/Campaign/SMB2_Stage_01.unity`.
10. Choose a character with `1`, `2`, `3` or `4`.

The campaign generator first creates the complete gameplay template and then produces three configured stage scenes in `Assets/NesNewLife/SMB2/Campaign/`.

## Campaign flow

1. choose a character and begin Stage 1
2. complete the surface/underground/key route and defeat the guardian
3. reach the exit; score/lives/character are saved and Stage 2 loads automatically
4. Stage 2 raises platform variation, encounter pressure and guardian durability
5. complete Stage 2 to transition into Stage 3 with the same run state
6. Stage 3 adds the highest current encounter pressure and strongest guardian
7. clear Stage 3 to record a full campaign completion
8. `R` after completion/game-over begins a fresh campaign
9. `C` on the start screen resumes an unfinished saved campaign at its saved stage

These are still development stages built from a reusable level template; they are not a claim that all original commercial SMB2 stages have been recreated.

## Controls

| Action | Key |
|---|---|
| Select Mario / Luigi / Peach / Toad | 1 / 2 / 3 / 4 |
| Continue saved campaign | C |
| Reset local progress | N |
| Move | A/D or Left/Right |
| Jump | Space |
| Crouch / charge jump | S or Down |
| Pick up / throw | Left Shift / Right Shift |
| Pull buried item | Crouch + Shift near a green plant |
| Enter door | W or Up Arrow |
| Pause / resume | P or Esc |
| New campaign after win/game over | R |

## Build a Windows EXE

Choose `NES New Life > SMB2 > Build Windows x64`.

If the three campaign scenes do not exist, the build command generates them automatically. The build includes Stage 1, Stage 2 and Stage 3 in that order and writes locally to `Builds/Windows/NES_New_Life_SMB2.exe`.

`Builds/` and compiled executables are intentionally ignored by Git. A tested build can later be attached to a GitHub Release.

## Validation

Use `NES New Life > SMB2 > Validate 3-Stage Campaign`. It checks every generated campaign scene for stage metadata, GameManager, player, exit, guardian and camera-follow structure. The older single-scene validator remains useful for the development template.

## Current art state

`v0.5` still deliberately uses generated colored graybox shapes. Gameplay/campaign architecture is being proven before the production pass replaces prototype presentation with modern original art, animation, VFX and audio.

## Next production milestones

- `0.6` vertical rooms, climbable traversal, richer hazards and a second boss archetype
- `0.7` modern original art pass, animation state machine, VFX and stronger camera feedback
- `0.8` audio, modern Input System/controller remapping, settings and accessibility
- `0.9` broader campaign content, balancing, QA and performance pass
- `1.0` first public-safe standalone release

## Validation status

Source and project structure are reviewed statically. A real Unity 6.3 LTS Editor compile/play-mode test is still required before treating any Windows binary as tested. The repository intentionally does not claim a successful binary build until that real smoke test exists.

## Legal / repository hygiene

Do not commit ROMs or commercial asset dumps. The root `.gitignore` blocks common ROM/dump/archive/executable formats. Reference material should stay local.
