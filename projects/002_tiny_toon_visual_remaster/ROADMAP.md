# Project #002 — HD Completion Roadmap

## Current milestone: capture completeness under control

The tooling path is now:

`MesenCE capture → Capture Mission Control → incremental production sync → automatic baseline → master-art batch → pixel QA → validation → one-click MesenCE playtest`

## Gate A — Complete local capture

- [ ] Boot/title/menu states
- [ ] Player idle/walk/run/crouch/jump/fall/land
- [ ] Player actions, damage, invulnerability and death
- [ ] Every normal route and scrolling boundary
- [ ] Alternate routes, secrets and revisits
- [ ] Every common enemy state
- [ ] Rare/route-specific enemies
- [ ] Every boss phase, attack, hit/death and effect
- [ ] HUD, text, pause/status/result screens
- [ ] Effects, projectiles and transitions
- [ ] Ending, credits and post-game states

Use `capture_mission_control.py`; the capture gate stays BLOCKED until these are explicitly verified.

## Gate B — HD art production

- [ ] Run resume-safe sync against the latest complete capture
- [ ] Seed untouched masters for full-pack baseline visibility
- [ ] Replace PLAYER/BOSS masters with final-quality art first
- [ ] Finish ENEMY/WORLD/UI/EFFECTS masters
- [ ] Resolve every UNASSIGNED art-queue row
- [ ] Zero TODO/INVALID masters

## Gate C — QA and regression

- [ ] Pixel QA PASS
- [ ] `hires.txt` mapping preserved
- [ ] No missing referenced PNGs
- [ ] 4x target preserved
- [ ] Full-game visual regression pass in MesenCE
- [ ] No animation seams, wrong palette contexts or transparency regressions

## Gate D — Release

- [ ] HD readiness gate PASS
- [ ] Runtime pack contains no ROM/save-state/patch payloads
- [ ] Final release ZIP built from validated pack only
- [ ] README screenshots/video captured from the user's local legally supplied game environment

A toolchain milestone is not the same as a finished remaster. Full HD completion requires the user's local full-game capture plus final artwork and real MesenCE regression testing.
