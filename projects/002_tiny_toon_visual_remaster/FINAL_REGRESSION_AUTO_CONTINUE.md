# Final Regression Auto-Continue Director

`windows/Auto_Continue_Final_Regression.bat` is the highest-level Project #002 final visual regression runner.

It does **not** automate visual judgment. Every PASS/FAIL still comes from a real observation of the exact current HD-pack fingerprint in verified-fullscreen MesenCE.

## What it removes

Before this director, the operator had to manually decide which of several final-regression launchers to run after every PASS, repair, restart or changed fingerprint. The director now sequences those existing authoritative tools without weakening their evidence rules.

## State machine

- `PLAYTEST_CASE_REQUIRED` → launch the existing Guided Exact-Build Regression workflow for the current authoritative case.
- PASS → re-plan immediately and continue to the next required case.
- FAIL → persistent Regression Recovery Session becomes authoritative.
- `RECOVERY_REPAIR_REQUIRED` → route to the exact art/capture-gap/mapping/runtime repair path and stop at the real repair boundary.
- after the repair changes the runtime fingerprint, `SAME_CASE_RETEST_REQUIRED` → resume the remembered failed case before normal ordering.
- verified same-case PASS → normal ordering resumes on the repaired fingerprint.
- any earlier PASS from the old fingerprint is `STALE` and is re-tested; it is never carried forward as release evidence.
- `REGRESSION_COMPLETE` is emitted only when all 10 cases PASS on one exact current fingerprint, then the director dispatches the Final Release Gate.

A 30-iteration orchestration safety stop prevents accidental infinite loops.

## Windows

Run:

```text
windows/Auto_Continue_Final_Regression.bat
```

Authoritative Production Studio exposes the same flow as:

```text
CTRL+ALT+F9 — AUTO-CONTINUE FINAL REGRESSION
```

## Evidence and safety

The Python director emits metadata-only JSON/HTML under `Reports/FinalRegressionAutoContinue/`. It does not store ROM bytes, capture PNG/JPG pixels, screenshots, save states or emulator binaries.

The director never writes PASS itself. It delegates gameplay observation and recording to the existing Guided Regression and Recovery workflows. A real repair remains a hard boundary: the loop stops there and must be resumed after the runtime or mapping/capture state has actually changed.

No ROADMAP Gate A-D checkbox is modified by this tooling milestone.
