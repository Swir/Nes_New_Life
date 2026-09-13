# Authoritative Remaster Studio

`tools/AuthoritativeRemasterStudio.py` is the production-facing Project #002 UI for the current HD workflow.

It exists because the older `TinyToonRemasterStudio.py` still exposes legacy Top-N / Release Candidate paths while the project has since gained stricter production gates. The authoritative Studio puts the newest path in one place without changing the original ROM-driven gameplay model.

## Production path

`capture → safe promotion → Visual Completion Matrix → family-aware High-Impact Art Sprint → active family workbench → transactional visual/family/Pixel QA → verified fullscreen MesenCE playtest → Final Regression Cockpit → Final Release Gate`

The Studio can:

- launch regression-safe capture promotion,
- run Visual Completion Matrix directly against the selected local workspace and HD pack,
- export the exact `NEXT_HIGH_IMPACT_ART_BATCH` into `Artwork/CurrentImpactSprint`,
- resolve the highest-priority PLAYER/ENEMY/BOSS family from the current family-aware sprint,
- open that family's generated reference/edit/onion contact board and the exact editable sprint folder together,
- write metadata-only `ACTIVE_FAMILY_WORKBENCH.json` so the current local production target is explicit without storing pixels or absolute paths,
- finish the current family through transactional master visual QA, animation-family consistency QA, `hires.txt` preservation and Pixel QA,
- launch verified-fullscreen MesenCE only after the art transaction succeeds,
- launch the exact-build Final Regression Cockpit,
- run the seven-gate Final Release Readiness audit,
- launch gated release packaging only through the existing Final Release Gate.

## Active family workbench

`CTRL+F10` opens the current highest-priority character-family board and `Artwork/CurrentImpactSprint/editable` together. The resolver accepts only relative workbench paths and refuses missing/unsafe board references.

When the redraw is ready, `CTRL+F11` launches `windows/Finish_Family_And_Playtest.bat`. The launcher performs the transactional High-Impact Art Sprint finish first. If visual QA, animation-family QA, mapping preservation, Pixel QA or stale-workspace protection blocks the transaction, the fullscreen playtest is not started. Only a successful art finish proceeds to the existing QA-gated MesenCE deployment/fullscreen path.

This is intentionally a production accelerator, not ROADMAP evidence. A successful tool run cannot check Gate A-D by itself.

## Keyboard shortcuts

- `F1` workspace
- `F2` accepted MesenCE capture
- `F3` current candidate/final HD pack
- `F5` safe capture promotion
- `F6` Visual Completion Matrix
- `F7` prepare exact High-Impact Art Sprint
- `F8` finish sprint + Pixel QA
- `F9` verified fullscreen playtest
- `F10` Final Regression Cockpit
- `F11` Final Release Gate
- `CTRL+F6` full Capture → HD Autopilot
- `CTRL+F7` continue QA-gated art session
- `CTRL+F8` refresh Production Cockpit
- `CTRL+F9` ROADMAP Evidence Readiness
- `CTRL+F10` open active family workbench
- `CTRL+F11` commit family + QA + verified fullscreen playtest

## Windows launch

Run:

```text
windows/Authoritative_Remaster_Studio.bat
```

The Studio does not bundle MesenCE, a ROM, save states or game-derived art. All capture, editable sprint PNGs and generated family boards remain in the user's local workspace.

## Roadmap semantics

The Visual Completion Matrix percentage shown in Studio is **capture-bounded art progress only**. It never changes the repository ROADMAP percentage.

`projects/002_tiny_toon_visual_remaster/ROADMAP.md` remains authoritative and its progress is calculated only from Gate A-D checkboxes. The Master Roadmap mirrors that exact release percentage. Tooling milestones do not count as completed release gates without real local capture/art/QA evidence.
