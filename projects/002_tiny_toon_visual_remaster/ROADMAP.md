# Project #002 — HD Completion Roadmap

## Current milestone: unified build-bound release gate

The production path is now:

`MesenCE capture → Capture Mission Control → incremental production sync → automatic baseline → master-art batch → pixel QA → validation → one-click MesenCE playtest → build-bound full-game regression → Unified Release Candidate Gate → safe ZIP`

The final gate intentionally refuses stale evidence: changing `hires.txt` or any referenced runtime PNG invalidates previous final Art QA and full-game regression completion for the older build.

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

## Gate C — QA and build-bound regression

- [ ] Run `bound_art_qa.py` against the exact final runtime pack
- [ ] Pixel QA PASS and fingerprint matches the current build
- [ ] `hires.txt` mapping preserved
- [ ] No missing referenced PNGs
- [ ] 4x target preserved
- [ ] Complete all final regression cases in MesenCE against the exact current fingerprint
- [ ] No animation seams, wrong palette contexts or transparency regressions
- [ ] Re-run any stale QA/regression evidence after a late runtime-art change

## Gate D — Release

- [ ] `release_candidate.py audit` reports `RELEASE GATE: PASS`
- [ ] Capture missions are complete
- [ ] Art queue has 0 TODO and 0 UNASSIGNED rows
- [ ] Current-build pixel QA is PASS
- [ ] Current-build full-game visual regression is complete
- [ ] Runtime pack contains no ROM/save-state/patch payloads
- [ ] Final release ZIP built through the gated `release_candidate.py package` command
- [ ] README screenshots/video captured from the user's local legally supplied game environment

A toolchain milestone is not the same as a finished remaster. Full HD completion still requires the user's local full-game capture, final artwork and real MesenCE regression testing. The new unified gate makes those remaining requirements explicit and prevents an older successful test run from being reused after the playable HD assets change.
