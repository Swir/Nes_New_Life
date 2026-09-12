from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from art_production import build_tile_catalog

REVIEW_THRESHOLD = 4
FIELDS = [
    "priority",
    "tile_id",
    "uses",
    "palettes",
    "conditions",
    "visual_variants",
    "art_groups",
    "risk_score",
    "risk_reasons",
    "family_fingerprint",
    "status",
    "notes",
]


def _family_fingerprint(item: dict) -> str:
    payload = {
        "tile_id": item["tile_id"],
        "palettes": sorted(item["palettes"]),
        "conditions": sorted(item["conditions"]),
        "hashes": sorted(item["hashes"]),
        "groups": sorted(item["groups"]),
        "uses": item["uses"],
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def build_context_families(pack_dir: Path, queue: Path | None = None) -> list[dict]:
    catalog = build_tile_catalog(Path(pack_dir), Path(queue) if queue else None)
    grouped: dict[str, dict] = {}
    for tile in catalog:
        family = grouped.setdefault(
            tile["tile_id"],
            {
                "tile_id": tile["tile_id"],
                "uses": 0,
                "palettes": set(),
                "conditions": set(),
                "hashes": set(),
                "groups": set(),
            },
        )
        family["uses"] += 1
        family["palettes"].add(tile["palette"])
        if tile["condition"]:
            family["conditions"].add(tile["condition"])
        family["hashes"].add(tile["exact_hash"])
        family["groups"].add(tile["group"])

    rows: list[dict] = []
    for family in grouped.values():
        reasons: list[str] = []
        score = 0
        if len(family["palettes"]) > 1:
            score += 3
            reasons.append("multi-palette")
        if len(family["conditions"]) > 1:
            score += 3
            reasons.append("multi-condition")
        if len(family["hashes"]) > 1:
            score += 4
            reasons.append("visual-variants")
        if len(family["groups"]) > 1:
            score += 4
            reasons.append("mixed-art-groups")
        if "UNASSIGNED" in family["groups"]:
            score += 2
            reasons.append("unassigned")
        if family["uses"] <= 2:
            score += 1
            reasons.append("rare")
        if len(family["palettes"]) > 1 and len(family["conditions"]) > 1:
            score += 1
            reasons.append("palette-condition-intersection")

        item = {
            **family,
            "risk_score": score,
            "risk_reasons": reasons,
            "needs_review": score >= REVIEW_THRESHOLD,
        }
        item["family_fingerprint"] = _family_fingerprint(item)
        rows.append(item)

    return sorted(rows, key=lambda row: (-row["risk_score"], -row["uses"], row["tile_id"]))


def _read_existing(path: Path) -> dict[str, dict]:
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return {row.get("tile_id", "").upper(): row for row in csv.DictReader(handle) if row.get("tile_id")}


def sync_review(pack_dir: Path, queue: Path | None, review_path: Path) -> dict:
    families = build_context_families(pack_dir, queue)
    old = _read_existing(review_path)
    review_path.parent.mkdir(parents=True, exist_ok=True)
    pending = 0
    stale = 0
    with review_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for priority, family in enumerate(families, 1):
            previous = old.get(family["tile_id"], {})
            same_family = previous.get("family_fingerprint") == family["family_fingerprint"]
            previous_status = (previous.get("status") or "").strip().upper()
            if family["needs_review"]:
                if same_family and previous_status in {"REVIEWED", "PASS", "DONE"}:
                    status = "REVIEWED"
                else:
                    status = "REVIEW"
                    pending += 1
                    if previous_status in {"REVIEWED", "PASS", "DONE"} and not same_family:
                        stale += 1
            else:
                status = "AUTO"
            writer.writerow({
                "priority": priority,
                "tile_id": family["tile_id"],
                "uses": family["uses"],
                "palettes": " | ".join(sorted(family["palettes"])),
                "conditions": " | ".join(sorted(family["conditions"])),
                "visual_variants": len(family["hashes"]),
                "art_groups": " | ".join(sorted(family["groups"])),
                "risk_score": family["risk_score"],
                "risk_reasons": " | ".join(family["risk_reasons"]),
                "family_fingerprint": family["family_fingerprint"],
                "status": status,
                "notes": previous.get("notes", "") if same_family else "",
            })
    return {
        "families": len(families),
        "review_required": sum(1 for item in families if item["needs_review"]),
        "pending": pending,
        "stale": stale,
        "gate": "PASS" if pending == 0 else "BLOCKED",
        "review": str(review_path),
    }


def mark_reviewed(review_path: Path, tile_id: str, notes: str = "") -> dict:
    rows: list[dict] = []
    found = None
    with review_path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("tile_id", "").upper() == tile_id.upper():
                row["status"] = "REVIEWED"
                if notes:
                    row["notes"] = notes
                found = row
            rows.append(row)
    if found is None:
        raise ValueError(f"Tile family not found: {tile_id}")
    with review_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return found


def review_status(pack_dir: Path, queue: Path | None, review_path: Path) -> dict:
    if not review_path.is_file():
        return {"exists": False, "gate": "BLOCKED", "families": 0, "review_required": 0, "reviewed": 0, "pending": 0, "stale": 0}
    current = {item["tile_id"]: item for item in build_context_families(pack_dir, queue)}
    reviewed = pending = stale = required = 0
    with review_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    seen: set[str] = set()
    for row in rows:
        tile_id = (row.get("tile_id") or "").upper()
        if not tile_id or tile_id not in current:
            continue
        seen.add(tile_id)
        family = current[tile_id]
        if not family["needs_review"]:
            continue
        required += 1
        fingerprint_ok = row.get("family_fingerprint") == family["family_fingerprint"]
        status_ok = (row.get("status") or "").upper() in {"REVIEWED", "PASS", "DONE"}
        if fingerprint_ok and status_ok:
            reviewed += 1
        else:
            pending += 1
            if status_ok and not fingerprint_ok:
                stale += 1
    for tile_id, family in current.items():
        if family["needs_review"] and tile_id not in seen:
            required += 1
            pending += 1
    return {
        "exists": True,
        "gate": "PASS" if pending == 0 else "BLOCKED",
        "families": len(current),
        "review_required": required,
        "reviewed": reviewed,
        "pending": pending,
        "stale": stale,
    }


def write_dashboard(pack_dir: Path, queue: Path | None, review_path: Path, output_dir: Path) -> dict:
    sync = sync_review(pack_dir, queue, review_path)
    families = build_context_families(pack_dir, queue)
    status = review_status(pack_dir, queue, review_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "families": [
            {
                "tile_id": row["tile_id"],
                "uses": row["uses"],
                "palettes": sorted(row["palettes"]),
                "conditions": sorted(row["conditions"]),
                "visual_variants": len(row["hashes"]),
                "art_groups": sorted(row["groups"]),
                "risk_score": row["risk_score"],
                "risk_reasons": row["risk_reasons"],
                "needs_review": row["needs_review"],
            }
            for row in families
        ],
    }
    (output_dir / "VISUAL_CONTEXT_AUDIT.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    review_rows = _read_existing(review_path)
    rows_html = "".join(
        "<tr>"
        f"<td>{row['risk_score']}</td><td><code>{html.escape(row['tile_id'])}</code></td>"
        f"<td>{row['uses']}</td><td>{len(row['palettes'])}</td><td>{len(row['conditions'])}</td>"
        f"<td>{len(row['hashes'])}</td><td>{html.escape(', '.join(row['risk_reasons']))}</td>"
        f"<td>{html.escape((review_rows.get(row['tile_id'], {}).get('status') or 'MISSING'))}</td>"
        "</tr>"
        for row in families if row["needs_review"]
    ) or "<tr><td colspan='8'>No high-risk families detected.</td></tr>"
    gate_class = "pass" if status["gate"] == "PASS" else "blocked"
    document = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'>
<title>Project #002 Visual Context Audit</title><style>body{{font:15px system-ui;max-width:1200px;margin:32px auto;padding:0 22px;background:#0d1117;color:#e6edf3}}.card{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:18px;margin:14px 0}}.pass{{color:#3fb950}}.blocked{{color:#f85149}}table{{width:100%;border-collapse:collapse}}td,th{{padding:8px;border-bottom:1px solid #30363d;text-align:left}}code{{color:#79c0ff}}</style></head><body>
<h1>Tiny Toon Visual Remaster — Visual Context Audit</h1><div class='card'><h2 class='{gate_class}'>REVIEW GATE: {status['gate']}</h2><p>Families: <b>{status['families']}</b> · review required: <b>{status['review_required']}</b> · reviewed: <b>{status['reviewed']}</b> · pending: <b>{status['pending']}</b> · stale: <b>{status['stale']}</b></p><p>Review metadata only; no captured artwork is embedded in this report.</p></div><div class='card'><h2>High-risk tile families</h2><table><tr><th>Risk</th><th>Tile</th><th>Uses</th><th>Palettes</th><th>Conditions</th><th>Variants</th><th>Reasons</th><th>Status</th></tr>{rows_html}</table></div></body></html>"""
    html_path = output_dir / "VISUAL_CONTEXT_AUDIT.html"
    html_path.write_text(document, encoding="utf-8")
    return {**sync, **status, "dashboard": str(html_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 visual-context and animation-risk audit")
    commands = parser.add_subparsers(dest="command", required=True)

    sync = commands.add_parser("sync")
    sync.add_argument("pack", type=Path)
    sync.add_argument("review", type=Path)
    sync.add_argument("--queue", type=Path)

    mark = commands.add_parser("review")
    mark.add_argument("review", type=Path)
    mark.add_argument("tile_id")
    mark.add_argument("--notes", default="")

    audit = commands.add_parser("audit")
    audit.add_argument("pack", type=Path)
    audit.add_argument("review", type=Path)
    audit.add_argument("output", type=Path)
    audit.add_argument("--queue", type=Path)

    args = parser.parse_args()
    if args.command == "sync":
        print(json.dumps(sync_review(args.pack, args.queue, args.review), indent=2))
        return 0
    if args.command == "review":
        print(json.dumps(mark_reviewed(args.review, args.tile_id, args.notes), indent=2))
        return 0
    result = write_dashboard(args.pack, args.queue, args.review, args.output)
    print(json.dumps(result, indent=2))
    return 0 if result["gate"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
