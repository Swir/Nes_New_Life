from __future__ import annotations

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

CHARACTER_GROUPS = {"PLAYER", "ENEMY", "BOSS"}


def _family_key(item: dict) -> str:
    seed_tile = str(item.get("seed_tile_id") or item.get("tile_id") or "UNKNOWN").upper()
    seed_palette = str(item.get("seed_palette") or item.get("palette") or "UNKNOWN").upper()
    return f"{item.get('group','UNASSIGNED').upper()}::{seed_tile}::{seed_palette}"


def _bbox(alpha: Image.Image):
    return alpha.getbbox()


def _centroid(alpha: Image.Image):
    bbox = alpha.getbbox()
    if not bbox:
        return None
    x0, y0, x1, y1 = bbox
    return ((x0 + x1) / 2.0, (y0 + y1) / 2.0)


def generate_family_contact_boards(items: list[dict], kit_dir: Path) -> dict:
    """Generate local-only family boards with reference/editable pairs and alignment overlays."""
    kit_dir = Path(kit_dir)
    out_dir = kit_dir / "family_boards"
    out_dir.mkdir(parents=True, exist_ok=True)
    families: dict[str, list[dict]] = {}
    for item in items:
        if str(item.get("group", "")).upper() not in CHARACTER_GROUPS:
            continue
        families.setdefault(_family_key(item), []).append(item)

    font = ImageFont.load_default()
    outputs = []
    for index, (family, members) in enumerate(sorted(families.items()), start=1):
        members = sorted(members, key=lambda row: int(row.get("priority", 0)))
        cell_w, cell_h = 340, 310
        board = Image.new("RGBA", (cell_w * len(members), cell_h), (16, 18, 24, 255))
        draw = ImageDraw.Draw(board)
        metrics = []
        for col, item in enumerate(members):
            editable_path = kit_dir / "editable" / item["kit_file"]
            reference_path = kit_dir / "reference" / item["kit_file"]
            with Image.open(editable_path) as im:
                edit = im.convert("RGBA")
            with Image.open(reference_path) as im:
                ref = im.convert("RGBA")
            canvas = Image.new("RGBA", (150, 150), (0, 0, 0, 0))
            ref_thumb = ref.copy(); ref_thumb.thumbnail((140, 140), Image.Resampling.NEAREST)
            edit_thumb = edit.copy(); edit_thumb.thumbnail((140, 140), Image.Resampling.NEAREST)
            canvas.alpha_composite(ref_thumb, ((150-ref_thumb.width)//2, (150-ref_thumb.height)//2))
            overlay = Image.new("RGBA", (150, 150), (0, 0, 0, 0))
            overlay.alpha_composite(edit_thumb, ((150-edit_thumb.width)//2, (150-edit_thumb.height)//2))
            onion = Image.blend(canvas, overlay, 0.5)
            x = col * cell_w
            board.alpha_composite(canvas, (x+10, 20))
            board.alpha_composite(overlay, (x+175, 20))
            board.alpha_composite(onion, (x+92, 175))
            draw.text((x+10, 4), f"REF  #{item['priority']}", fill=(235,235,235,255), font=font)
            draw.text((x+175, 4), "EDIT", fill=(235,235,235,255), font=font)
            draw.text((x+10, 286), f"{item['group']} {item['tile_id']} {str(item['palette'])[:8]}", fill=(160,205,255,255), font=font)
            alpha = edit.getchannel("A")
            metrics.append({"priority": item["priority"], "tile_id": item["tile_id"], "palette": item["palette"], "bbox": _bbox(alpha), "centroid": _centroid(alpha), "dimensions": list(edit.size)})
        filename = f"FAMILY_{index:03d}.png"
        board.save(out_dir / filename, optimize=True)
        outputs.append({"family": family, "file": f"family_boards/{filename}", "members": len(members), "metrics": metrics})

    manifest = {"schema": 1, "family_count": len(outputs), "families": outputs, "note": "Local-only ROM-derived production aid. Do not commit generated boards."}
    (kit_dir / "FAMILY_CONTACT_BOARDS.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
