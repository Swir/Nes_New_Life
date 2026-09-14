from __future__ import annotations

import argparse
import base64
import html
import io
import json
from pathlib import Path

from PIL import Image, ImageDraw

from art_production import build_tile_catalog
from regression_defect_locator import SCHEMA as LOCATOR_SCHEMA
from release_candidate import pack_fingerprint

SCHEMA = "swir.project002.regression-visual-picker.v1"


class VisualPickerError(RuntimeError):
    pass


def _load_json(path: Path) -> dict:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VisualPickerError(f"Cannot read {Path(path).name}: {exc}") from exc
    if not isinstance(data, dict):
        raise VisualPickerError(f"Expected JSON object: {Path(path).name}")
    return data


def _preview_data_uri(image: Image.Image, *, size: int = 152) -> str:
    tile = image.convert("RGBA")
    checker = Image.new("RGBA", (size, size), (32, 37, 44, 255))
    draw = ImageDraw.Draw(checker)
    cell = max(8, size // 10)
    for y in range(0, size, cell):
        for x in range(0, size, cell):
            if ((x // cell) + (y // cell)) % 2:
                draw.rectangle((x, y, min(size - 1, x + cell - 1), min(size - 1, y + cell - 1)), fill=(49, 55, 64, 255))
    max_side = max(tile.size)
    scale = max(1, (size - 20) // max(1, max_side))
    target = (max(1, tile.width * scale), max(1, tile.height * scale))
    tile = tile.resize(target, Image.Resampling.NEAREST)
    x = (size - tile.width) // 2
    y = (size - tile.height) // 2
    checker.alpha_composite(tile, (x, y))
    buffer = io.BytesIO()
    checker.save(buffer, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def build_cards(plan: dict, pack: Path, *, max_variants: int = 4) -> list[dict]:
    if plan.get("schema") != LOCATOR_SCHEMA:
        raise VisualPickerError("Unsupported regression defect locator plan schema")
    runtime = Path(pack)
    if not (runtime / "hires.txt").is_file():
        raise VisualPickerError("Runtime pack is missing hires.txt")
    current_fp = pack_fingerprint(runtime)
    if current_fp != plan.get("pack_fingerprint"):
        raise VisualPickerError("Runtime fingerprint changed since defect candidates were ranked; rebuild the locator plan.")

    index: dict[tuple[str, str], list[dict]] = {}
    for item in build_tile_catalog(runtime):
        key = (str(item.get("tile_id") or "").upper(), str(item.get("palette") or "").upper())
        if not all(key):
            continue
        index.setdefault(key, []).append(item)

    cards: list[dict] = []
    for candidate in plan.get("candidates") or []:
        key = (str(candidate.get("tile_id") or "").upper(), str(candidate.get("palette") or "").upper())
        rows = index.get(key, [])
        seen_hashes: set[str] = set()
        variants: list[dict] = []
        for row in rows:
            exact_hash = str(row.get("exact_hash") or "")
            if exact_hash and exact_hash in seen_hashes:
                continue
            if exact_hash:
                seen_hashes.add(exact_hash)
            variants.append({
                "condition": str(row.get("condition") or ""),
                "preview": _preview_data_uri(row["image"]),
            })
            if len(variants) >= max(1, int(max_variants)):
                break
        cards.append({
            "rank": int(candidate.get("rank", 0) or 0),
            "score": int(candidate.get("score", 0) or 0),
            "group": str(candidate.get("group") or "UNASSIGNED"),
            "tile_id": key[0],
            "palette": key[1],
            "uses": int(candidate.get("uses", 0) or 0),
            "family": str(candidate.get("family") or ""),
            "conditions": list(candidate.get("conditions") or []),
            "reasons": list(candidate.get("reasons") or []),
            "target_tag": str(candidate.get("target_tag") or ""),
            "variant_count": len(variants),
            "variants": variants,
        })
    return cards


def write_picker(plan: dict, pack: Path, output_dir: Path, *, max_variants: int = 4) -> dict:
    cards = build_cards(plan, pack, max_variants=max_variants)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    path = output / "REGRESSION_VISUAL_PICKER_LOCAL_ONLY.html"

    card_html = []
    for card in cards:
        variants = "".join(
            "<figure><img alt='candidate preview' src='" + variant["preview"] + "'>"
            + (f"<figcaption>{html.escape(variant['condition'] or 'default context')}</figcaption>")
            + "</figure>"
            for variant in card["variants"]
        ) or "<div class='missing'>No local crop preview available for this candidate.</div>"
        conditions = ", ".join(card["conditions"][:8]) or "—"
        reasons = ", ".join(card["reasons"]) or "—"
        family = card["family"] or "—"
        card_html.append(
            f"<button class='candidate' data-rank='{card['rank']}' onclick='pick(this)'>"
            f"<div class='rank'>#{card['rank']}</div><div class='meta'><b>{html.escape(card['group'])}</b> · score {card['score']} · uses {card['uses']}</div>"
            f"<div class='ids'>tile <code>{html.escape(card['tile_id'])}</code> · palette <code>{html.escape(card['palette'])}</code></div>"
            f"<div class='previews'>{variants}</div>"
            f"<div class='small'><b>Family:</b> {html.escape(family)}</div>"
            f"<div class='small'><b>Contexts:</b> {html.escape(conditions)}</div>"
            f"<div class='small'><b>Why ranked:</b> {html.escape(reasons)}</div>"
            f"<div class='tag'>{html.escape(card['target_tag'])}</div>"
            "</button>"
        )

    document = f"""<!doctype html>
<html lang='en'><head><meta charset='utf-8'><title>Project #002 Visual Defect Picker</title>
<style>
body{{font:15px system-ui;margin:0;background:#0d1117;color:#e6edf3}}main{{max-width:1500px;margin:24px auto;padding:0 20px 50px}}h1{{margin-bottom:6px}}.hero{{background:#161b22;border:1px solid #30363d;border-radius:16px;padding:18px;margin:14px 0 20px}}.warn{{color:#f2cc60}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:14px}}.candidate{{position:relative;text-align:left;background:#161b22;color:#e6edf3;border:1px solid #30363d;border-radius:16px;padding:16px;cursor:pointer;font:inherit}}.candidate:hover{{border-color:#58a6ff;transform:translateY(-1px)}}.candidate.selected{{outline:3px solid #3fb950;border-color:#3fb950}}.rank{{position:absolute;top:12px;right:14px;font-size:28px;font-weight:900;color:#79c0ff}}.meta{{padding-right:56px;font-size:17px}}.ids{{margin:8px 0}}code,.tag{{color:#79c0ff}}.previews{{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}}figure{{margin:0;background:#0d1117;border:1px solid #30363d;border-radius:10px;padding:6px}}figure img{{width:118px;height:118px;image-rendering:pixelated;display:block}}figcaption{{max-width:118px;font-size:11px;color:#8b949e;margin-top:4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}.small{{font-size:12px;color:#b1bac4;margin-top:5px}}.tag{{font-size:12px;margin-top:9px;word-break:break-all}}.picked{{position:sticky;bottom:12px;margin-top:18px;background:#1f6feb;color:white;border-radius:14px;padding:14px 18px;font-size:18px;font-weight:800;box-shadow:0 8px 30px #0008}}.missing{{padding:18px;color:#8b949e}}
</style></head><body><main>
<h1>Project #002 — Visual Defect Picker</h1>
<div class='hero'><p><b>Case:</b> {html.escape(str(plan.get('case_key') or ''))} · <b>category:</b> {html.escape(str(plan.get('failure_category') or ''))}</p><p><b>Exact runtime fingerprint:</b> <code>{html.escape(str(plan.get('pack_fingerprint') or ''))}</code></p><p>Click the tile/palette that matches the defect you just saw in MesenCE. The candidate number is copied to the clipboard when supported; enter/paste that number back in the PowerShell window.</p><p class='warn'><b>LOCAL-ONLY:</b> this page embeds ROM-derived HD-pack pixels for visual identification. It lives under the gitignored Reports directory and must never be committed, uploaded or used as gameplay-completion evidence.</p></div>
<div class='grid'>{''.join(card_html)}</div>
<div id='picked' class='picked'>No candidate selected yet.</div>
</main><script>
function pick(el){{
  document.querySelectorAll('.candidate').forEach(x=>x.classList.remove('selected'));
  el.classList.add('selected');
  const rank=el.dataset.rank;
  document.getElementById('picked').textContent='Selected candidate #' + rank + ' — return to PowerShell and enter/paste ' + rank;
  if(navigator.clipboard && navigator.clipboard.writeText){{navigator.clipboard.writeText(rank).catch(()=>{{}});}}
}}
</script></body></html>"""
    path.write_text(document, encoding="utf-8")
    return {
        "schema": SCHEMA,
        "picker": str(path),
        "candidate_count": len(cards),
        "contains_rom_derived_pixels": True,
        "repository_policy": "LOCAL_ONLY_GITIGNORED_REPORTS",
        "pack_fingerprint": plan.get("pack_fingerprint"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 local-only visual picker for ranked regression defect candidates")
    parser.add_argument("plan_json", type=Path)
    parser.add_argument("pack", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--variants", type=int, default=4)
    args = parser.parse_args()
    plan = _load_json(args.plan_json)
    result = write_picker(plan, args.pack, args.output, max_variants=max(1, args.variants))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
