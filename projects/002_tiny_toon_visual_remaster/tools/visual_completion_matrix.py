from __future__ import annotations

import argparse
import csv
import html
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from art_production import build_tile_catalog

GROUP_ORDER = ("PLAYER", "BOSS", "ENEMY", "WORLD", "UI", "EFFECTS", "UNASSIGNED")
GROUP_WEIGHT = {"PLAYER": 7, "BOSS": 6, "ENEMY": 5, "WORLD": 3, "UI": 4, "EFFECTS": 4, "UNASSIGNED": 6}
FINAL_STATES = {"EDITED", "DONE", "PASS", "FINAL"}
BAD_STATES = {"INVALID", "INVALID_SIZE", "INVALID_FORMAT", "CONFLICT", "STALE"}


def _read_csv(path: Path | None) -> list[dict]:
    if path is None or not Path(path).is_file():
        return []
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _workspace_states(workspace: Path | None) -> dict[tuple[str, str], dict]:
    if workspace is None:
        return {}
    rows = _read_csv(Path(workspace) / "ART_STATE.csv")
    return {
        ((row.get("tile_id") or "").upper(), (row.get("palette") or "").upper()): row
        for row in rows if row.get("tile_id") and row.get("palette")
    }


def build_matrix(pack_dir: Path, *, queue: Path | None = None, workspace: Path | None = None, batch_size: int = 40) -> dict:
    catalog = build_tile_catalog(Path(pack_dir), Path(queue) if queue else None)
    states = _workspace_states(workspace)
    grouped: dict[tuple[str, str], dict] = {}

    for item in catalog:
        key = (item["tile_id"].upper(), item["palette"].upper())
        row = grouped.setdefault(key, {
            "tile_id": key[0], "palette": key[1], "group": (item.get("group") or "UNASSIGNED").upper(),
            "uses": 0, "conditions": set(), "exact_hashes": set(),
        })
        row["uses"] += 1
        if item.get("condition"):
            row["conditions"].add(item["condition"])
        if item.get("exact_hash"):
            row["exact_hashes"].add(item["exact_hash"])

    totals = defaultdict(lambda: {"masters": 0, "final": 0, "todo": 0, "invalid": 0, "uses": 0, "final_uses": 0})
    unfinished: list[dict] = []

    for key, row in grouped.items():
        state = states.get(key, {})
        status = (state.get("status") or "TODO").upper()
        group = row["group"] if row["group"] in GROUP_ORDER else "UNASSIGNED"
        final = status in FINAL_STATES
        invalid = status in BAD_STATES or status.startswith("INVALID")
        stat = totals[group]
        stat["masters"] += 1
        stat["uses"] += row["uses"]
        if final:
            stat["final"] += 1
            stat["final_uses"] += row["uses"]
        elif invalid:
            stat["invalid"] += 1
        else:
            stat["todo"] += 1

        if not final:
            score = GROUP_WEIGHT[group] * 100 + min(row["uses"], 50) * 5 + len(row["conditions"]) * 4
            reasons = [f"group:{group.lower()}"]
            if row["uses"] >= 5:
                reasons.append("high-reuse")
            if invalid:
                score += 500
                reasons.append("invalid-master")
            if group == "UNASSIGNED":
                score += 250
                reasons.append("classification-blocker")
            if len(row["exact_hashes"]) > 1:
                score += 30
                reasons.append("visual-variants")
            unfinished.append({
                "group": group, "tile_id": row["tile_id"], "palette": row["palette"], "status": status,
                "uses": row["uses"], "condition_count": len(row["conditions"]),
                "visual_variants": len(row["exact_hashes"]), "impact_score": score, "reasons": reasons,
            })

    unfinished.sort(key=lambda r: (-r["impact_score"], -r["uses"], r["group"], r["tile_id"], r["palette"]))
    batch = unfinished[: max(1, batch_size)]
    for index, row in enumerate(batch, 1):
        row["batch_order"] = index

    groups: list[dict] = []
    weighted_done = 0
    weighted_total = 0
    for group in GROUP_ORDER:
        stat = totals[group]
        if stat["masters"] == 0:
            continue
        master_pct = round(stat["final"] * 100.0 / stat["masters"], 1)
        use_pct = round(stat["final_uses"] * 100.0 / stat["uses"], 1) if stat["uses"] else 0.0
        weight = GROUP_WEIGHT[group]
        weighted_done += stat["final"] * weight
        weighted_total += stat["masters"] * weight
        groups.append({"group": group, **stat, "master_percent": master_pct, "use_percent": use_pct, "weight": weight})

    overall = round(weighted_done * 100.0 / weighted_total, 1) if weighted_total else 0.0
    blocking = sum(item["invalid"] for item in groups) + totals["UNASSIGNED"]["masters"]
    return {
        "schema": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "important_note": "Measures only graphics present in the supplied local capture/pack. Uncaptured game states remain unknown.",
        "overall_weighted_percent": overall,
        "captured_masters": len(grouped),
        "captured_final": sum(item["final"] for item in groups),
        "captured_unfinished": len(unfinished),
        "blocking_items": blocking,
        "groups": groups,
        "next_batch": batch,
    }


def write_matrix(result: dict, output_dir: Path) -> dict:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "VISUAL_COMPLETION_MATRIX.json"
    csv_path = output / "VISUAL_COMPLETION_MATRIX.csv"
    batch_path = output / "NEXT_HIGH_IMPACT_ART_BATCH.csv"
    html_path = output / "VISUAL_COMPLETION_MATRIX.html"
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    fields = ["group", "masters", "final", "todo", "invalid", "uses", "final_uses", "master_percent", "use_percent", "weight"]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(result["groups"])

    batch_fields = ["batch_order", "impact_score", "group", "tile_id", "palette", "status", "uses", "condition_count", "visual_variants", "reasons"]
    with batch_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=batch_fields)
        writer.writeheader()
        for row in result["next_batch"]:
            writer.writerow({**row, "reasons": " | ".join(row["reasons"])})

    group_rows = "".join(
        f"<tr><td>{html.escape(g['group'])}</td><td>{g['final']}/{g['masters']}</td><td>{g['master_percent']}%</td><td>{g['use_percent']}%</td><td>{g['todo']}</td><td>{g['invalid']}</td></tr>"
        for g in result["groups"]
    )
    batch_rows = "".join(
        f"<tr><td>{r['batch_order']}</td><td>{r['impact_score']}</td><td>{html.escape(r['group'])}</td><td><code>{html.escape(r['tile_id'])}</code></td><td><code>{html.escape(r['palette'])}</code></td><td>{r['uses']}</td><td>{html.escape(', '.join(r['reasons']))}</td></tr>"
        for r in result["next_batch"]
    ) or "<tr><td colspan='7'>No unfinished captured graphics remain.</td></tr>"
    doc = f"""<!doctype html><html><head><meta charset='utf-8'><title>Visual Completion Matrix</title><style>body{{font:15px system-ui;max-width:1250px;margin:30px auto;padding:0 22px;background:#0d1117;color:#e6edf3}}.hero,.card{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:18px;margin:14px 0}}.big{{font-size:42px;font-weight:800}}table{{width:100%;border-collapse:collapse}}th,td{{padding:8px;border-bottom:1px solid #30363d;text-align:left}}code{{color:#79c0ff}}</style></head><body><h1>Tiny Toon Visual Remaster — Visual Completion Matrix</h1><div class='hero'><div class='big'>{result['overall_weighted_percent']}%</div><p>Weighted captured-art completion · {result['captured_final']}/{result['captured_masters']} masters final · {result['captured_unfinished']} unfinished · {result['blocking_items']} blockers</p><p>{html.escape(result['important_note'])}</p></div><div class='card'><h2>Completion by production group</h2><table><tr><th>Group</th><th>Final</th><th>Master %</th><th>Usage-weighted %</th><th>TODO</th><th>Invalid</th></tr>{group_rows}</table></div><div class='card'><h2>Next high-impact art batch</h2><table><tr><th>#</th><th>Impact</th><th>Group</th><th>Tile</th><th>Palette</th><th>Uses</th><th>Why</th></tr>{batch_rows}</table></div></body></html>"""
    html_path.write_text(doc, encoding="utf-8")
    return {"json": str(json_path), "csv": str(csv_path), "batch_csv": str(batch_path), "dashboard": str(html_path)}


def build_and_write(pack_dir: Path, output_dir: Path, *, queue: Path | None = None, workspace: Path | None = None, batch_size: int = 40) -> dict:
    result = build_matrix(pack_dir, queue=queue, workspace=workspace, batch_size=batch_size)
    result["outputs"] = write_matrix(result, output_dir)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 captured-art visual completion matrix and next high-impact batch")
    parser.add_argument("pack", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--queue", type=Path)
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--batch-size", type=int, default=40)
    args = parser.parse_args()
    print(json.dumps(build_and_write(args.pack, args.output, queue=args.queue, workspace=args.workspace, batch_size=args.batch_size), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
