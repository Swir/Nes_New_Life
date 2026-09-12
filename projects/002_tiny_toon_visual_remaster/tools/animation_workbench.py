from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from art_production import build_tile_catalog

ACTION_TOKENS = {
    "idle", "walk", "walking", "run", "running", "jump", "fall", "falling", "land", "landing",
    "crouch", "duck", "attack", "attacking", "shoot", "throw", "kick", "hit", "hurt", "damage",
    "invulnerable", "death", "dead", "die", "intro", "phase", "spawn", "appear", "disappear",
    "open", "close", "opening", "closing", "projectile", "effect", "transition", "frame", "anim",
}
FRAME_TOKEN_RE = re.compile(r"^(?:f|frame|frm|phase|p)?\d+$", re.I)
SPLIT_RE = re.compile(r"[^a-zA-Z0-9]+")
REVIEW_FIELDS = [
    "priority", "family", "uses", "conditions", "tile_ids", "palettes", "visual_variants", "art_groups",
    "candidate_states", "risk_score", "risk_reasons", "family_fingerprint", "status", "notes",
]


def _tokens(condition: str) -> list[str]:
    return [token.lower() for token in SPLIT_RE.split(condition or "") if token]


def semantic_family(condition: str) -> str:
    """Best-effort semantic family key from a Mesen condition name.

    This is deliberately heuristic. It never changes mappings and never claims
    that sheet coordinates represent on-screen sprite layout.
    """
    tokens = _tokens(condition)
    if not tokens:
        return "UNCONDITIONED"
    kept: list[str] = []
    for token in tokens:
        if token in ACTION_TOKENS or FRAME_TOKEN_RE.match(token):
            continue
        kept.append(token)
    if not kept:
        return tokens[0]
    return "_".join(kept[:4]).upper()


def _fingerprint(family: dict) -> str:
    payload = {
        "family": family["family"],
        "conditions": sorted(family["conditions"]),
        "tile_ids": sorted(family["tile_ids"]),
        "palettes": sorted(family["palettes"]),
        "hashes": sorted(family["hashes"]),
        "groups": sorted(family["groups"]),
        "states": sorted(family["states"]),
        "uses": family["uses"],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def build_animation_families(pack_dir: Path, queue: Path | None = None) -> list[dict]:
    catalog = build_tile_catalog(Path(pack_dir), Path(queue) if queue else None)
    grouped: dict[str, dict] = {}
    for tile in catalog:
        condition = tile["condition"] or ""
        key = semantic_family(condition)
        family = grouped.setdefault(key, {
            "family": key,
            "uses": 0,
            "conditions": set(),
            "tile_ids": set(),
            "palettes": set(),
            "hashes": set(),
            "groups": set(),
            "states": set(),
            "tiles": [],
        })
        family["uses"] += 1
        if condition:
            family["conditions"].add(condition)
            action = [t for t in _tokens(condition) if t in ACTION_TOKENS or FRAME_TOKEN_RE.match(t)]
            if action:
                family["states"].add("_".join(action))
        family["tile_ids"].add(tile["tile_id"])
        family["palettes"].add(tile["palette"])
        family["hashes"].add(tile["exact_hash"])
        family["groups"].add(tile["group"])
        family["tiles"].append(tile)

    rows: list[dict] = []
    for family in grouped.values():
        reasons: list[str] = []
        score = 0
        if len(family["conditions"]) >= 2:
            score += 2
            reasons.append("multi-state")
        if len(family["hashes"]) >= 3:
            score += 3
            reasons.append("many-visual-frames")
        if len(family["palettes"]) > 1:
            score += 2
            reasons.append("multi-palette")
        if len(family["tile_ids"]) >= 4:
            score += 2
            reasons.append("multi-tile-object")
        if len(family["groups"]) > 1:
            score += 3
            reasons.append("mixed-art-groups")
        if "UNASSIGNED" in family["groups"]:
            score += 2
            reasons.append("unassigned")
        if len(family["states"]) >= 3:
            score += 2
            reasons.append("animation-sequence")
        family["risk_score"] = score
        family["risk_reasons"] = reasons
        family["needs_review"] = score >= 4 and family["family"] != "UNCONDITIONED"
        family["family_fingerprint"] = _fingerprint(family)
        rows.append(family)
    return sorted(rows, key=lambda item: (-item["risk_score"], -item["uses"], item["family"]))


def build_condition_candidates(pack_dir: Path, queue: Path | None = None) -> list[dict]:
    """Build metadata-only sprite/metatile candidates from condition co-occurrence.

    Coordinates inside Mesen texture sheets are NOT treated as screen geometry.
    A candidate only means the listed tile mappings share a condition/group and
    should be inspected together in the running game.
    """
    catalog = build_tile_catalog(Path(pack_dir), Path(queue) if queue else None)
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for tile in catalog:
        condition = tile["condition"] or "UNCONDITIONED"
        groups[(condition, tile["group"])].append(tile)
    candidates = []
    for (condition, art_group), tiles in groups.items():
        ids = sorted({tile["tile_id"] for tile in tiles})
        variants = sorted({tile["exact_hash"] for tile in tiles})
        candidates.append({
            "condition": condition,
            "family": semantic_family("" if condition == "UNCONDITIONED" else condition),
            "art_group": art_group,
            "uses": len(tiles),
            "tile_ids": ids,
            "palettes": sorted({tile["palette"] for tile in tiles}),
            "visual_variants": len(variants),
            "candidate_type": "condition-cooccurrence",
            "requires_ingame_layout_verification": True,
        })
    return sorted(candidates, key=lambda item: (-len(item["tile_ids"]), -item["uses"], item["condition"], item["art_group"]))


def _load_review(path: Path) -> dict[str, dict]:
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return {row["family"]: row for row in csv.DictReader(handle) if row.get("family")}


def sync_review(pack_dir: Path, queue: Path | None, review_path: Path) -> dict:
    families = build_animation_families(pack_dir, queue)
    previous = _load_review(review_path)
    review_path.parent.mkdir(parents=True, exist_ok=True)
    pending = stale = 0
    with review_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        for priority, family in enumerate(families, 1):
            old = previous.get(family["family"], {})
            same = old.get("family_fingerprint") == family["family_fingerprint"]
            old_status = (old.get("status") or "").upper()
            if family["needs_review"]:
                if same and old_status in {"REVIEWED", "PASS", "DONE"}:
                    status = "REVIEWED"
                else:
                    status = "REVIEW"
                    pending += 1
                    if old_status in {"REVIEWED", "PASS", "DONE"} and not same:
                        stale += 1
            else:
                status = "AUTO"
            writer.writerow({
                "priority": priority,
                "family": family["family"],
                "uses": family["uses"],
                "conditions": " | ".join(sorted(family["conditions"])),
                "tile_ids": " | ".join(sorted(family["tile_ids"])),
                "palettes": " | ".join(sorted(family["palettes"])),
                "visual_variants": len(family["hashes"]),
                "art_groups": " | ".join(sorted(family["groups"])),
                "candidate_states": " | ".join(sorted(family["states"])),
                "risk_score": family["risk_score"],
                "risk_reasons": " | ".join(family["risk_reasons"]),
                "family_fingerprint": family["family_fingerprint"],
                "status": status,
                "notes": old.get("notes", "") if same else "",
            })
    return {
        "families": len(families),
        "review_required": sum(1 for family in families if family["needs_review"]),
        "pending": pending,
        "stale": stale,
        "gate": "PASS" if pending == 0 else "BLOCKED",
        "review": str(review_path),
    }


def mark_reviewed(review_path: Path, family_name: str, notes: str = "") -> dict:
    with review_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    found = None
    for row in rows:
        if row.get("family", "").upper() == family_name.upper():
            row["status"] = "REVIEWED"
            if notes:
                row["notes"] = notes
            found = row
    if found is None:
        raise ValueError(f"Animation family not found: {family_name}")
    with review_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return found


def review_status(pack_dir: Path, queue: Path | None, review_path: Path) -> dict:
    if not review_path.is_file():
        return {"exists": False, "gate": "BLOCKED", "families": 0, "review_required": 0, "reviewed": 0, "pending": 0, "stale": 0}
    current = {family["family"]: family for family in build_animation_families(pack_dir, queue)}
    stored = _load_review(review_path)
    required = reviewed = pending = stale = 0
    for name, family in current.items():
        if not family["needs_review"]:
            continue
        required += 1
        row = stored.get(name)
        if not row:
            pending += 1
            continue
        fingerprint_ok = row.get("family_fingerprint") == family["family_fingerprint"]
        status_ok = (row.get("status") or "").upper() in {"REVIEWED", "PASS", "DONE"}
        if fingerprint_ok and status_ok:
            reviewed += 1
        else:
            pending += 1
            if status_ok and not fingerprint_ok:
                stale += 1
    return {
        "exists": True,
        "gate": "PASS" if pending == 0 else "BLOCKED",
        "families": len(current),
        "review_required": required,
        "reviewed": reviewed,
        "pending": pending,
        "stale": stale,
    }


def write_contact_sheets(pack_dir: Path, queue: Path | None, output_dir: Path, columns: int = 8) -> dict:
    """Create local-only visual boards. Never intended for repository commits."""
    families = build_animation_families(pack_dir, queue)
    output_dir.mkdir(parents=True, exist_ok=True)
    created = []
    for family in families:
        if family["family"] == "UNCONDITIONED" or len(family["tiles"]) < 2:
            continue
        tile_size = 96
        label_height = 44
        rows = (len(family["tiles"]) + columns - 1) // columns
        board = Image.new("RGBA", (columns * tile_size, rows * (tile_size + label_height)), (20, 24, 30, 255))
        draw = ImageDraw.Draw(board)
        font = ImageFont.load_default()
        for index, tile in enumerate(family["tiles"]):
            col, row = index % columns, index // columns
            x, y = col * tile_size, row * (tile_size + label_height)
            thumb = tile["image"].copy()
            thumb.thumbnail((80, 80), Image.Resampling.NEAREST)
            board.alpha_composite(thumb, (x + (tile_size - thumb.width) // 2, y + (tile_size - thumb.height) // 2))
            draw.text((x + 4, y + tile_size + 2), f"{tile['tile_id']} {tile['palette'][:6]}", fill=(235, 240, 245, 255), font=font)
            draw.text((x + 4, y + tile_size + 17), (tile["condition"] or "-")[:18], fill=(150, 190, 220, 255), font=font)
        safe = re.sub(r"[^A-Z0-9_-]+", "_", family["family"].upper())[:64]
        path = output_dir / f"ANIM_{safe}.png"
        board.save(path, optimize=True)
        created.append(path.name)
    manifest = {
        "warning": "Local ROM-derived visual boards. Keep them out of git and release packages.",
        "created": created,
    }
    (output_dir / "ANIMATION_CONTACT_SHEETS.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def write_dashboard(pack_dir: Path, queue: Path | None, review_path: Path, output_dir: Path) -> dict:
    sync = sync_review(pack_dir, queue, review_path)
    families = build_animation_families(pack_dir, queue)
    candidates = build_condition_candidates(pack_dir, queue)
    status = review_status(pack_dir, queue, review_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "families": [{
            "family": f["family"], "uses": f["uses"], "conditions": sorted(f["conditions"]),
            "tile_ids": sorted(f["tile_ids"]), "palettes": sorted(f["palettes"]),
            "visual_variants": len(f["hashes"]), "art_groups": sorted(f["groups"]),
            "candidate_states": sorted(f["states"]), "risk_score": f["risk_score"],
            "risk_reasons": f["risk_reasons"], "needs_review": f["needs_review"],
        } for f in families],
        "assembly_candidates": candidates,
        "important_note": "Assembly candidates are condition co-occurrence hints, not reconstructed screen geometry.",
    }
    (output_dir / "ANIMATION_WORKBENCH.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    rows = "".join(
        "<tr>" +
        f"<td>{f['risk_score']}</td><td><code>{html.escape(f['family'])}</code></td><td>{f['uses']}</td>" +
        f"<td>{len(f['conditions'])}</td><td>{len(f['tile_ids'])}</td><td>{len(f['hashes'])}</td>" +
        f"<td>{html.escape(', '.join(f['risk_reasons']))}</td></tr>"
        for f in families if f["needs_review"]
    ) or "<tr><td colspan='7'>No high-risk semantic animation families detected.</td></tr>"
    gate_class = "pass" if status["gate"] == "PASS" else "blocked"
    document = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><title>Animation Family Workbench</title>
<style>body{{font:15px system-ui;max-width:1200px;margin:32px auto;padding:0 22px;background:#0d1117;color:#e6edf3}}.card{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:18px;margin:14px 0}}.pass{{color:#3fb950}}.blocked{{color:#f85149}}table{{width:100%;border-collapse:collapse}}td,th{{padding:8px;border-bottom:1px solid #30363d;text-align:left}}code{{color:#79c0ff}}</style></head><body>
<h1>Tiny Toon Visual Remaster — Animation Family Workbench</h1><div class='card'><h2 class='{gate_class}'>ANIMATION REVIEW: {status['gate']}</h2><p>Families: <b>{status['families']}</b> · review required: <b>{status['review_required']}</b> · reviewed: <b>{status['reviewed']}</b> · pending: <b>{status['pending']}</b> · stale: <b>{status['stale']}</b></p><p>Condition-cooccurrence candidates are review hints only; texture-sheet coordinates are never treated as on-screen sprite geometry.</p></div><div class='card'><h2>High-risk animation families</h2><table><tr><th>Risk</th><th>Family</th><th>Uses</th><th>Conditions</th><th>Tiles</th><th>Variants</th><th>Reasons</th></tr>{rows}</table></div></body></html>"""
    dashboard = output_dir / "ANIMATION_WORKBENCH.html"
    dashboard.write_text(document, encoding="utf-8")
    return {**sync, **status, "assembly_candidates": len(candidates), "dashboard": str(dashboard)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 animation-family and sprite/metatile review workbench")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("dashboard", "contact-sheets"):
        cmd = sub.add_parser(name)
        cmd.add_argument("pack", type=Path)
        cmd.add_argument("--queue", type=Path)
        cmd.add_argument("--output", type=Path, required=True)
        if name == "dashboard":
            cmd.add_argument("--review", type=Path, required=True)
    mark = sub.add_parser("mark-reviewed")
    mark.add_argument("review", type=Path)
    mark.add_argument("family")
    mark.add_argument("--notes", default="")
    args = parser.parse_args()
    if args.command == "dashboard":
        print(json.dumps(write_dashboard(args.pack, args.queue, args.review, args.output), indent=2))
        return 0
    if args.command == "contact-sheets":
        print(json.dumps(write_contact_sheets(args.pack, args.queue, args.output), indent=2))
        return 0
    print(json.dumps(mark_reviewed(args.review, args.family, args.notes), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
