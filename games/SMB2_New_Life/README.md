# SMB2 New Life

Project #001 in **NES New Life**.

> Public-safe modernization experiment inspired by the gameplay structure of a classic NES platformer. Commercial ROMs, ripped graphics, music and Nintendo-owned assets are not included.

## Current milestone

**`0.6.0-vertical-traversal-and-hazards`**

The campaign now supports genuinely different traversal patterns instead of only horizontal variants. Stages can contain climbable vertical routes, moving platforms, crumble platforms, environmental damage hazards and multiple guardian archetypes.

## Recommended editor

**Unity 6.3 LTS** (`6000.3.x`). The project pins `6000.3.0f1` as its minimum baseline; newer 6000.3 LTS patches can upgrade it.

## Campaign architecture now playable

- generated three-stage campaign: `SMB2_Stage_01`, `SMB2_Stage_02`, `SMB2_Stage_03`
- persistent active-stage save
- selected character, lives and accumulated score preserved between scenes
- highest unlocked stage stored locally
- Continue returns to the saved campaign stage
- stage completion bonuses and final-stage campaign completion
- per-stage visual treatment and encounter pressure
- Stage 1 introduces a safe climb route
- Stage 2 adds mandatory elevated exit traversal, moving platforms, crumble platforms and spikes
- Stage 3 combines the vertical/hazard systems with a faster charge guardian
- Windows build automatically generates missing campaign scenes and includes all three in order
- campaign-wide structural validator covers the critical v0.6 systems

## Existing gameplay systems

- Mario / Luigi / Peach / Toad profiles with different movement, jump, air control and throw power
- Peach-style temporary air float
- variable-height jumping, coyote time and jump buffering
- crouch and charged crouch-jump
- climbable vine/ladder-style traversal with jump-off support
- pickup, carry, throw and crouch+action plant pulling
- thrown-object combat
- patrol, hopping and proximity-chasing enemies
- two guardian archetypes: jumping guardian and timed charge guardian
- contact damage, 3-point health, knockback and invulnerability
- moving platforms, respawning crumble platforms and spike hazards
- lives, death, checkpoint respawn and pits
- score collectibles and healing
- room-specific camera bounds
- connected doors, keys and locked doors
- underground sub-area route
- boss-gated exits
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

The generator creates the gameplay template and then produces three configured stage scenes in `Assets/NesNewLife/SMB2/Campaign/`.

## Campaign flow

1. choose a character and begin Stage 1
2. complete the surface/underground/key route and defeat the guardian
3. learn the climb mechanic on the Stage 1 vertical route
4. reach the exit; score/lives/character are saved and Stage 2 loads automatically
5. Stage 2 introduces moving and crumbling platforms, spike hazards and a mandatory climb to the elevated exit
6. Stage 3 combines the hazard set with additional moving-platform pressure and a charge-focused guardian
7. clear Stage 3 to record a full campaign completion
8. `R` after completion/game-over begins a fresh campaign
9. `C` on the start screen resumes an unfinished saved campaign at its saved stage

These are still development stages built from reusable original/public-safe systems; they are not a claim that all original commercial SMB2 stages have been recreated.

## Controls

| Action | Key |
|---|---|
| Select Mario / Luigi / Peach / Toad | 1 / 2 / 3 / 4 |
| Continue saved campaign | C |
| Reset local progress | N |
| Move | A/D or Left/Right |
| Jump | Space |
| Crouch / charge jump | S or Down |
| Climb | W/S or Up/Down while touching a green climbable zone |
| Jump away from climbable | Space |
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

Use `NES New Life > SMB2 > Validate 3-Stage Campaign`. It checks stage metadata, GameManager, player, exit, camera, guardian presence and the v0.6 traversal/hazard requirements. Stage 2+ must contain moving platforms, crumble platforms and spikes; Stage 3 must contain the charge guardian.

## Current art state

`v0.6` still deliberately uses generated colored graybox shapes. Gameplay and campaign architecture are being proven before the production pass replaces prototype presentation with modern original art, animation, VFX and audio.

## Next production milestones

- `0.7` richer room archetypes, more enemy behaviors, throwable/bomb interactions and additional boss logic
- `0.8` modern original art pass, animation state machine, VFX and stronger camera feedback
- `0.9` audio, modern Input System/controller remapping, settings, accessibility, balancing and QA
- `1.0` first public-safe standalone release

## Validation status

Source and project structure are reviewed statically. A real Unity 6.3 LTS Editor compile/play-mode test is still required before treating any Windows binary as tested. The repository intentionally does not claim a successful binary build until that real smoke test exists.

## Legal / repository hygiene

Do not commit ROMs or commercial asset dumps. The root `.gitignore` blocks common ROM/dump/archive/executable formats. Reference material should stay local.
