# Project #002 — Studio-Grade Art Pass

`studio_grade_art_pass.py` is the automatic quality-first polish stage for the exact batch selected by **Visual Completion Matrix → High-Impact Art Sprint**.

It exists to make the local sprint visually stronger before manual review, without pretending that a generic filter is final artwork.

## Quality-first workflow

The recommended art loop is now:

`Visual Completion Matrix → High-Impact Sprint → Studio-Grade Art Pass → artist review/edit → Finish Sprint + Pixel QA → verified-fullscreen MesenCE review`

`windows/High_Impact_Art_Sprint.bat` asks whether to run the Studio-Grade pass immediately after the exact high-impact batch is prepared. It can also be launched directly with:

```text
windows/Studio_Grade_Art_Pass.bat
```

## Three scored candidates per asset

For every untouched sprint master, the pass generates three deterministic local candidates:

- `refined` — restrained cleanup and clarity,
- `studio` — balanced production target,
- `bold` — stronger color/contrast/clarity option.

Candidates are scored rather than selected blindly. The scorer evaluates:

- edge-energy change,
- colorfulness change,
- channel clipping,
- mean RGB drift from the reference,
- mean luminance drift.

The target differs by art group. PLAYER/BOSS/UI favor stronger edge clarity, EFFECTS favor more color lift, while WORLD is kept more restrained to reduce over-processing.

## Group-aware visual direction

Profiles are deterministic for:

- PLAYER,
- ENEMY,
- BOSS,
- WORLD,
- UI,
- EFFECTS,
- UNASSIGNED.

The pass uses fixed global color/tone behavior rather than per-image autocontrast. This is deliberate: exact duplicates should receive identical treatment and neighboring/reused tiles should not drift because two local histograms happened to differ.

## Hard safety rules

Every selected candidate must preserve:

- exact width and height,
- exact alpha/transparency bytes,
- sprint filenames,
- High-Impact Sprint mapping relationship.

The pass never modifies `hires.txt`.

If an `editable/*.png` has already changed since sprint export, it is considered artist work and is **preserved by default**. `--force` exists for deliberate replacement but is not used by the one-click normal path.

## Local candidate storage

A/B/C candidate PNGs are kept in:

```text
Artwork/CurrentImpactSprint/quality_candidates/
```

They are local production material and may contain ROM-derived graphics. The containing `Artwork/` tree is gitignored and must never be committed.

The JSON/HTML quality report contains metrics and local filenames only; it never embeds the source/candidate image bytes.

## Not a final-art claim

Studio-Grade Art Pass is a higher-quality **automatic starting pass**. It does not mark a master as artist-approved and does not satisfy release readiness by itself.

The selected result still has to pass:

1. visual inspection / optional manual redraw,
2. stale-conflict checks on sprint import,
3. exact dimensions,
4. byte-preserved `hires.txt`,
5. Pixel QA,
6. real fullscreen MesenCE gameplay review,
7. final exact-build regression.

This keeps quality first without weakening the release gate.
