# Regression CAPTURE_GAP Recovery Loop

`windows/Regression_Capture_Gap_Recovery.bat` closes the missing-content branch of Final Regression Cockpit.

It is used only when the authoritative current-build regression case is already recorded as `FAIL / CAPTURE_GAP`. The original local ROM remains the only source of gameplay, level progression, timing, physics and hidden/rare states.

## Flow

```text
exact-build regression FAIL / CAPTURE_GAP
→ bind failed case + runtime fingerprint + source capture fingerprint
→ map the regression case to authoritative Capture Mission Control mission(s)
→ build current Capture Gap Planner + Route Capture Sequencer
→ show the highest-affinity gameplay pass
→ run the existing verified-fullscreen Guided Capture Marathon
→ require explicit VERIFIED_IN_GAME for the target mission(s)
→ reject unchanged/stale/regressed capture evidence
→ evidence-bound HD art handoff
→ prepare the exact new/affected 4x art work
→ transactional visual/family/Pixel QA
→ re-run the SAME failed regression case
```

The loop never turns capture recovery into a regression PASS. After capture recovery, the failed case remains failed until the refreshed capture has been promoted into production, the affected 4x art has been completed, and the same regression case has been visually re-tested in verified-fullscreen MesenCE against the repaired runtime fingerprint.

## Exact case → capture mission targeting

The director maps the ten authoritative regression cases to the existing Capture Mission Control model. Examples:

- `player_movement` → `player_idle_walk_run`
- `player_actions_damage_death` → `player_actions_damage_death`
- `world_route_1` → `world_route_1` + `common_enemies`
- `world_route_2` → `world_route_2` + `rare_enemies`
- `enemies` → common + rare enemy missions
- `bosses` → `bosses_all_phases`
- `effects_transitions` → `effects_transitions`
- `ending_credits` → `ending_credits`

The Route Capture Sequencer is then used to choose the best existing bundled gameplay pass. This reduces restarts without inventing level names or claiming unseen game states.

## Fail-closed verification

After Guided Capture Marathon returns, recovery is accepted only when:

- the capture fingerprint changed from the capture that produced the original gap;
- Capture Integrity admission is `PASS`;
- there is no `CAPTURE_REGRESSION`;
- there are no structural capture blockers;
- every target mission exists in current acceptance evidence;
- every target mission is `VERIFIED_IN_GAME`;
- target mission provenance is bound to the refreshed capture fingerprint.

If any requirement fails, HD art handoff is not started.

## Production handoff

A verified refreshed capture is sent directly to the existing `Evidence_Bound_Art_Handoff.ps1` path. That means the recovery still uses the authoritative production stack:

```text
Capture Review
→ acceptance-gated promotion
→ resume-safe MasterWorkspace sync
→ Visual Context Audit
→ Animation Family Workbench
→ Visual Completion Matrix
→ family-aware High-Impact Art Sprint
→ transactional QA
```

This is important because a capture gap can reveal new tile/palette/context data, but those pixels still need a real 4x art pass before the original regression failure can be cleared.

## Privacy and repository policy

`REGRESSION_CAPTURE_GAP_TOKEN.json` and the HTML/JSON recovery reports are metadata-only. They contain fingerprints, regression case keys, mission keys, counts and route metadata only.

The workflow never commits or uploads:

- ROM bytes,
- save states,
- MesenCE capture PNG/JPG,
- gameplay screenshots,
- ripped commercial art/audio,
- emulator binaries,
- local derivative HD packs.

## ROADMAP policy

This milestone does not change Gate A-D checkboxes. A successful recovery only means the failed capture gap is ready to re-enter the normal HD production path. Final Gate C still requires the same regression case—and ultimately all ten cases—to PASS through real local MesenCE verification on the final exact runtime fingerprint.
