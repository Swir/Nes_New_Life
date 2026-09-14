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

## Ranked Defect Target Locator

For art-repair categories (`MISSING_HD`, `WRONG_PALETTE`, `ANIMATION_SEAM`, `TRANSPARENCY`, `OTHER`), the Windows guided runner invokes `tools/regression_defect_locator.py` immediately after classification and before recording the FAIL.

The locator scans the **current exact HD runtime**, uses `Artwork/ART_QUEUE.csv` when available, and cross-references `Artwork/CurrentImpactSprint/ART_SPRINT_KIT.json`. It ranks tile/palette candidates using:

- the expected production group for the current regression case,
- actual tile reuse count in the supplied runtime,
- Mesen condition/context count,
- palette-variant count for palette defects,
- PLAYER/ENEMY/BOSS animation-family relevance,
- current family-aware sprint membership and priority.

The metadata plan contains up to twelve candidates with group, tile, palette, score, reuse, family and condition contexts. Selecting one writes:

```text
[SWIR_TARGET tile=<tile> palette=<palette>]
```

plus a human-readable `SWIR_CONTEXT` note into the real FAIL description. The existing Regression Repair Loop already understands `SWIR_TARGET`, so the subsequent repair sprint can jump directly to that tile/palette and expand only to its family peers instead of guessing from the whole current sprint.

Choosing `0 = unknown` is always allowed. Candidate ranking is an accelerator only; it never auto-selects a defect and never proves gameplay coverage.

The JSON/CSV locator plan and its metadata dashboard remain metadata-only.

## Local Visual Defect Picker

`tools/regression_visual_picker.py` turns the ranked locator plan into a **local-only visual board** before the operator chooses the target number.

For every ranked tile/palette candidate it finds the matching graphics in the exact same HD runtime and renders up to four distinct visual variants on transparency checkerboards. The board shows:

- candidate number,
- actual HD-pack tile preview(s),
- group / tile / palette,
- family,
- Mesen condition contexts,
- ranking reasons,
- repair-compatible `SWIR_TARGET`.

The candidate card is clickable. Clicking highlights it and attempts to copy the candidate number to the clipboard so it can be pasted back into the PowerShell prompt.

The visual board is **fingerprint-bound**. If the runtime pack changes after ranking, generation fails closed and the candidate plan must be rebuilt.

The file is generated as:

```text
Reports/RegressionDefectLocator/REGRESSION_VISUAL_PICKER_LOCAL_ONLY.html
```

Unlike the locator JSON/CSV, this HTML intentionally embeds ROM-derived HD-pack pixels so the operator can visually identify the real defect. `projects/**/Reports/` is gitignored; this local board must never be committed, uploaded or treated as gameplay-completion evidence.

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

The ranked defect locator and local visual picker are part of that same path automatically; no extra Studio button is required.

## Privacy / repository policy

The authoritative locator plan, selection JSON, regression evidence and normal dashboards remain metadata-only and contain no capture pixels or absolute local paths.

The one deliberate exception is `REGRESSION_VISUAL_PICKER_LOCAL_ONLY.html`: it embeds local ROM-derived HD-pack preview pixels solely for operator-side defect identification and is written under the already gitignored `Reports/` tree. It must never be committed or uploaded.

The workflow does not commit ROMs, save states, gameplay screenshots, capture PNG/JPG, ripped commercial art/audio, emulator binaries or local derivative HD packs.

This tooling milestone does not change Gate A-D checkboxes. Real MesenCE gameplay evidence remains mandatory.
