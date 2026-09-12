# Project #002 — HD Completion Roadmap

## Current milestone: animation-family production workbench + enforced visual-context release gate

The production path is now:

`MesenCE capture → Capture Mission Control → incremental production sync → Visual Context Audit → Animation Family Workbench → automatic baseline → master-art batch → build-bound pixel QA → one-click MesenCE playtest → build-bound full-game regression → Unified Release Candidate Gate → gated ZIP`

Visual Context Review is now an actual authoritative release requirement rather than documentation-only guidance. Missing, pending or stale high-risk visual-context review blocks the final release gate.

The Animation Family Workbench groups condition-driven states into semantic families and emits condition co-occurrence candidates for local inspection. It deliberately does not infer on-screen sprite geometry from HD texture-sheet coordinates. Local contact sheets can be generated for production review and remain gitignored.

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
- [ ] Generate `VISUAL_CONTEXT_REVIEW.csv` and clear every high-risk palette/condition/variant family
- [ ] Generate `ANIMATION_FAMILY_REVIEW.csv` and inspect high-risk player/enemy/boss animation families
- [ ] Use local animation contact sheets for transition/seam review where useful
- [ ] Seed untouched masters for full-pack baseline visibility
- [ ] Replace PLAYER/BOSS masters with final-quality art first
- [ ] Finish ENEMY/WORLD/UI/EFFECTS masters
- [ ] Resolve every UNASSIGNED art-queue row
- [ ] Re-run visual-context and animation-family audits after major capture/art changes
- [ ] Zero TODO/INVALID masters

Studio's MasterWorkspace remains the primary local batch-edit surface. Exact duplicates can be propagated safely; near-duplicates remain review hints only. Condition co-occurrence candidates are inspection hints, not reconstructed screen layouts.

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
- [ ] Visual Context Review exists and has no pending/stale high-risk families
- [ ] Current-build pixel QA is PASS
- [ ] Current-build full-game visual regression is complete
- [ ] Runtime pack contains no ROM/save-state/patch payloads
- [ ] Final release ZIP built only through Studio **GATED release ZIP** or the gated `release_candidate.py package` command
- [ ] README screenshots/video captured from the user's local legally supplied game environment

## Highest-impact remaining work

The largest remaining blockers are now primarily local content/evidence work:

1. complete local MesenCE capture of every route/state/boss/effect/ending,
2. clear the enforced Visual Context Review on the latest final-art pack,
3. inspect high-risk animation families and condition-cooccurrence candidates in-game,
4. finish the real 4x art pass for every captured master,
5. resolve every art-queue classification,
6. run full-game visual regression on the exact final fingerprint,
7. only then create the gated public HD Pack ZIP (without ROM/emulator/save-state content).

A toolchain milestone is not the same as a finished remaster. Full HD completion still requires the user's local full-game capture, final artwork and real MesenCE regression testing.
