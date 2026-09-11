# NES New Life — Roadmap

## Project philosophy

1. Recreate the gameplay loop before visual polish.
2. Keep each game isolated in `games/<project>/`.
3. Move truly reusable systems into `shared/`.
4. Never commit commercial ROMs, ripped music, sprites or other unlicensed assets.
5. Every playable milestone receives a game-prefixed version tag.

## #001 — SMB2 New Life

### Milestone 0.1 — Foundation
- [x] Repository initialized
- [x] ROM header documented locally
- [x] Unity source layout created
- [x] Basic player locomotion script
- [x] Carry / throw system foundation
- [ ] Test scene
- [ ] Camera follow system
- [ ] Character stats profiles
- [ ] Basic enemy prototype
- [ ] Door / transition prototype

### Milestone 0.2 — Core loop
- [ ] Four character archetypes
- [ ] Lift timing and carry poses
- [ ] Throwable vegetables / objects
- [ ] Damage / invulnerability
- [ ] Enemy interactions
- [ ] Ladders / vines / doors
- [ ] One complete graybox level

### Milestone 0.3 — Presentation
- [ ] Original replacement art direction
- [ ] Parallax backgrounds
- [ ] Particles and hit feedback
- [ ] Modern UI and pause menu
- [ ] Audio mixer and replacement SFX/music
- [ ] 16:9 camera framing

### Milestone 0.5 — Beta
- [ ] Multiple complete levels
- [ ] Save / checkpoint system
- [ ] Controller remapping
- [ ] Accessibility settings
- [ ] Performance pass

### Milestone 1.0
- [ ] Full playable public-safe build using original/licensed assets
- [ ] Windows build
- [ ] Release notes
- [ ] Screenshots / trailer assets
- [ ] GitHub Release `smb2-v1.0.0`

## Shared framework targets

Future reusable modules:
- input abstraction
- save system
- game state machine
- scene transitions
- camera framework
- audio manager
- settings menu
- localization hooks
- controller support
- build/version metadata
