# Visual Context & Animation Risk Audit

Project #002 now has a local metadata-only audit for the tile families most likely to produce visible HD mistakes.

The tool does **not** embed or commit captured commercial artwork. It reads the user's local MesenCE HD Pack, analyzes tile/palette/condition relationships and exact RGBA hashes, then writes only CSV/JSON/HTML metadata under the local workspace.

## Why this exists

A tile ID can appear in more than one palette, condition or captured visual form. Treating those uses as one blindly interchangeable graphic is risky: it can produce wrong palette-context art, animation seams, boss-state mistakes or a replacement that looks correct in one state and wrong in another.

`visual_context_audit.py` groups all captured uses by tile ID and assigns a risk score. Review priority rises when a family has:

- multiple palettes,
- multiple conditional contexts,
- multiple exact visual variants,
- mixed art groups,
- unresolved `UNASSIGNED` classification,
- very rare usage,
- intersecting palette + condition variation.

High-risk families require explicit local review. The review row stores a family fingerprint derived from palettes, conditions, exact visual hashes, groups and usage count. If capture/art changes later, an older `REVIEWED` decision becomes stale automatically.

## Recommended workflow

```bash
python tools/visual_context_audit.py sync \
  "C:\\TinyToonWork\\ModernizedPack\\final_art" \
  "C:\\TinyToonWork\\Artwork\\VISUAL_CONTEXT_REVIEW.csv" \
  --queue "C:\\TinyToonWork\\Artwork\\ART_QUEUE.csv"

python tools/visual_context_audit.py audit \
  "C:\\TinyToonWork\\ModernizedPack\\final_art" \
  "C:\\TinyToonWork\\Artwork\\VISUAL_CONTEXT_REVIEW.csv" \
  "C:\\TinyToonWork\\Reports\\VisualContext" \
  --queue "C:\\TinyToonWork\\Artwork\\ART_QUEUE.csv"
```

Open `Reports/VisualContext/VISUAL_CONTEXT_AUDIT.html`. Work from the highest risk score downward and verify the listed tile family in the real local MesenCE playtest.

After checking a family:

```bash
python tools/visual_context_audit.py review \
  "C:\\TinyToonWork\\Artwork\\VISUAL_CONTEXT_REVIEW.csv" \
  2E \
  --notes "Verified all palette/animation contexts in MesenCE"
```

Run the audit again. It returns `PASS` only when every currently detected high-risk family has current review evidence.

## Important boundary

This audit is not a substitute for full capture or full-game regression. It is a focused production accelerator and safety check that makes the remaining manual art review smaller and better prioritized. New capture data can create new high-risk families, and later art changes can invalidate earlier review fingerprints.
