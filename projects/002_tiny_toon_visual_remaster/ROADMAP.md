# Project #002 — HD Completion Roadmap

## Current milestone: exact-build Final Release Readiness Director

The production path is now:

`MesenCE capture → Capture Mission Control → Capture Promotion Director → resume-safe sync → Visual Context Audit → Animation Family Workbench → Final Art Priority Board → Final Art Sprint Kit → build-bound Pixel QA → one-click verified-fullscreen MesenCE playtest → Final Regression Cockpit → Final Release Readiness Director → gated ZIP`

The **Capture Promotion Director** remains the preferred bridge from a fresh local MesenCE capture into production. It validates the candidate, compares it with the previous accepted capture, and refuses to synchronize `ART_QUEUE.csv` or `MasterWorkspace` when `CAPTURE_REGRESSION` is present. A clean candidate can then run resume-safe sync, Visual Context, Animation Family, Final Art Priority and Production Sprint refresh in one pass and optionally prepare the next Top-N Art Sprint immediately.

The **Fullscreen-by-Contract Playtest** closes a user-facing readiness gap: the one-click Windows playtest no longer stops after installing the pack. It launches the user's local ROM in MesenCE with native fullscreen requested, checks the actual emulator window against the active monitor, retries with F11 when needed and rejects a windowed launch. When a runtime pack is supplied, the launcher writes exact-build metadata-only fullscreen evidence tied to the current HD-pack fingerprint.

The **Final Release Readiness Director** makes that fullscreen evidence packaging-authoritative. A public ZIP can now pass only when HD Pack structure, Capture Mission Control, final art, Visual Context, Pixel QA, verified fullscreen and all ten Final Regression Cockpit cases are simultaneously green. Pixel QA, fullscreen and regression must all match the exact current `hires.txt + runtime PNG` fingerprint. Any late runtime-art change invalidates old evidence and blocks packaging until the changed build is re-tested.

The main production stack now covers capture planning, regression-safe capture promotion, prioritized art execution, exact-build fullscreen launch, exact-build regression and a single final release decision. **PRODUCTION SPRINT** still combines Capture Mission Control, capture regressions, Visual Context Review, Animation Family Review, MasterWorkspace progress and Final Art Priority into one metadata-only **DO THIS NEXT** dashboard.

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
- [ ] Compare repeated captures and resolve every `CAPTURE_REGRESSION` before promoting a newer capture to production baseline

After each targeted MesenCE session, run `windows/Promote_Capture_To_HD.bat` (preferably with the previous accepted capture selected). A candidate with capture regression must remain unpromoted until the lost state is recaptured. Capture Promotion never auto-completes gameplay missions; continue using Capture Mission Control for explicit full-game evidence.

## Gate B — HD art production

- [ ] Promote only the latest valid, non-regressed capture through Capture Promotion Director
- [ ] Confirm resume-safe sync preserved existing edited masters and artist decisions
- [ ] Generate/refresh `VISUAL_CONTEXT_REVIEW.csv` and clear every high-risk palette/condition/variant family
- [ ] Generate/refresh `ANIMATION_FAMILY_REVIEW.csv` and inspect high-risk player/enemy/boss animation families
- [ ] Generate `FINAL_ART_NEXT.csv` and work the highest-scoring unfinished masters first
- [ ] Export Top-N work into `Artwork/CurrentArtSprint` (the director can do this during promotion)
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

## Gate C — QA, fullscreen launch and exact-build regression

- [ ] Use Studio **Finish Sprint + Pixel QA** or **Apply full workspace + QA** against the exact final runtime pack
- [ ] Pixel QA PASS and fingerprint matches the current build
- [ ] `hires.txt` mapping preserved
- [ ] No missing referenced PNGs
- [ ] 4x target preserved
- [ ] Build/deploy the current pack through **One-click HD Playtest**
- [ ] One-click playtest launches the local ROM in MesenCE automatically
- [ ] Fullscreen is verified against the active monitor bounds; windowed-only playtest is rejected
- [ ] `Reports/FullscreenPlaytest/FULLSCREEN_PLAYTEST.json` matches the exact current runtime fingerprint
- [ ] Open `windows/Final_Regression_Cockpit.bat` against the exact deployed/final pack
- [ ] Work the cockpit's `DO THIS NEXT` case in real MesenCE gameplay
- [ ] Record visible problems as FAIL with defect category; fix them and re-test the same case
- [ ] Complete all ten cases with current-build PASS evidence
- [ ] No animation seams, wrong palette contexts, missing HD coverage, mapping errors or transparency regressions
- [ ] Re-run stale QA/regression/fullscreen evidence after any late runtime-art change

## Gate D — Release

- [ ] Run `windows/Final_Release_Gate.bat` or `final_release_director.py audit`
- [ ] Final Release Readiness Director reports `FINAL RELEASE GATE: PASS`
- [ ] Capture missions are complete
- [ ] Art queue has 0 TODO and 0 UNASSIGNED rows
- [ ] Visual Context Review exists and has no pending/stale high-risk families
- [ ] Current-build Pixel QA is PASS
- [ ] Final Regression Cockpit has 10/10 PASS for the exact current fingerprint
- [ ] Final user-facing playtest has verified fullscreen evidence for the exact current fingerprint
- [ ] Runtime pack contains no ROM/save-state/patch payloads
- [ ] Final release ZIP is built only through `final_release_director.py package` / the PASS path in `windows/Final_Release_Gate.bat`
- [ ] README screenshots/video captured from the user's local legally supplied game environment

## Highest-impact remaining work

The tooling now reaches from capture through packaging-authoritative verified fullscreen and exact-build regression. The largest remaining blockers are local content/evidence work:

1. complete local MesenCE capture of every route/state/boss/effect/ending,
2. promote each new capture through **Capture Promotion Director** and eliminate every regression before it can touch production state,
3. clear Visual Context / high-risk animation reviews produced by the promoted capture,
4. repeatedly create and finish Top-N Final Art Sprints until captured TODO/INVALID work is exhausted,
5. resolve every art-queue classification,
6. run the QA-gated **verified-fullscreen** playtest and drive **Final Regression Cockpit** from FAIL/STALE/PENDING to 10/10 current-build PASS,
7. run **Final Release Gate** and create the public HD Pack ZIP only after all seven exact-build gates are green (without ROM/emulator/save-state content).

A toolchain milestone is not the same as a finished remaster. Full HD completion still requires the user's local full-game capture, final artwork and real MesenCE regression testing.
