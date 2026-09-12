# Project #002 — HD Completion Roadmap

## Current milestone: Studio production command center + unified build-bound release gate

The production path is now:

`MesenCE capture → Capture Mission Control → incremental production sync → automatic baseline → master-art batch → build-bound pixel QA → one-click MesenCE playtest → build-bound full-game regression → Unified Release Candidate Gate → gated ZIP`

Remaster Studio now exposes that same authoritative path. The old GUI-level direct ZIP path has been removed: Studio packaging is blocked unless the unified release gate passes for the exact current runtime fingerprint.

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

Use Studio **Capture Mission Control** / **Record capture session** or `capture_mission_control.py`. Tile-count growth never auto-completes a mission; the capture gate stays BLOCKED until coverage is explicitly verified.

## Gate B — HD art production

- [ ] Run resume-safe sync against the latest complete capture
- [ ] Seed untouched masters for full-pack baseline visibility
- [ ] Replace PLAYER/BOSS masters with final-quality art first
- [ ] Finish ENEMY/WORLD/UI/EFFECTS masters
- [ ] Resolve every UNASSIGNED art-queue row
- [ ] Zero TODO/INVALID masters

Studio's MasterWorkspace remains the primary local batch-edit surface. Exact duplicates can be propagated safely; near-duplicates remain review hints only.

## Gate C — QA and exact-build regression

- [ ] Use Studio **Apply + build-bound QA** or run `bound_art_qa.py` against the exact final runtime pack
- [ ] Pixel QA PASS and fingerprint matches the current build
- [ ] `hires.txt` mapping preserved
- [ ] No missing referenced PNGs
- [ ] 4x target preserved
- [ ] Build/deploy the current pack through **One-click HD Playtest**
- [ ] Complete all final regression cases in MesenCE against the exact current fingerprint
- [ ] No animation seams, wrong palette contexts or transparency regressions
- [ ] Re-run stale QA/regression evidence after any late runtime-art change

## Gate D — Release

- [ ] Studio **Release Candidate Audit** / `release_candidate.py audit` reports `RELEASE GATE: PASS`
- [ ] Capture missions are complete
- [ ] Art queue has 0 TODO and 0 UNASSIGNED rows
- [ ] Current-build pixel QA is PASS
- [ ] Current-build full-game visual regression is complete
- [ ] Runtime pack contains no ROM/save-state/patch payloads
- [ ] Final release ZIP built only through Studio **GATED release ZIP** or the gated `release_candidate.py package` command
- [ ] README screenshots/video captured from the user's local legally supplied game environment

## Highest-impact remaining work

The tooling path is now substantially closed end-to-end. The remaining blockers are overwhelmingly content/evidence work that cannot be fabricated in CI:

1. complete local MesenCE capture of every route/state/boss/effect/ending,
2. finish the real 4x art pass for every captured master,
3. resolve every art-queue classification,
4. run full-game visual regression on the exact final fingerprint,
5. only then create the gated public HD Pack ZIP (without ROM/emulator/save-state content).

A toolchain milestone is not the same as a finished remaster. Full HD completion still requires the user's local full-game capture, final artwork and real MesenCE regression testing. The unified gate and Studio command center now make those boundaries explicit and prevent old or partial evidence from being treated as release-ready.
