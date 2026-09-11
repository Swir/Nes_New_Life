# SMB2 New Life

Project #001 in **NES New Life**.

> Public-safe modernization experiment inspired by the gameplay structure of a classic NES platformer. Commercial ROMs, ripped graphics, music and Nintendo-owned assets are not included.

## Current milestone

**`0.7.0-seven-world-campaign-framework`**

The project now has a complete campaign-scale progression framework: **7 worlds and 20 stage slots**, matching the useful high-level scope of a full-length classic campaign while keeping all generated layouts, names and presentation original/public-safe.

This is not a claim that the original commercial levels have been recreated 1:1. The 20 generated scenes are development stages built from reusable systems so every future handcrafted level has a real slot, save path, transition, validation path and build target already in place.

## Recommended editor

**Unity 6.3 LTS** (`6000.3.x`). The project pins `6000.3.0f1` as its baseline.

## Campaign architecture

- 7 worlds
- 20 generated campaign stages
- world structure: `3 + 3 + 3 + 3 + 3 + 3 + 2`
- stage IDs/names from `1-1` through `7-2`
- scene naming `SMB2_Stage_01` through `SMB2_Stage_20`
- automatic stage-to-world mapping
- persistent current stage and highest unlocked stage
- selected character, lives and score preserved between scenes
- Continue returns to the exact unfinished stage
- unlocked-stage selector from the start screen (`Q/E`, then `Enter`)
- world finales detected by the catalog
- later world finales use the charge-guardian archetype
- final Stage 20 is marked as the campaign finale
- Windows build includes all 20 scenes in progression order
- campaign validator checks all 20 generated scenes

## Generated world progression

The generator now scales encounters and traversal across the full campaign instead of cloning three identical development levels:

- World 1 introduces climbing and basic moving traversal
- World 2 increases moving-platform pressure and adds environmental hazards
- World 3 adds crumble traversal and charge-guardian finales
- World 4 adds horizontal moving-platform challenges
- World 5 adds denser vertical/crumble combinations
- World 6 increases hazard and guardian pressure further
- World 7 contains the two-stage final world with the strongest generated guardian configuration

Each world also receives a distinct public-safe color treatment and simple geometric landmarks. These are placeholders for the later original art pass.

## Existing gameplay systems

- Mario / Luigi / Peach / Toad profiles with different movement, jump, air control and throw power
- Peach-style temporary air float
- variable-height jumping, coyote time and jump buffering
- crouch and charged crouch-jump
- climbable traversal with jump-off support
- pickup, carry, throw and crouch+action plant pulling
- thrown-object combat
- patrol, hopping and proximity-chasing enemies
- jumping and charge guardian archetypes
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

## Generate and run

1. Open `games/SMB2_New_Life/UnityProject` in Unity 6.3 LTS.
2. Wait for scripts to compile.
3. Select `NES New Life > SMB2 > Create 20-Stage Campaign`.
4. Run `NES New Life > SMB2 > Validate 20-Stage Campaign`.
5. Open/play `Assets/NesNewLife/SMB2/Campaign/SMB2_Stage_01.unity`.
6. Choose a character with `1`, `2`, `3` or `4`.

The generator registers all twenty scenes in Build Settings automatically.

## Start-screen progression controls

| Action | Key |
|---|---|
| Select Mario / Luigi / Peach / Toad | 1 / 2 / 3 / 4 |
| Continue unfinished campaign | C |
| Previous unlocked stage | Q or `[` |
| Next unlocked stage | E or `]` |
| Start selected unlocked stage | Enter |
| Reset local progress | N |

Stage select never allows a stage above the highest unlocked save value.

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
| New campaign after win/game over | R |

## Build Windows x64

Choose `NES New Life > SMB2 > Build Windows x64`.

If campaign scenes are missing, the builder generates all 20 first. Output remains:

`Builds/Windows/NES_New_Life_SMB2.exe`

Compiled builds are ignored by Git and should only be published after a real Unity compile/play/build smoke test.

## Validation status

Source and project structure are reviewed statically. **A real Unity 6.3 LTS Editor compile, Play Mode pass and Windows executable launch have not been performed in this run.** The repository therefore does not claim a tested binary yet.

## Next production milestones

- replace generated development layouts with richer handcrafted original rooms while retaining the 20-stage campaign framework
- add more enemy families, projectile/bomb interactions and boss archetypes
- modern original art, animation, VFX and camera feedback
- audio, modern Input System/controller remapping, settings and accessibility
- automated Unity CI compile/test/build once repository secrets are configured
- balancing, QA and first tested standalone release

## Legal / repository hygiene

Do not commit ROMs or commercial asset dumps. Public builds must use original or properly licensed assets.
