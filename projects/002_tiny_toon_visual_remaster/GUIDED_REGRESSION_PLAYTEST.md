# Guided Exact-Build Regression Playtest

`windows/Guided_Regression_Playtest.bat` turns the ten authoritative Final Regression Cockpit cases into a case-by-case verified-fullscreen gameplay workflow.

The goal is to reduce Gate C manual bookkeeping without weakening evidence. The launcher never auto-passes gameplay. It selects the authoritative next case, launches the exact current HD runtime in verified-fullscreen MesenCE, shows targeted gameplay cues, then requires an explicit local PASS or FAIL after real visual observation.

## Ordering

The existing Final Regression Cockpit remains authoritative. Its ordering is preserved:

1. any current-build `FAIL` is handled before ordinary pending work;
2. otherwise the first `PENDING` or `STALE` case is selected;
3. only 10/10 current-fingerprint PASS advances to Final Release Gate.

A runtime PNG or `hires.txt` change changes the pack fingerprint and therefore makes old PASS evidence stale exactly as before.

## Ten guided cases

The director contains concrete routes and visual cues for:

- boot/title/menu,
- player movement,
- actions/damage/death,
- primary world route,
- alternate routes/secrets/revisits,
- enemies,
- bosses,
- HUD/text/status/result,
- effects/transitions,
- ending/credits/post-game.

The cues are review instructions only. They do not claim an unseen state exists and never manufacture gameplay evidence.

## FAIL routing

After a real observed failure, choose one existing Final Regression Cockpit defect category:

- `MISSING_HD` — return to capture/art coverage;
- `WRONG_PALETTE` — Visual Context / affected family repair;
- `ANIMATION_SEAM` — family sequence redraw and transactional QA;
- `TRANSPARENCY` — alpha/canvas repair followed by Pixel QA;
- `MAPPING` — repair mapping provenance rather than hiding it in artwork;
- `SCALE_OR_FILTER` — restore required 4x/fullscreen runtime presentation;
- `CAPTURE_GAP` — return to Capture Review Director / Guided Capture Marathon for real gameplay evidence;
- `OTHER` — isolate, document and repair before re-testing.

A known FAIL is never silently skipped to reach later cases.

## Exact-build safety

The Python director plans against the current `hires.txt + referenced runtime PNG` fingerprint. Recording refuses if the runtime fingerprint changed between planning and result recording. It also refuses out-of-order evidence: only the cockpit's exact current `next_case` may be recorded.

The Windows launcher invokes `launch_remaster.ps1 -PackDir <runtime> -EvidencePath <fullscreen evidence>` before each case, so a failed verified-fullscreen launch records no regression result.

## One case or marathon

Default mode performs one authoritative case and stops with the next case prepared. Use:

```text
Guided_Regression_Playtest.bat -RunAll
```

to continue PASSed cases in sequence during one local session. Any FAIL stops immediately and prints the exact repair route.

## Studio

Authoritative Production Studio exposes the workflow as:

```text
CTRL+SHIFT+F10  GUIDED EXACT-BUILD REGRESSION
```

## Privacy / repository policy

Generated JSON/HTML reports are metadata-only. The workflow does not commit ROMs, save states, gameplay screenshots, capture PNG/JPG, ripped commercial art/audio, emulator binaries or local derivative HD packs.

This tooling milestone does not change Gate A-D checkboxes. Real MesenCE gameplay evidence remains mandatory.
