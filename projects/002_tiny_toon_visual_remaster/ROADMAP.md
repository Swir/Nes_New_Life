# Project #002 — HD Completion Roadmap

## Current milestone: visual-context / animation-risk production audit

The production path is now:

`MesenCE capture → Capture Mission Control → incremental production sync → visual-context risk audit → automatic baseline → master-art batch → build-bound pixel QA → one-click MesenCE playtest → build-bound full-game regression → Unified Release Candidate Gate → gated ZIP`

The new Visual Context Audit targets the highest-risk real-art cases before final polish: tile families reused across multiple palettes, Mesen conditions or visually distinct captured forms. It produces a local metadata-only review queue and invalidates a prior `REVIEWED` decision when that family's fingerprint changes.

The final release gate still refuses stale exact-build QA/regression evidence: changing `hires.txt` or any referenced runtime PNG invalidates previous final Art QA and full-game regression completion for the older build.

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
- [ ] Generate `VISUAL_CONTEXT_REVIEW.csv` and clear the highest-risk palette/condition/variant families first
- [ ] Seed untouched masters for full-pack baseline visibility
- [ ] Replace PLAYER/BOSS masters with final-quality art first
- [ ] Finish ENEMY/WORLD/UI/EFFECTS masters
- [ ] Resolve every UNASSIGNED art-queue row
- [ ] Re-run Visual Context Audit after major capture/art changes; stale reviews must be rechecked
- [ ] Zero TODO/INVALID masters

Studio's MasterWorkspace remains the primary local batch-edit surface. Exact duplicates can be propagated safely; near-duplicates remain review hints only. `visual_context_audit.py` adds a separate family-level check so visually distinct palette/condition contexts are not accidentally treated as interchangeable.

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
- [ ] Visual Context Audit has no pending/stale high-risk family review
- [ ] Current-build pixel QA is PASS
- [ ] Current-build full-game visual regression is complete
- [ ] Runtime pack contains no ROM/save-state/patch payloads
- [ ] Final release ZIP built only through Studio **GATED release ZIP** or the gated `release_candidate.py package` command
- [ ] README screenshots/video captured from the user's local legally supplied game environment

## Highest-impact remaining work

The tooling path is substantially closed end-to-end. The largest remaining blockers are content/evidence work that cannot be fabricated in CI:

1. complete local MesenCE capture of every route/state/boss/effect/ending,
2. run Visual Context Audit and verify the highest-risk palette/condition/animation families in-game,
3. finish the real 4x art pass for every captured master,
4. resolve every art-queue classification,
5. run full-game visual regression on the exact final fingerprint,
6. only then create the gated public HD Pack ZIP (without ROM/emulator/save-state content).

A toolchain milestone is not the same as a finished remaster. Full HD completion still requires the user's local full-game capture, final artwork and real MesenCE regression testing.
