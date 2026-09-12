# Project #002 — HD Completion Roadmap

## Current milestone: exact-build Final Regression Cockpit + direct final-art execution

The production path is now:

`MesenCE capture → Capture Mission Control → PRODUCTION SPRINT → Capture Gap Planner → incremental production sync → Visual Context Audit → Animation Family Workbench → Final Art Priority Board → Final Art Sprint Kit → build-bound Pixel QA → one-click MesenCE playtest → Final Regression Cockpit → Unified Release Candidate Gate → gated ZIP`

The main production stack now covers capture planning, prioritized art execution and exact-build verification. **PRODUCTION SPRINT** combines Capture Mission Control, capture regressions, Visual Context Review, Animation Family Review, MasterWorkspace progress and Final Art Priority into one metadata-only **DO THIS NEXT** dashboard.

Final Art Priority and Final Art Sprint remain focused on real captured graphics: Top-N unfinished masters are exported into `Artwork/CurrentArtSprint`, edited locally, then imported through stale-conflict checks, exact dimensions, `hires.txt` preservation, validation and Pixel QA.

The **Final Regression Cockpit** turns the last manual QA phase into a fingerprint-bound workflow. Each of the ten authoritative full-game cases is marked PASS/FAIL only after real MesenCE verification. FAIL results carry a defect category and stay blocking until re-tested. Any later runtime PNG or `hires.txt` change makes older PASS evidence STALE automatically.

These production accelerators do not prove whole-game completeness. Capture Mission Control remains the explicit source of truth for full-game capture coverage and real in-game MesenCE regression remains authoritative for final animation/context correctness.

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

Use Studio **Capture Mission Control** / **Record capture session**. After each session, click **PRODUCTION SPRINT** and work from its highest-priority action. Use **Capture Gap Planner** when comparing a previous and current capture. Tile-count growth never auto-completes a mission.

## Gate B — HD art production

- [ ] Run resume-safe sync against the latest complete, non-regressed capture
- [ ] Generate `VISUAL_CONTEXT_REVIEW.csv` and clear every high-risk palette/condition/variant family
- [ ] Generate `ANIMATION_FAMILY_REVIEW.csv` and inspect high-risk player/enemy/boss animation families
- [ ] Generate `FINAL_ART_NEXT.csv` and work the highest-scoring unfinished masters first
- [ ] Export Top-N work through Studio **Create Top-N Art Sprint** into `Artwork/CurrentArtSprint`
- [ ] Redraw sprint `editable/*.png` while keeping dimensions unchanged
- [ ] Finish each sprint through Studio **Finish Sprint + Pixel QA**
- [ ] Refresh **PRODUCTION SPRINT** after every successful sprint
- [ ] Use local animation contact sheets for transition/seam review where useful
- [ ] Replace PLAYER/BOSS masters with final-quality art first
- [ ] Finish ENEMY/WORLD/UI/EFFECTS masters
- [ ] Resolve every UNASSIGNED art-queue row
- [ ] Re-run visual-context and animation-family audits after major capture/art changes
- [ ] Zero TODO/INVALID masters

Studio's MasterWorkspace remains the authoritative local source of final art. Sprint kits are temporary focused editing surfaces. Exact duplicates can be propagated safely; near-duplicates remain review hints only. Condition co-occurrence candidates are inspection hints, not reconstructed screen layouts.

## Gate C — QA and exact-build regression

- [ ] Use Studio **Finish Sprint + Pixel QA** or **Apply full workspace + QA** against the exact final runtime pack
- [ ] Pixel QA PASS and fingerprint matches the current build
- [ ] `hires.txt` mapping preserved
- [ ] No missing referenced PNGs
- [ ] 4x target preserved
- [ ] Build/deploy the current pack through **One-click HD Playtest**
- [ ] Open `windows/Final_Regression_Cockpit.bat` (or the CLI cockpit) against the exact deployed/final pack
- [ ] Work the cockpit's `DO THIS NEXT` case in real MesenCE gameplay
- [ ] Record visible problems as FAIL with defect category; fix them and re-test the same case
- [ ] Complete all ten cases with current-build PASS evidence
- [ ] No animation seams, wrong palette contexts, missing HD coverage, mapping errors or transparency regressions
- [ ] Re-run stale QA/regression evidence after any late runtime-art change

## Gate D — Release

- [ ] Studio **Release Candidate Audit** / `release_candidate.py audit` reports `RELEASE GATE: PASS`
- [ ] Capture missions are complete
- [ ] Art queue has 0 TODO and 0 UNASSIGNED rows
- [ ] Visual Context Review exists and has no pending/stale high-risk families
- [ ] Current-build pixel QA is PASS
- [ ] Final Regression Cockpit has 10/10 PASS for the exact current fingerprint
- [ ] Runtime pack contains no ROM/save-state/patch payloads
- [ ] Final release ZIP built only through Studio **GATED release ZIP** or the gated `release_candidate.py package` command
- [ ] README screenshots/video captured from the user's local legally supplied game environment

## Highest-impact remaining work

The tooling now reaches from capture through exact-build regression. The largest remaining blockers are local content/evidence work:

1. complete local MesenCE capture of every route/state/boss/effect/ending,
2. use **PRODUCTION SPRINT** after each session and eliminate capture regressions / high-priority PLAYER-BOSS-ENEMY gaps,
3. sync the accepted capture and clear Visual Context / high-risk animation reviews,
4. repeatedly create and finish Top-N Final Art Sprints until captured TODO/INVALID work is exhausted,
5. resolve every art-queue classification,
6. run the QA-gated playtest and drive **Final Regression Cockpit** from FAIL/STALE/PENDING to 10/10 current-build PASS,
7. only then create the gated public HD Pack ZIP (without ROM/emulator/save-state content).

A toolchain milestone is not the same as a finished remaster. Full HD completion still requires the user's local full-game capture, final artwork and real MesenCE regression testing.
