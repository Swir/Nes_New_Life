# Project #002 — HD Completion Roadmap

## Current milestone: GitHub Capture Evidence Triage + privacy-safe Local Capture Bridge + authoritative final path

<!-- SWIR-ROADMAP-STANDARD:v1 -->
<!-- ROADMAP-PROGRESS:START -->
<p align="center">
  <a href="https://github.com/Swir/Nes_New_Life/actions/workflows/project-002-tools.yml"><img alt="CI" src="https://github.com/Swir/Nes_New_Life/actions/workflows/project-002-tools.yml/badge.svg"></a>
  <img alt="Roadmap progress" src="https://img.shields.io/badge/ROADMAP-0.0%25-6b7280?style=for-the-badge">
  <img alt="Completed" src="https://img.shields.io/badge/DONE-0%2F52-1f6feb?style=for-the-badge">
  <img alt="Status" src="https://img.shields.io/badge/STATUS-RELEASE%20GATES%20OPEN-f59e0b?style=for-the-badge">
</p>

## 📊 Final release readiness

```text
░░░░░░░░░░░░░░░░░░░░ 0.0%
```

| ✅ Completed | ⏳ Remaining | 📦 Total | 🎯 Progress |
|---:|---:|---:|---:|
| **0** | **52** | **52** | **0.0%** |

> **Progress rule:** this dashboard measures only authoritative Gate A–D release checkboxes. Tooling work is not counted as finished release work. Update `[x]/[ ]` first, then update badges, numbers, percentage and the 20-segment bar. Never mark a gate complete without real local capture/art/QA evidence.
<!-- ROADMAP-PROGRESS:END -->

The production path is now:

`MesenCE capture → Local Capture Bridge → GitHub Capture Evidence Triage → Capture Mission Control → Capture Promotion Director → resume-safe sync → Visual Context Audit → Animation Family Workbench → Visual Completion Matrix → High-Impact Art Sprint → build-bound Pixel QA → one-click verified-fullscreen MesenCE playtest → Final Regression Cockpit → Final Release Readiness Director → gated ZIP`

The **GitHub Capture Evidence Triage** consumes only validator-approved safe snapshots from `evidence/capture/`. It compares evidence history, reports added/removed tile IDs, palettes and condition names, mapping/group growth, Capture Mission Control progress and explicit regressions, then emits one **DO THIS NEXT** action in the GitHub Actions summary. A snapshot with invalid metadata, non-4x scale, missing referenced capture images or explicit `CAPTURE_REGRESSION` is blocked from becoming an accepted evidence baseline. Gate A condition-name matches are only `CANDIDATE_REVIEW` hints and never auto-complete a ROADMAP checkbox.

The **Local Capture Bridge** closes the operational gap between a legally supplied local MesenCE session and the GitHub-hosted project. `windows/Local_Capture_Bridge.bat` inspects the current capture locally and emits only validator-approved metadata: mapping/tile/palette/condition counts, PLAYER/BOSS/ENEMY/WORLD/UI/EFFECTS group counts, image dimensions/sizes/SHA-256 hashes, Capture Mission Control status and capture-regression metadata. It never uploads ROM bytes, save states, capture pixels, emulator binaries or absolute local paths. When authenticated GitHub CLI is available, the launcher can send only the validated `SAFE_CAPTURE_HANDOFF.json` to a dedicated evidence PR; `.github/workflows/project-002-capture-evidence.yml` re-validates and triages it. Evidence arrival never auto-completes Gate A–D.

The **Authoritative Remaster Studio** exposes the current production path in one UI instead of sending the user through older Top-N / Release Candidate flows. F4 launches Local Capture Bridge, F5 runs safe capture promotion, and the remaining controls run Visual Completion Matrix, the exact matrix-selected High-Impact Art Sprint, conflict-safe finish + Pixel QA, verified-fullscreen playtest, Final Regression Cockpit and the seven-gate Final Release Readiness audit. Its Visual Completion percentage remains capture-bounded art information only and never changes this Gate A–D release percentage.

The **Capture Promotion Director** remains the preferred bridge from an accepted fresh local MesenCE capture into production. It validates the candidate, compares it with the previous accepted capture, and refuses to synchronize `ART_QUEUE.csv` or `MasterWorkspace` when `CAPTURE_REGRESSION` is present. A clean candidate can then run resume-safe sync, Visual Context, Animation Family, Final Art Priority and Production Sprint refresh in one pass.

The **Visual Completion Matrix** turns the captured-art backlog into measurable production progress instead of one flat TODO count. It reports completion for PLAYER, BOSS, ENEMY, WORLD, UI, EFFECTS and UNASSIGNED, includes usage-weighted completion, highlights invalid/classification blockers and writes `NEXT_HIGH_IMPACT_ART_BATCH.csv`. PLAYER/BOSS/ENEMY, invalid masters and high-reuse graphics receive more production weight so each local art session is aimed at visible game impact. The matrix is deliberately capture-bounded: it never claims that uncaptured states are complete.

The **High-Impact Art Sprint Director** removes the ranking-to-execution gap. `windows/High_Impact_Art_Sprint.bat` runs the matrix and exports the exact `NEXT_HIGH_IMPACT_ART_BATCH` selection into a local editable/reference sprint kit with impact scores, reasons, dimensions and SHA-256 workspace state. `windows/Finish_High_Impact_Art_Sprint.bat` reuses the stale-conflict-aware Art Sprint importer, preserves `hires.txt`, composes a candidate HD pack and runs Pixel QA. The local sprint board and PNGs remain ROM-derived local production material and are never committed.

The **Fullscreen-by-Contract Playtest** closes a user-facing readiness gap: the one-click Windows playtest no longer stops after installing the pack. It launches the user's local ROM in MesenCE with native fullscreen requested, checks the actual emulator window against the active monitor, retries with F11 when needed and rejects a windowed launch. When a runtime pack is supplied, the launcher writes exact-build metadata-only fullscreen evidence tied to the current HD-pack fingerprint.

The **Final Release Readiness Director** makes that fullscreen evidence packaging-authoritative. A public ZIP can now pass only when HD Pack structure, Capture Mission Control, final art, Visual Context, Pixel QA, verified fullscreen and all ten Final Regression Cockpit cases are simultaneously green. Pixel QA, fullscreen and regression must all match the exact current `hires.txt + runtime PNG` fingerprint. Any late runtime-art change invalidates old evidence and blocks packaging until the changed build is re-tested.

The main production stack now covers privacy-safe evidence transfer and GitHub-side history triage, capture planning, regression-safe capture promotion, quantified visual completion, exact high-impact art execution, exact-build fullscreen launch, exact-build regression and a single final release decision. **PRODUCTION SPRINT** still combines Capture Mission Control, capture regressions, Visual Context Review, Animation Family Review, MasterWorkspace progress and Final Art Priority into one metadata-only **DO THIS NEXT** dashboard.

Final Art Priority remains useful for broader review, while High-Impact Art Sprint is now the fastest default production path after the Visual Completion Matrix. Sprint kits are edited locally and imported through stale-conflict checks, exact dimensions, `hires.txt` preservation, validation and Pixel QA.

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

After each targeted MesenCE session, run `windows/Local_Capture_Bridge.bat` first to create a privacy-safe evidence handoff and optionally send that metadata to GitHub. GitHub Evidence Triage will compare it against older accepted snapshots and expose regressions/growth in CI without checking any ROADMAP box automatically. Then run `windows/Promote_Capture_To_HD.bat` (preferably with the previous accepted capture selected). A candidate with capture regression must remain unpromoted until the lost state is recaptured. Capture Mission Control remains explicit full-game evidence.

## Gate B — HD art production

- [ ] Promote only the latest valid, non-regressed capture through Capture Promotion Director
- [ ] Confirm resume-safe sync preserved existing edited masters and artist decisions
- [ ] Generate/refresh `VISUAL_CONTEXT_REVIEW.csv` and clear every high-risk palette/condition/variant family
- [ ] Generate/refresh `ANIMATION_FAMILY_REVIEW.csv` and inspect high-risk player/enemy/boss animation families
- [ ] Run `windows/High_Impact_Art_Sprint.bat` to refresh Visual Completion Matrix and export its exact highest-impact batch
- [ ] Work only `Artwork/CurrentImpactSprint/editable/*.png`; preserve dimensions, alpha canvas and filenames
- [ ] Finish through `windows/Finish_High_Impact_Art_Sprint.bat`; stale workspace conflicts or dimension changes must block import
- [ ] Confirm candidate pack preserves `hires.txt` and Pixel QA PASSes before continuing
- [ ] Resolve every invalid master and every UNASSIGNED classification blocker reported by the matrix
- [ ] Repeat High-Impact Art Sprint until PLAYER/BOSS/ENEMY high-visibility backlog is exhausted, then finish WORLD/UI/EFFECTS
- [ ] Use local animation contact sheets for transition/seam review where useful
- [ ] Re-run visual-context and animation-family audits after major capture/art changes
- [ ] Zero TODO/INVALID masters in every captured group

Studio's MasterWorkspace remains the authoritative local source of final art. Sprint kits are temporary focused editing surfaces. Exact duplicates can be propagated safely; near-duplicates remain review hints only. Condition co-occurrence candidates are inspection hints, not reconstructed screen layouts.

## Gate C — QA, fullscreen launch and exact-build regression

- [ ] High-Impact Art Sprint finish or Studio **Apply full workspace + QA** passes against the exact final runtime pack
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
- [ ] Visual Completion Matrix has zero captured TODO/invalid/classification blockers
- [ ] Visual Context Review exists and has no pending/stale high-risk families
- [ ] Current-build Pixel QA is PASS
- [ ] Final Regression Cockpit has 10/10 PASS for the exact current fingerprint
- [ ] Final user-facing playtest has verified fullscreen evidence for the exact current fingerprint
- [ ] Runtime pack contains no ROM/save-state/patch payloads
- [ ] Final release ZIP is built only through `final_release_director.py package` / the PASS path in `windows/Final_Release_Gate.bat`
- [ ] README screenshots/video captured from the user's local legally supplied game environment

## Highest-impact remaining work

The tooling now reaches from a local MesenCE capture through privacy-safe GitHub evidence **and history triage**, quantified captured-art completion, exact batch execution, packaging-authoritative verified fullscreen and exact-build regression. The largest remaining blockers are real content/evidence work:

1. complete local MesenCE capture of every route/state/boss/effect/ending and feed each session through **Local Capture Bridge**, letting GitHub Evidence Triage reject regressions and rank the next capture target without receiving ROM/capture pixels,
2. promote each accepted non-regressed capture through **Capture Promotion Director** before it can touch production state,
3. clear Visual Context / high-risk animation reviews produced by the promoted capture,
4. repeatedly run **High-Impact Art Sprint** so the exact matrix-selected PLAYER/BOSS/ENEMY/invalid/high-reuse backlog becomes editable immediately and reaches zero TODO/invalid,
5. resolve every art-queue classification and finish WORLD/UI/EFFECTS,
6. run the QA-gated **verified-fullscreen** playtest and drive **Final Regression Cockpit** from FAIL/STALE/PENDING to 10/10 current-build PASS,
7. run **Final Release Gate** and create the public HD Pack ZIP only after all seven exact-build gates are green (without ROM/emulator/save-state content).

A toolchain milestone is not the same as a finished remaster. Full HD completion still requires real full-game capture evidence, final artwork and real MesenCE regression testing. Local Capture Bridge plus GitHub Evidence Triage minimize manual handoff and make regressions visible without inventing or faking completion.
