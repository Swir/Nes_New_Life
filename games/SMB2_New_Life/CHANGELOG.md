# Changelog — SMB2 New Life

All notable development milestones for Project #001 are recorded here.

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
- variable-height jump
- coyote time and jump buffering
- crouch and charged-jump prototype hook
- pickup / carry / throw system
- smooth 2D camera follow
- one-click Unity prototype scene generator
- ROM and dump ignore rules
