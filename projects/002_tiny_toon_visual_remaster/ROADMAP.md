# Project #002 — HD Completion Roadmap

## Current milestone: final-art sprint execution + targeted capture planning

The production path is now:

`MesenCE capture → Capture Mission Control → Capture Gap Planner → incremental production sync → Visual Context Audit → Animation Family Workbench → Final Art Priority Board → Final Art Sprint Kit → master-art batch → build-bound pixel QA → one-click MesenCE playtest → build-bound full-game regression → Unified Release Candidate Gate → gated ZIP`

The Capture Gap Planner compares repeated local captures and produces a ranked **CAPTURE NEXT** queue. Coverage that existed in an older capture but disappears from the current one is treated as a high-priority regression. PLAYER/BOSS/ENEMY families also receive advisory missing-state suggestions so local play sessions can target the most likely visual gaps first.

The Final Art Priority Board converts the latest accepted capture plus art/review evidence into a ranked **FINAL ART NEXT** queue. The new Final Art Sprint Kit turns the Top-N entries into an actual local batch-edit folder with reference copies, exact dimensions, export hashes and a priority contact board. Sprint import is stale-workspace aware and refuses silent overwrite conflicts. Sprint finish imports edits, composes the pack, preserves `hires.txt`, validates the pack and runs pixel QA in one operation.

These rankings and sprint tools are production accelerators, not proof of whole-game completeness. Capture Mission Control remains the explicit source of truth for full-game coverage and exact-build regression remains authoritative for final animation correctness.

Visual Context Review is an authoritative release requirement. Missing, pending or stale high-risk visual-context review blocks the final release gate.

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
- [ ] Compare repeated captures and resolve any `CAPTURE_REGRESSION` rows before promoting a newer capture to production baseline

Use Studio **Capture Mission Control** / **Record capture session** or `capture_mission_control.py`. After each targeted session, run `capture_gap_planner.py` (or Studio orchestration) against the previous and current capture and work from the top of `CAPTURE_NEXT.csv`. Tile-count growth never auto-completes a mission.

## Gate B — HD art production

- [ ] Run resume-safe sync against the latest complete, non-regressed capture
- [ ] Generate `VISUAL_CONTEXT_REVIEW.csv` and clear every high-risk palette/condition/variant family
- [ ] Generate `ANIMATION_FAMILY_REVIEW.csv` and inspect high-risk player/enemy/boss animation families
- [ ] Generate `FINAL_ART_NEXT.csv` and work the highest-scoring unfinished masters first
- [ ] Export Top-N work through `art_sprint_kit.py` / Studio into `Artwork/CurrentArtSprint`
- [ ] Redraw sprint `editable/*.png` while keeping dimensions unchanged
- [ ] Finish each sprint through the safe import + compose + Pixel QA path
- [ ] Use local animation contact sheets for transition/seam review where useful
- [ ] Replace PLAYER/BOSS masters with final-quality art first
- [ ] Finish ENEMY/WORLD/UI/EFFECTS masters
- [ ] Resolve every UNASSIGNED art-queue row
- [ ] Re-run Final Art Priority Board after each successful sprint so completed masters fall out of the queue
- [ ] Re-run visual-context and animation-family audits after major capture/art changes
- [ ] Zero TODO/INVALID masters

Studio's MasterWorkspace remains the authoritative local source of final art. Sprint kits are temporary focused editing surfaces. Exact duplicates can be propagated safely; near-duplicates remain review hints only. Condition co-occurrence candidates are inspection hints, not reconstructed screen layouts.

## Gate C — QA and exact-build regression

- [ ] Use Studio **Apply + build-bound QA** or the Sprint Kit `finish` path against the exact final runtime pack
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
2. use Capture Gap Planner between sessions and eliminate capture regressions / high-priority PLAYER-BOSS-ENEMY gaps,
3. sync the accepted capture and refresh Final Art Priority Board,
4. repeatedly export/finalize Top-N Final Art Sprint Kits until captured TODO/INVALID work is exhausted,
5. clear the enforced Visual Context Review and inspect high-risk animation families,
6. resolve every art-queue classification,
7. run full-game visual regression on the exact final fingerprint,
8. only then create the gated public HD Pack ZIP (without ROM/emulator/save-state content).

A toolchain milestone is not the same as a finished remaster. Full HD completion still requires the user's local full-game capture, final artwork and real MesenCE regression testing.
