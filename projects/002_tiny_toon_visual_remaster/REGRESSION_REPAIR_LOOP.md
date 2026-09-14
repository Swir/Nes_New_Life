# Regression Defect → Repair Sprint → Same-Case Retest

`windows/Regression_Repair_Loop.bat` closes the operational gap after a real Final Regression Cockpit FAIL.

It does not auto-fix graphics and it never auto-passes gameplay. Instead it converts one authoritative current-build FAIL into the smallest safe local repair job that can be identified from the current production state, then sends that repair through the same transactional QA path used by normal HD art production.

## Flow

```text
current-build Final Regression FAIL
→ classify defect
→ ranked tile/palette/family locator during Guided Regression
→ local visual candidate board from the exact HD runtime
→ human-select the matching visible tile/palette
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

## Automatic target handoff from Guided Regression

The Guided Exact-Build Regression runner invokes the metadata-only Regression Defect Locator for art-related FAILs. The locator ranks candidates from the **whole current HD runtime**, not merely the files already present in the current sprint. It cross-references art groups and the family-aware sprint.

Before asking for the target number, `regression_visual_picker.py` renders those ranked candidates from the same fingerprint-bound runtime into a local visual board. Each card can contain several distinct variants for the same tile/palette, which is important for animation/palette/context defects that would be difficult to identify from hexadecimal IDs alone.

A selected target is stored in the FAIL notes as:

```text
[SWIR_TARGET tile=2E palette=FF16360F]
```

with an additional `SWIR_CONTEXT` note containing the selected group/family/condition context. The repair director parses the `SWIR_TARGET` marker, locks onto that exact tile/palette and expands only to family peers when appropriate.

This removes manual tile/palette transcription and most target guessing from the normal workflow while preserving human authority: selecting `0 = unknown` leaves the FAIL descriptive and the existing family/group fallback remains available.

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

The upstream Guided Regression launcher now:

1. records the real observed failure category;
2. ranks likely tile/palette/family/context targets;
3. opens the local visual candidate board;
4. lets the operator choose the matching visible target or `0 = unknown`;
5. writes the chosen `SWIR_TARGET` into the authoritative FAIL.

Then the Regression Repair Loop:

1. identifies the authoritative current FAIL;
2. consumes `SWIR_TARGET` automatically when Guided Regression captured a concrete target;
3. creates/opens `Artwork/CurrentRepairSprint`;
4. waits for the local edit;
5. runs transactional QA and commits only an all-green repair;
6. launches the repaired build through verified-fullscreen MesenCE;
7. shows the original case route/cues;
8. requires explicit local PASS/FAIL for that same case;
9. returns to the authoritative Final Regression Cockpit order afterward.

## Privacy / repository policy

Repair PNGs, references and contact boards are local ROM-derived production material and remain gitignored. Defect-locator JSON/CSV/normal HTML and repair-controller reports remain metadata-only by contract.

`Reports/RegressionDefectLocator/REGRESSION_VISUAL_PICKER_LOCAL_ONLY.html` is deliberately different: it embeds local HD-pack pixels so the operator can visually identify the defect. The entire `projects/**/Reports/` tree is gitignored; this picker must never be committed or uploaded.

The workflow never commits ROMs, save states, capture pixels, gameplay screenshots, ripped commercial art/audio, emulator binaries or derivative local HD packs.

This milestone improves Gate B/C execution but does not itself check any Gate A-D ROADMAP item.
