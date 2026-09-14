# Project #002 — HD Completion Roadmap

## Current milestone: Ledger-backed Capture Review → evidence-bound HD art handoff → authoritative final path

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

`Guided fullscreen MesenCE capture → explicit Capture Mission Control attestation → Local Capture Bridge → GitHub Capture Evidence Triage → fingerprint-bound Capture Coverage Acceptance → Capture Review Director → ledger-backed VERIFIED_GATE_A review → Evidence-bound Art Handoff v2 → acceptance-gated Capture Promotion Director → resume-safe sync → Visual Context Audit → Animation Family Workbench → Visual Completion Matrix → family-aware High-Impact Art Sprint → transactional visual/family/Pixel QA → one-click verified-fullscreen MesenCE playtest → Final Regression Cockpit → Final Release Readiness Director → gated ZIP`

The **Guided Capture Marathon** is now the fastest route through the real Gate A blocker. `windows/Guided_Capture_Marathon.bat` launches the user's legally supplied local ROM through the verified-fullscreen MesenCE path, loads all eleven Capture Mission Control missions, displays targeted gameplay cues and records a mission only after an explicit in-game verification choice. It never infers completion from tile/palette/image growth. Skipped or unplayed missions remain pending. When the session ends it writes a metadata-only marathon dashboard and runs Local Capture Bridge against the exact same capture so evidence handoff does not require re-selecting inputs.

The **GitHub Capture Evidence Triage** consumes only validator-approved safe snapshots from `evidence/capture/`. It compares evidence history, reports added/removed tile IDs, palettes and condition names, mapping/group growth, Capture Mission Control progress and explicit regressions, then emits one **DO THIS NEXT** action in the GitHub Actions summary. A snapshot with invalid metadata, non-4x scale, missing referenced capture images or explicit `CAPTURE_REGRESSION` is blocked from becoming an accepted evidence baseline. Gate A condition-name matches are only `CANDIDATE_REVIEW` hints and never auto-complete a ROADMAP checkbox.

The **Local Capture Bridge** closes the operational gap between a legally supplied local MesenCE session and the GitHub-hosted project. `windows/Local_Capture_Bridge.bat` inspects the current capture locally and emits only validator-approved metadata: mapping/tile/palette/condition counts, PLAYER/BOSS/ENEMY/WORLD/UI/EFFECTS group counts, image dimensions/sizes/SHA-256 hashes, Capture Mission Control status and capture-regression metadata. It never uploads ROM bytes, save states, capture pixels, emulator binaries or absolute local paths. Its PowerShell entry point accepts scripted current/previous capture inputs so Guided Capture Marathon can hand off the exact session without duplicate selection. When authenticated GitHub CLI is available, the launcher can send only the validated `SAFE_CAPTURE_HANDOFF.json` to a dedicated evidence PR; `.github/workflows/project-002-capture-evidence.yml` re-validates and triages it. Evidence arrival never auto-completes Gate A–D.

The **Capture Coverage Acceptance** checkpoint binds the current capture fingerprint, Capture Integrity Ledger, all eleven mission provenance records and structural PLAYER/BOSS/ENEMY/WORLD/UI/EFFECTS signals into one metadata-only decision. `READY_FOR_GATE_A_REVIEW` means hard metadata/provenance blockers are clean, not that Gate A is automatically complete. `BLOCKED` preserves the exact blocker list and one `DO THIS NEXT` action. Authoritative Remaster Studio exposes this checkpoint directly so the operator can see whether the current capture is safe, incomplete or stale before promotion.

The **Evidence-bound Art Handoff v2** closes the reviewed-capture → real 4x production gap without weakening Gate A semantics. `windows/Evidence_Bound_Art_Handoff.bat` reuses the local-only capture-session state, refreshes Capture Review Director without forcing another play session and validates both `GATE_A_REVIEW_HANDOFF.json` and the actual `GATE_A_ATTESTATIONS.json` ledger against the exact current capture fingerprint. `FULL_GATE_A_HANDOFF` requires 12/12 ledger-backed `VERIFIED_GATE_A` attestations. Safe incomplete capture may continue only as the existing incremental-art mode. After admission it uses the authoritative Capture Production Director + HD Art Autopilot, preserves an existing sprint, generates the exact family-aware high-impact batch and resolves the Active Family Workbench. It never changes ROADMAP itself.

The **Authoritative Remaster Studio** exposes the current production path in one UI instead of sending the user through older Top-N / Release Candidate flows. F4 launches Local Capture Bridge, **CHECK CAPTURE ACCEPTANCE** / Ctrl+F5 runs the fingerprint-bound acceptance checkpoint, F5 runs acceptance-gated safe capture promotion, **Ctrl+Shift+F11** launches the ledger-backed Evidence-bound Art Handoff, and the remaining controls run Visual Completion Matrix, the exact matrix-selected High-Impact Art Sprint, conflict-safe finish + Pixel QA, verified-fullscreen playtest, Final Regression Cockpit and the seven-gate Final Release Readiness audit. The standalone Guided Capture Marathon is the preferred long-form Gate A capture session. Visual Completion percentage remains capture-bounded art information only and never changes this Gate A–D release percentage.

The **Capture Promotion Director** is now acceptance-gated before it can mutate production state. It validates the candidate, generates fresh Capture Coverage Acceptance evidence and classifies promotion admission as `FULL_CAPTURE_READY`, `INCREMENTAL_CAPTURE_READY` or `UNSAFE_CAPTURE`. Integrity admission failure, structural capture failure, capture regression, at-risk verified missions or untrusted mission provenance block synchronization of `ART_QUEUE.csv` / `MasterWorkspace`. Pending missions and not-yet-seen groups continue to block full Gate A/release but do not unnecessarily prevent safe incremental HD art production. A safe candidate can then run resume-safe sync, Visual Context, Animation Family, Final Art Priority and Production Sprint refresh in one pass.

The **Visual Completion Matrix** turns the captured-art backlog into measurable production progress instead of one flat TODO count. It reports completion for PLAYER, BOSS, ENEMY, WORLD, UI, EFFECTS and UNASSIGNED, includes usage-weighted completion, highlights invalid/classification blockers and writes `NEXT_HIGH_IMPACT_ART_BATCH.csv`. PLAYER/BOSS/ENEMY, invalid masters and high-reuse graphics receive more production weight so each local art session is aimed at visible game impact. The matrix is deliberately capture-bounded: it never claims that uncaptured states are complete.

The **High-Impact Art Sprint Director** removes the ranking-to-execution gap. `windows/High_Impact_Art_Sprint.bat` runs the matrix and exports the exact `NEXT_HIGH_IMPACT_ART_BATCH` selection into a local editable/reference sprint kit with impact scores, reasons, dimensions and SHA-256 workspace state. `windows/Finish_High_Impact_Art_Sprint.bat` reuses the stale-conflict-aware Art Sprint importer, preserves `hires.txt`, composes a candidate HD pack and runs Pixel QA. The local sprint board and PNGs remain ROM-derived local production material and are never committed.

The **Fullscreen-by-Contract Playtest** closes a user-facing readiness gap: the one-click Windows playtest no longer stops after installing the pack. It launches the user's local ROM in MesenCE with native fullscreen requested, checks the actual emulator window against the active monitor, retries with F11 when needed and rejects a windowed launch. When a runtime pack is supplied, the launcher writes exact-build metadata-only fullscreen evidence tied to the current HD-pack fingerprint.

The **Final Release Readiness Director** makes that fullscreen evidence packaging-authoritative. A public ZIP can now pass only when HD Pack structure, Capture Mission Control, final art, Visual Context, Pixel QA, verified fullscreen and all ten Final Regression Cockpit cases are simultaneously green. Pixel QA, fullscreen and regression must all match the exact current `hires.txt + runtime PNG` fingerprint. Any late runtime-art change invalidates old evidence and blocks packaging until the changed build is re-tested.

The main production stack now covers guided evidence-first gameplay capture, privacy-safe evidence transfer and GitHub-side history triage, fingerprint-bound acceptance/review/attestation, ledger-backed safe art admission, regression/provenance-safe capture promotion, quantified visual completion, exact family-aware art execution, exact-build fullscreen launch, exact-build regression and a single final release decision. **PRODUCTION SPRINT** still combines Capture Mission Control, capture regressions, Visual Context Review, Animation Family Review, MasterWorkspace progress and Final Art Priority into one metadata-only **DO THIS NEXT** dashboard.

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

Use `windows/Guided_Capture_Marathon.bat` as the default full-game capture runner. It starts verified-fullscreen MesenCE, works these mission areas one at a time and records completion only after explicit in-game verification. At the end it runs Local Capture Bridge automatically. GitHub Evidence Triage compares the safe metadata against older accepted snapshots and exposes regressions/growth without checking any ROADMAP box automatically. Run Capture Coverage Acceptance to see exact hard blockers and fingerprint-bound mission provenance. After each real review, `windows/Evidence_Bound_Art_Handoff.bat` can safely route the same exact fingerprint into incremental/final 4x production; a candidate with unsafe integrity/provenance or capture regression remains blocked. Safe incomplete capture may feed incremental art production but cannot satisfy Gate A.

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

The tooling now reaches from a guided verified-fullscreen gameplay session through privacy-safe GitHub evidence/history triage, fingerprint-bound capture acceptance/review/attestation, a ledger-backed evidence-bound art handoff, guarded incremental production, quantified captured-art completion, exact family-aware batch execution, packaging-authoritative verified fullscreen and exact-build regression. The largest remaining blockers are real content/evidence work:

1. run **Guided Capture Marathon** against the real local game and verify every route/state/boss/effect/ending mission; send each session through Local Capture Bridge so GitHub Evidence Triage can reject regressions without receiving ROM/capture pixels,
2. run **Capture Coverage Acceptance + Capture Review Director** and resolve integrity/provenance/regression blockers; explicitly attest only real gameplay evidence with `VERIFIED_GATE_A`,
3. run **Evidence-bound Art Handoff v2** so the exact reviewed fingerprint is admitted through Capture Production Director + HD Art Autopilot and opens the highest-impact Active Family Workbench,
4. clear Visual Context / high-risk animation reviews produced by the promoted capture,
5. repeatedly finish the **family-aware High-Impact Art Sprint** so the exact matrix-selected PLAYER/BOSS/ENEMY/invalid/high-reuse backlog reaches zero TODO/invalid,
6. resolve every art-queue classification and finish WORLD/UI/EFFECTS,
7. run the QA-gated **verified-fullscreen** playtest and drive **Final Regression Cockpit** from FAIL/STALE/PENDING to 10/10 current-build PASS,
8. run **Final Release Gate** and create the public HD Pack ZIP only after all seven exact-build gates are green (without ROM/emulator/save-state content).

A toolchain milestone is not the same as a finished remaster. Full HD completion still requires real full-game capture evidence, final artwork and real MesenCE regression testing. Guided Capture Marathon plus ledger-backed evidence-bound art handoff now minimizes manual bookkeeping while preventing unsafe/stale capture or fake Gate A review from silently entering production.
