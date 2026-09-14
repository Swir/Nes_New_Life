# Regression Defect → Repair Sprint → Same-Case Retest

`windows/Regression_Repair_Loop.bat` closes the operational gap after a real Final Regression Cockpit FAIL.

It does not auto-fix graphics and it never auto-passes gameplay. Instead it converts one authoritative current-build FAIL into the smallest safe local repair job that can be identified from the current production state, then sends that repair through the same transactional QA path used by normal HD art production.

## Flow

```text
current-build Final Regression FAIL
→ classify defect
→ resolve exact active family / affected production group
→ re-export minimal repair files from current MasterWorkspace
→ edit CurrentRepairSprint/editable
→ master visual quality gate
→ animation-family consistency gate
→ candidate HD pack
→ hires.txt preservation
→ Pixel QA
→ atomic commit / rollback
→ repaired runtime fingerprint
→ verified-fullscreen MesenCE
→ re-test the SAME failed case
→ PASS or FAIL on the repaired fingerprint
→ continue full authoritative 10/10 regression
```

The repair sprint is deliberately exported from the **current MasterWorkspace** rather than copying old CurrentImpactSprint pixels/hashes. That prevents a stale sprint from overwriting newer artist work.

## Defect routing

Art-repair categories can create a minimal sprint:

- `MISSING_HD`
- `WRONG_PALETTE`
- `ANIMATION_SEAM`
- `TRANSPARENCY`
- `OTHER` when the current production target is known

Categories that must not be papered over with pixels are routed away before any sprint is created:

- `CAPTURE_GAP` → Capture Review Director / real gameplay capture
- `MAPPING` → repair `hires.txt` mapping provenance
- `SCALE_OR_FILTER` → repair runtime/fullscreen/4x presentation

Character failures prefer the current PLAYER/ENEMY/BOSS Active Family Workbench so related animation/palette frames stay together. For WORLD/UI/EFFECTS the director falls back to the failed regression case's production group in the current high-impact sprint.

If failure notes contain an optional structured hint such as:

```text
[SWIR_TARGET tile=2E palette=FF16360F]
```

the director targets that tile/palette and expands to its selected family peers. The hint is advisory targeting metadata only; it never proves gameplay coverage.

## Fingerprint-bound same-case retest

A successful transactional repair creates local-only:

```text
Artwork/CurrentRepairSprint/REPAIR_RETEST_TOKEN.json
```

The token binds:

- the original failed regression case,
- its original failure category,
- the source runtime fingerprint that produced the FAIL,
- the repaired runtime fingerprint.

Before recording the repair retest, the tool verifies that the original FAIL actually exists in `FINAL_REGRESSION.json` history and that the repaired pack still matches the token fingerprint.

This allows the operator to immediately re-check the exact defect that was just repaired. A repair PASS does **not** waive other stale/pending regression cases. Any runtime-art change can stale prior PASS evidence, so Gate C still requires all ten cases to PASS on the final exact runtime fingerprint.

## Windows one-click

Run:

```text
windows/Regression_Repair_Loop.bat
```

The launcher:

1. identifies the authoritative current FAIL;
2. creates/opens `Artwork/CurrentRepairSprint`;
3. waits for the local edit;
4. runs transactional QA and commits only an all-green repair;
5. launches the repaired build through verified-fullscreen MesenCE;
6. shows the original case route/cues;
7. requires explicit local PASS/FAIL for that same case;
8. returns to the authoritative Final Regression Cockpit order afterward.

## Privacy / repository policy

Repair PNGs, references and contact boards are local ROM-derived production material and remain gitignored. Reports committed by the project code are metadata-only by contract; the workflow never commits ROMs, save states, capture pixels, gameplay screenshots, ripped commercial art/audio, emulator binaries or derivative local HD packs.

This milestone improves Gate B/C execution but does not itself check any Gate A-D ROADMAP item.
