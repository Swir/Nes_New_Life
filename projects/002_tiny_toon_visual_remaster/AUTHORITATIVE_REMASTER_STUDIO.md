# Authoritative Remaster Studio

`tools/AuthoritativeRemasterStudio.py` is the production-facing Project #002 UI for the current HD workflow.

It exists because the older `TinyToonRemasterStudio.py` still exposes legacy Top-N / Release Candidate paths while the project has since gained stricter production gates. The authoritative Studio puts the newest path in one place without changing the original ROM-driven gameplay model.

## Production path

`capture → safe promotion → Visual Completion Matrix → exact High-Impact Art Sprint → Pixel QA → verified fullscreen MesenCE playtest → Final Regression Cockpit → Final Release Gate`

The Studio can:

- launch regression-safe capture promotion,
- run Visual Completion Matrix directly against the selected local workspace and HD pack,
- export the exact `NEXT_HIGH_IMPACT_ART_BATCH` into `Artwork/CurrentImpactSprint`,
- open the editable sprint and local board,
- launch the stale-conflict-safe finish + Pixel QA flow,
- launch the verified-fullscreen one-click MesenCE playtest,
- launch the exact-build Final Regression Cockpit,
- run the seven-gate Final Release Readiness audit,
- launch gated release packaging only through the existing Final Release Gate.

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

## Windows launch

Run:

```text
windows/Authoritative_Remaster_Studio.bat
```

The Studio does not bundle MesenCE, a ROM, save states or game-derived art. All capture, editable sprint PNGs and evidence remain in the user's local workspace.

## Roadmap semantics

The Visual Completion Matrix percentage shown in Studio is **capture-bounded art progress only**. It never changes the repository ROADMAP percentage.

`projects/002_tiny_toon_visual_remaster/ROADMAP.md` remains authoritative and its progress is calculated only from Gate A–D checkboxes. The Master Roadmap mirrors that exact release percentage. Tooling milestones do not count as completed release gates without real local capture/art/QA evidence.
