# Capture Gap Art → Same-Case Retest

`windows/Finish_Capture_Gap_Art_And_Retest.bat` closes the second half of regression `CAPTURE_GAP` recovery.

After `Regression_Capture_Gap_Recovery.bat` has gathered and verified the missing real gameplay capture and handed it into the authoritative HD art pipeline, this launcher finishes the resulting `CurrentImpactSprint` through the existing transactional visual/animation/Pixel QA stack, binds the rebuilt runtime to the original failed regression case, launches verified-fullscreen MesenCE and requires an explicit local PASS/FAIL for that **same case**.

## Flow

```text
verified CAPTURE_GAP recovery
→ evidence-bound HD art handoff
→ edit CurrentImpactSprint/editable
→ Finish_Capture_Gap_Art_And_Retest.bat
→ transactional visual quality gate
→ animation-family consistency gate
→ candidate composition
→ hires.txt preservation
→ Pixel QA
→ repaired runtime fingerprint
→ fingerprint-bound capture-gap retest token
→ verified-fullscreen MesenCE
→ re-test ONLY the original failed case
→ explicit PASS / FAIL
→ continue authoritative 10/10 regression
```

## Fail-closed binding

The retest is prepared only when:

- the recovery token is valid;
- the recovery report is `CAPTURE_RECOVERED_READY_FOR_HD_HANDOFF`;
- the original `FAIL / CAPTURE_GAP` still exists in authoritative `FINAL_REGRESSION.json` history;
- the recovered capture fingerprint differs from the failed source capture;
- transactional art finish produces a runtime pack containing `hires.txt`;
- the repaired runtime fingerprint differs from the source runtime that originally failed.

The generated `REGRESSION_CAPTURE_GAP_RETEST_TOKEN.json` binds source runtime, source capture, recovered capture, repaired runtime and exact regression case.

If the repaired runtime changes after the token is generated, result recording is refused and the case must be planned again.

## PASS does not mean Gate C complete

A same-case PASS records only that exact regression case on the repaired runtime fingerprint. Any previous cases that became `STALE` after the runtime changed still require new real MesenCE verification. Gate C remains blocked until all ten authoritative cases PASS on one final exact runtime fingerprint.

If the same case still FAILs, the new failure category is recorded normally and immediately re-enters the existing capture/art/runtime repair routing.

## Privacy / legal boundary

The retest director stores metadata only: fingerprints, case key, mission keys, counts and PASS/FAIL metadata. It does not commit ROM bytes, save states, capture pixels, screenshots, emulator binaries, ripped commercial assets or local derivative HD packs.

The ROM remains local and is used only by MesenCE for actual gameplay verification.

## ROADMAP policy

This workflow does not edit Gate A-D checkboxes. Recovery, transactional QA and retest tooling are execution infrastructure; release progress changes only from real reviewed capture/art/QA evidence under the existing ROADMAP rules.
