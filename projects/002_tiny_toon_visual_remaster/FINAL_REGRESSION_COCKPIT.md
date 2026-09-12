# Final Regression Cockpit

Project #002 keeps the original ROM as the authoritative gameplay source. The final visual regression therefore has to be performed in the real game, in MesenCE, against the exact HD Pack that may later be released.

`tools/final_regression_cockpit.py` and `tools/FinalRegressionCockpit.py` turn that manual verification into a fingerprint-bound production gate instead of a loose checklist.

## What it tracks

The cockpit uses the ten authoritative full-game regression scopes already required by `release_candidate.py`: boot/title/menu, player movement, actions/damage/death, primary route, alternate routes/secrets, enemies, bosses, HUD/text/status, effects/transitions and ending/credits.

Each test result is bound to the SHA-256 runtime fingerprint derived from `hires.txt` plus every referenced HD PNG.

States are:

- `PASS` — manually verified in MesenCE on the current exact fingerprint.
- `FAIL` — a visible problem was found on the current fingerprint and must be fixed/retested.
- `STALE` — evidence belongs to an older runtime fingerprint.
- `PENDING` — not yet verified.

A runtime PNG or `hires.txt` change automatically turns older current-build evidence into `STALE`; old evidence cannot silently authorize a newer pack.

## Failure triage

FAIL results can be classified as:

`MISSING_HD`, `WRONG_PALETTE`, `ANIMATION_SEAM`, `TRANSPARENCY`, `MAPPING`, `SCALE_OR_FILTER`, `CAPTURE_GAP`, or `OTHER`.

The failure stays in `FINAL_REGRESSION.json` history. Re-testing the same case to PASS clears the active blocker while preserving the history entry for diagnosis.

## Windows one-click GUI

Double-click:

```text
windows/Final_Regression_Cockpit.bat
```

Then select the local Project #002 workspace and the exact runtime HD Pack. **Test NEXT case** always selects a failing case first, then pending/stale work. The GUI never auto-passes a test.

The dashboard is written to:

```text
Reports/FinalRegressionCockpit/FINAL_REGRESSION_COCKPIT.html
```

It is metadata-only and does not copy capture PNGs into the report.

## CLI

```bash
python tools/final_regression_cockpit.py status \
  "C:\\TinyToonWork\\FINAL_REGRESSION.json" \
  "C:\\TinyToonWork\\ModernizedPack\\final_art" \
  --output "C:\\TinyToonWork\\Reports\\FinalRegressionCockpit"

python tools/final_regression_cockpit.py pass \
  "C:\\TinyToonWork\\FINAL_REGRESSION.json" boot_title_menu \
  "C:\\TinyToonWork\\ModernizedPack\\final_art" \
  --notes "Boot/menu verified in MesenCE"

python tools/final_regression_cockpit.py fail \
  "C:\\TinyToonWork\\FINAL_REGRESSION.json" player_movement \
  "C:\\TinyToonWork\\ModernizedPack\\final_art" \
  --category ANIMATION_SEAM \
  --failure-notes "Landing transition has a visible seam"
```

## Release boundary

The cockpit accelerates real testing; it cannot replace it. Full capture, final artwork and a complete in-game MesenCE regression are still required. `release_candidate.py` remains the final authority and will only PASS after all ten cases have current-build PASS evidence together with the capture/art/review/Pixel-QA gates.

No ROM, save state, Mesen capture, emulator binary, ripped commercial asset or derivative final pack belongs in the repository.
