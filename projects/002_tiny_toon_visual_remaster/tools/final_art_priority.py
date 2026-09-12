from __future__ import annotations

import argparse
import csv
import html
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from animation_workbench import build_animation_families, semantic_family
from art_production import build_tile_catalog
from visual_context_audit import build_context_families

GROUP_WEIGHT = {
    "PLAYER": 40,
    "BOSS": 36,
    "ENEMY": 28,
    "UI": 20,
    "EFFECTS": 18,
    "WORLD": 14,
    "UNASSIGNED": 24,
}


def _read_csv(path: Path | None) -> list[dict]:
    if path is None or not path.is_file():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _master_state(workspace: Path | None) -> dict[tuple[str, str], dict]:
    if workspace is None:
        return {}
    rows = _read_csv(workspace / "ART_STATE.csv")
    return {
        ((row.get("tile_id") or "").upper(), (row.get("palette") or "").upper()): row
        for row in rows if row.get("tile_id") and row.get("palette")
    }


def _review_status(path: Path | None, key: str, field: str) -> dict[str, str]:
    return {
        (row.get(key) or "").upper(): (row.get(field) or "").upper()
        for row in _read_csv(path) if row.get(key)
    }


def build_priority_rows(
    pack_dir: Path,
    queue: Path | None = None,
    workspace: Path | None = None,
    visual_review: Path | None = None,
    animation_review: Path | None = None,
) -> list[dict]:
    catalog = build_tile_catalog(pack_dir, queue)
    visual = {row["tile_id"]: row for row in build_context_families(pack_dir, queue)}
    animation = {row["family"]: row for row in build_animation_families(pack_dir, queue)}
    vstatus = _review_status(visual_review, "tile_id", "status")
    astatus = _review_status(animation_review, "family", "status")
    states = _master_state(workspace)

    grouped: dict[tuple[str, str], dict] = {}
    for item in catalog:
        key = (item["tile_id"].upper(), item["palette"].upper())
        row = grouped.setdefault(key, {
            "tile_id": key[0], "palette": key[1], "group": item["group"], "uses": 0,
            "conditions": set(), "families": set(), "visual_hashes": set(),
        })
        row["uses"] += 1
        if item["condition"]:
            row["conditions"].add(item["condition"])
            row["families"].add(semantic_family(item["condition"]))
        row["visual_hashes"].add(item["exact_hash"])

    result: list[dict] = []
    for key, row in grouped.items():
        state = states.get(key, {})
        status = (state.get("status") or "UNKNOWN").upper()
        if status == "EDITED":
            continue
        group = row["group"] if row["group"] in GROUP_WEIGHT else "UNASSIGNED"
        score = GROUP_WEIGHT[group]
        reasons = [f"group:{group.lower()}"]
        score += min(row["uses"], 20) * 2
        if row["uses"] >= 5:
            reasons.append("high-reuse")

        vf = visual.get(row["tile_id"])
        if vf:
            score += int(vf["risk_score"]) * 4
            if vf["needs_review"] and vstatus.get(row["tile_id"], "") not in {"REVIEWED", "PASS", "DONE"}:
                score += 24
                reasons.append("visual-context-pending")

        animation_risk = 0
        pending_anim = False
        for family_name in row["families"]:
            family = animation.get(family_name)
            if not family:
                continue
            animation_risk = max(animation_risk, int(family["risk_score"]))
            if family["needs_review"] and astatus.get(family_name, "") not in {"REVIEWED", "PASS", "DONE"}:
                pending_anim = True
        score += animation_risk * 3
        if pending_anim:
            score += 18
            reasons.append("animation-family-pending")

        if group == "UNASSIGNED":
            score += 18
            reasons.append("classification-blocker")
        if status.startswith("INVALID"):
            score += 100
            reasons.append("invalid-master")
        elif status in {"TODO", "UNKNOWN", ""}:
            score += 12
            reasons.append("not-final-art")

        result.append({
            "tile_id": row["tile_id"], "palette": row["palette"], "group": group,
            "uses": row["uses"], "conditions": sorted(row["conditions"]),
            "families": sorted(row["families"]), "visual_variants": len(row["visual_hashes"]),
            "master_status": status, "priority_score": score, "reasons": reasons,
        })

    result.sort(key=lambda r: (-r["priority_score"], -r["uses"], r["group"], r["tile_id"], r["palette"]))
    for index, row in enumerate(result, 1):
        row["priority"] = index
    return result


def write_priority_board(pack_dir: Path, output_dir: Path, *, queue: Path | None = None, workspace: Path | None = None,
                         visual_review: Path | None = None, animation_review: Path | None = None, top: int = 20) -> dict:
    rows = build_priority_rows(pack_dir, queue, workspace, visual_review, animation_review)
    output_dir.mkdir(parents=True, exist_ok=True)
    selected = rows[:max(1, top)]
    csv_path = output_dir / "FINAL_ART_NEXT.csv"
    fields = ["priority", "priority_score", "group", "tile_id", "palette", "uses", "master_status", "visual_variants", "families", "conditions", "reasons"]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in selected:
            writer.writerow({**row, "families": " | ".join(row["families"]), "conditions": " | ".join(row["conditions"]), "reasons": " | ".join(row["reasons"])})

    payload = {
        "schema": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "unfinished_candidates": len(rows),
        "top_count": len(selected),
        "important_note": "This is an evidence-driven art-production priority list, not proof that uncaptured game states do not exist.",
        "items": selected,
    }
    (output_dir / "FINAL_ART_PRIORITY.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    tr = "".join(
        "<tr>" + f"<td>{r['priority']}</td><td>{r['priority_score']}</td><td>{html.escape(r['group'])}</td>" +
        f"<td><code>{html.escape(r['tile_id'])}</code></td><td><code>{html.escape(r['palette'])}</code></td>" +
        f"<td>{r['uses']}</td><td>{html.escape(r['master_status'])}</td><td>{html.escape(', '.join(r['reasons']))}</td></tr>"
        for r in selected
    ) or "<tr><td colspan='8'>No unfinished captured art remains.</td></tr>"
    document = f"""<!doctype html><html><head><meta charset='utf-8'><title>Final Art Priority</title><style>body{{font:15px system-ui;max-width:1200px;margin:32px auto;padding:0 22px;background:#0d1117;color:#e6edf3}}.card{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:18px}}table{{width:100%;border-collapse:collapse}}td,th{{padding:8px;border-bottom:1px solid #30363d;text-align:left}}code{{color:#79c0ff}}</style></head><body><h1>Tiny Toon Visual Remaster — Final Art Priority Board</h1><div class='card'><p>Unfinished captured candidates: <b>{len(rows)}</b>. Showing top <b>{len(selected)}</b>.</p><p>{html.escape(payload['important_note'])}</p><table><tr><th>#</th><th>Score</th><th>Group</th><th>Tile</th><th>Palette</th><th>Uses</th><th>Master</th><th>Why now</th></tr>{tr}</table></div></body></html>"""
    html_path = output_dir / "FINAL_ART_PRIORITY.html"
    html_path.write_text(document, encoding="utf-8")
    return {**payload, "csv": str(csv_path), "dashboard": str(html_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 evidence-driven final art priority board")
    parser.add_argument("pack", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--queue", type=Path)
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--visual-review", type=Path)
    parser.add_argument("--animation-review", type=Path)
    parser.add_argument("--top", type=int, default=20)
    args = parser.parse_args()
    result = write_priority_board(args.pack, args.output, queue=args.queue, workspace=args.workspace,
                                  visual_review=args.visual_review, animation_review=args.animation_review, top=args.top)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
