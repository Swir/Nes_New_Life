# Project #002 — Unified Release Candidate Gate

Project #002 now has one authoritative final gate instead of several partially overlapping readiness indicators.

The gate is deliberately strict. A structurally valid HD Pack is **not** enough, and a successful capture session is **not** enough. `RELEASE GATE: PASS` means all required evidence belongs to the exact current runtime build.

## What must pass

1. **HD Pack structure**
   - `validate_hdpack.py` has no structural errors.
   - every referenced PNG exists.
   - the Project #002 target remains 4x or greater.

2. **Capture Mission Control**
   - every explicit capture mission is manually verified.
   - tile counts alone never auto-complete a mission.
   - required scope includes menus, all player states, normal/alternate routes, enemies, bosses, HUD/text, effects and ending/credits.

3. **Art queue**
   - the queue exists and is non-empty.
   - every row is finished.
   - zero rows remain `UNASSIGNED`.

4. **Build-bound pixel Art QA**
   - pixel QA must be `PASS`.
   - its `output_pack_fingerprint` must match the exact current HD Pack.
   - changing `hires.txt` or any referenced runtime PNG makes old QA evidence stale automatically.

5. **Build-bound full-game visual regression**
   - ten final playtest cases cover boot/menu, movement, actions/damage/death, both route passes, enemies, bosses, HUD/text, effects/transitions and ending/credits.
   - every completed case stores the exact pack fingerprint.
   - changing runtime graphics or mappings invalidates old regression evidence automatically.

## Runtime fingerprint

The fingerprint is SHA-256 evidence derived from:

- `hires.txt`, and
- every PNG referenced by `<img>` in `hires.txt`.

Generated reports and production metadata do not affect it. This means the fingerprint identifies the playable HD assets rather than the tooling workspace.

## Final workflow

```text
full MesenCE capture
  -> Capture Mission Control PASS
  -> final art queue: 0 TODO / 0 UNASSIGNED
  -> batch apply
  -> build-bound pixel QA PASS
  -> final full-game regression on that exact build
  -> Unified Release Candidate Gate PASS
  -> safe release ZIP
```

## Commands

Initialize final regression evidence:

```powershell
python tools/release_candidate.py init-regression D:\TinyToonHD\FINAL_REGRESSION.json
```

Run build-bound pixel QA for the final pack:

```powershell
python tools/bound_art_qa.py `
  D:\TinyToonHD\Capture `
  D:\TinyToonHD\ModernizedPack\playtest_current `
  D:\TinyToonHD\Artwork\MasterWorkspace `
  D:\TinyToonHD\Artwork\MasterWorkspace\qa_release
```

After visually verifying one final regression case in MesenCE, bind that evidence to the current build:

```powershell
python tools/release_candidate.py complete-regression `
  D:\TinyToonHD\FINAL_REGRESSION.json `
  bosses `
  D:\TinyToonHD\ModernizedPack\playtest_current `
  --notes "All boss phases checked in MesenCE"
```

Audit the complete release candidate:

```powershell
python tools/release_candidate.py audit `
  D:\TinyToonHD\ModernizedPack\playtest_current `
  --capture D:\TinyToonHD\CAPTURE_MISSIONS.json `
  --queue D:\TinyToonHD\Artwork\ART_QUEUE.csv `
  --art-qa D:\TinyToonHD\Artwork\MasterWorkspace\qa_release `
  --regression D:\TinyToonHD\FINAL_REGRESSION.json `
  --output D:\TinyToonHD\Reports\ReleaseCandidate
```

Package only after all gates pass:

```powershell
python tools/release_candidate.py package `
  D:\TinyToonHD\ModernizedPack\playtest_current `
  --capture D:\TinyToonHD\CAPTURE_MISSIONS.json `
  --queue D:\TinyToonHD\Artwork\ART_QUEUE.csv `
  --art-qa D:\TinyToonHD\Artwork\MasterWorkspace\qa_release `
  --regression D:\TinyToonHD\FINAL_REGRESSION.json `
  --output D:\TinyToonHD\Reports\ReleaseCandidate `
  --zip D:\TinyToonHD\Release\TinyToon_HD_Pack.zip
```

The package command exits with code 2 while any gate is blocked and does **not** create a release ZIP.

## Why stale evidence is blocked

A common remaster failure mode is:

1. finish a regression pass,
2. make a late art fix,
3. accidentally ship without retesting that changed build.

Project #002 now prevents this mechanically. A runtime asset change creates a new fingerprint. Previous pixel-QA and regression evidence no longer matches, so the release gate returns `BLOCKED` until the new build is checked.

## Copyright/safety boundary

The repository still contains no ROM, save state, Mesen-derived capture sheet, commercial art/audio, emulator binary or final derivative pack. All real capture, final art and playtest evidence remains local to the user. CI uses only synthetic graphics.
