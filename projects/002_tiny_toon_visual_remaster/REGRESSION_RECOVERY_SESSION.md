# Regression Recovery Session

Project #002 now keeps a **local, persistent recovery lock** whenever Final Regression records a real FAIL.

The problem this solves is exact-build ordering after repair. A repaired HD pack has a new fingerprint, so earlier PASS evidence can become `STALE`. Without a persistent lock, normal regression ordering could choose one of those earlier stale cases before returning to the defect that was just repaired.

## Local state

The recovery state is stored outside the repository:

```text
%LOCALAPPDATA%\Swir\TinyToonVisualRemaster\regression-recovery-session.json
```

It contains metadata only: case key/label, failure category/notes, source and current HD-pack fingerprints, phase, route launcher and a bounded transition history. It does not contain ROM bytes, capture pixels, screenshots, save states or emulator binaries.

## Phases

- `REPAIR_REQUIRED` — the remembered case still FAILs on the exact source fingerprint. The unified router sends it to the category-appropriate repair workflow.
- `RETEST_REQUIRED` — the runtime fingerprint changed after repair. Normal regression ordering is paused and the exact remembered case must be re-tested first.
- `COMPLETE` — that same case PASSed after real verified-fullscreen MesenCE observation on the repaired fingerprint. Normal regression ordering may resume.
- `BLOCKED` — the remembered evidence changed incompatibly without the expected fingerprint transition. No evidence is cleared automatically.
- `NO_ACTIVE_RECOVERY` — there is no remembered repair cycle.

## One-click resume

Run:

```text
windows\Resume_Regression_Recovery.bat
```

For `RETEST_REQUIRED`, the launcher shows the remembered route/cues, launches the repaired exact build through the existing verified-fullscreen MesenCE path, and asks for an explicit PASS/FAIL only after the operator performs that exact case in game.

A PASS records only that remembered case. It does not waive any other `STALE`, `PENDING` or `FAIL` case and cannot make Gate C pass by itself.

A remaining FAIL is rebound to the current repaired fingerprint and routed back to the correct art, capture-gap, mapping or runtime repair workflow.

## Unified Router integration

`Regression_Failure_Router.bat` synchronizes the persistent recovery state before ordinary routing. If a repaired fingerprint is waiting for same-case verification, the router refuses to move on to a different stale/pending case and transfers control to `Resume_Regression_Recovery.bat`.

## Studio integration

Authoritative Production Studio checks the local recovery state shortly after startup. An active recovery becomes the visible next action and can be resumed with:

```text
CTRL+ALT+F11
```

This startup behavior is informational and deterministic: Studio does not fabricate PASS evidence and does not auto-launch gameplay without the operator choosing the recovery action.

## ROADMAP policy

This workflow does not change Gate A-D checkboxes. It only prevents real regression evidence from being lost or bypassed across repair/restart cycles.
