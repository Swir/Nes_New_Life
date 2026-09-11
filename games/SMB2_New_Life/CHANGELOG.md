# Changelog — SMB2 New Life

All notable development milestones for Project #001 are recorded here.

## [0.6.0-vertical-traversal-and-hazards] - 2026-09-11

### Added
- climbable vine/ladder-style traversal zones
- player climbing state with vertical movement and jump-off behavior
- moving platform system with configurable travel vectors
- respawning crumble platforms
- reusable damage spike hazards
- mandatory elevated exits in later campaign stages
- vertical ledges and climb routes generated into the campaign
- second guardian archetype with timed high-speed charge attacks
- additional Stage 3 moving-platform pressure
- campaign validation coverage for climbables, moving platforms, crumble platforms, spikes and the charge guardian

### Changed
- Stage 1 introduces climbing as a safe traversal mechanic
- Stage 2 requires climbing after its guardian encounter and introduces environmental hazards
- Stage 3 combines climbing, moving/crumbling platforms, spikes and the new charge guardian
- campaign exits now correctly remain locked while either guardian archetype is alive

## [0.5.0-multi-stage-campaign] - 2026-09-11

### Added
- reusable campaign stage metadata component
- three-stage campaign catalog and scene naming convention
- active campaign save state: current stage, run score and remaining lives
- persistent highest unlocked stage
- scene-to-scene campaign transition bridge
- Continue flow that returns to the exact saved campaign stage
- one-click `Create 3-Stage Campaign` editor command
- generated Stage 1 / Stage 2 / Stage 3 scenes with distinct names and completion bonuses
- per-stage color treatment and platform-height variation
- progressive per-stage Hopper/Chaser encounter pressure
- progressively stronger stage guardians
- campaign-wide structural validator
- campaign stage name/progress display in HUD

### Changed
- stage exits now advance the campaign instead of always ending the run
- lives, character and score persist across campaign scenes
- final stage records a campaign clear; intermediate stages save and advance
- Windows builder now generates missing campaign scenes automatically and builds all three in order
- game-over/replay flow now starts a fresh campaign

## [0.4.0-progression-and-enemy-variety] - 2026-09-11

### Added
- persistent local campaign progress using Unity PlayerPrefs
- saved last selected character
- persistent best score, clear count and death count
- continue shortcut from the character-select screen
- explicit local progress reset shortcut
- veteran-run difficulty hook based on completed runs
- hopping enemy archetype that aims jumps toward the player
- proximity chaser enemy archetype with patrol fallback
- runtime encounter enhancer that injects new enemy archetypes into surface and underground sections
- additional veteran-run chaser encounter after the first clear
- HUD campaign statistics
- one-click playable-scene structural validator in the Unity editor

### Changed
- deaths and successful clears are now recorded persistently
- character selection now restores the last played character for continue flow
- level-complete screen shows best score and clear count
- generated v0.3 scene receives richer encounters without requiring commercial assets

## [0.3.0-world-flow-foundation] - 2026-09-11

### Added
- connected door portals between separate gameplay rooms
- player key inventory and key pickups
- key-gated doors with optional key consumption
- room-specific camera zones and world bounds
- HUD key counter and contextual world messages
- mandatory underground sub-area in the generated level
- progression barrier that requires the underground route
- crouch + action pullable-plant interaction
- buried throwable items generated on both surface and underground routes
- underground enemies, collectibles, healing and dedicated fall zone

### Changed
- generated playable level is now multi-room instead of one continuous strip
- camera can switch bounds when entering different rooms
- checkpoint moved behind the key-gated progression route
- controls documentation now includes doors and plant pulling

## [0.2.0-playable-vertical-slice] - 2026-09-11

### Added
- self-contained Unity 6.3 LTS project baseline
- four selectable character profiles with distinct movement values
- temporary air-float ability for the Peach profile
- player HP, knockback, invulnerability and blinking feedback
- lives, score, checkpoint respawn, game-over and win states
- patrol enemies with contact damage
- thrown-object combat
- score collectibles and health pickups
- fall kill zones
- midpoint checkpoint
- final 5-HP miniboss arena
- goal locked until boss defeat
- runtime HUD and replay flow
- one-click complete playable level generator
- one-click Windows x64 build command

### Changed
- corrected ground detection to use an isolated ground layer
- expanded carry pickup radius and per-character throw strength
- prototype scene generator now produces `SMB2_Playable.unity`

## [0.1.0-foundation]

### Added
- initial NES New Life repository structure
- verified iNES reference metadata documentation
- Unity 2D player movement foundation
- acceleration and deceleration
- variable jump
- coyote time and jump buffering
- crouch and charged-jump prototype hook
- pickup / carry / throw system
- smooth 2D camera follow
- one-click Unity prototype scene generator
- ROM and dump ignore rules
