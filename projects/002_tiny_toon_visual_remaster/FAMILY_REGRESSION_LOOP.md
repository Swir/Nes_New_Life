# Family Regression Loop

`windows/Family_Regression_Loop.bat` closes the production loop after a family redraw has passed transactional art QA and been launched in verified fullscreen MesenCE.

The director is intentionally evidence-first. It never records a regression PASS itself and never changes Gate A-D.

## Decision order

1. Require verified-fullscreen evidence bound to the exact runtime HD-pack fingerprint.
2. Refresh Final Regression Cockpit for that exact runtime.
3. If a FAIL exists, repair that FAIL before any PENDING/STALE case.
4. Route `CAPTURE_GAP` failures back to Capture Review Director instead of hiding them with art edits.
5. Route palette/animation/transparency/mapping failures back to the active family/art QA loop.
6. If no FAIL exists, expose the exact next PENDING/STALE gameplay regression case for real MesenCE verification.
7. Only after 10/10 PASS may `--prepare-next-family` call HD Art Autopilot and resolve the next highest-impact PLAYER/ENEMY/BOSS family.

## One-click Windows path

```text
Family_Regression_Loop.bat
```

The launcher reuses the local capture path remembered under `%LOCALAPPDATA%\Swir\TinyToonVisualRemaster\capture-session.json` when available. It writes only metadata reports under `Reports/FamilyRegressionLoop/`.

When a new family becomes ready, the launcher can open the exact family contact board plus `CurrentImpactSprint/editable`.

## Safety

The report contains no ROM bytes, save states, capture pixels, emulator binaries or absolute local paths. Local sprint PNGs/contact boards remain gitignored ROM-derived working material.

A 10/10 cockpit PASS is exact-build-specific. Any later `hires.txt` or runtime PNG change makes earlier regression evidence stale through the existing cockpit semantics.
