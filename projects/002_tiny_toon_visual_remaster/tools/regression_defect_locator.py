from __future__ import annotations

import argparse
import csv
import html
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from art_production import build_tile_catalog
from release_candidate import pack_fingerprint

SCHEMA = "swir.project002.regression-defect-locator.v1"
SELECTION_SCHEMA = "swir.project002.regression-defect-selection.v1"
ART_CATEGORIES = {"MISSING_HD", "WRONG_PALETTE", "ANIMATION_SEAM", "TRANSPARENCY", "OTHER"}
CASE_GROUPS = {
    "boot_title_menu": ("UI", "WORLD"),
    "player_movement": ("PLAYER",),
    "player_actions_damage_death": ("PLAYER",),
    "world_route_1": ("WORLD",),
    "world_route_2": ("WORLD",),
    "enemies": ("ENEMY",),
    "bosses": ("BOSS",),
    "hud_text_status": ("UI",),
    "effects_transitions": ("EFFECTS",),
    "ending_credits": ("UI", "WORLD"),
}


class DefectLocatorError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> dict:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DefectLocatorError(f"Cannot read {path.name}: {exc}") from exc
    if not isinstance(data, dict):
        raise DefectLocatorError(f"Expected JSON object: {path.name}")
    return data


def _sprint_index(project_root: Path) -> dict[tuple[str, str], dict]:
    manifest = Path(project_root) / "Artwork" / "CurrentImpactSprint" / "ART_SPRINT_KIT.json"
    if not manifest.is_file():
        return {}
    data = _load_json(manifest)
    result: dict[tuple[str, str], dict] = {}
    for row in data.get("items") or []:
        tile = str(row.get("tile_id") or "").upper()
        palette = str(row.get("palette") or "").upper()
        if not tile or not palette:
            continue
        seed_tile = str(row.get("seed_tile_id") or tile).upper()
        seed_palette = str(row.get("seed_palette") or palette).upper()
        group = str(row.get("group") or "UNASSIGNED").upper()
        result[(tile, palette)] = {
            "family": f"{group}::{seed_tile}::{seed_palette}",
            "family_seed_tile": seed_tile,
            "family_seed_palette": seed_palette,
            "priority": int(row.get("priority", 999999) or 999999),
            "impact_score": int(row.get("impact_score", row.get("priority_score", 0)) or 0),
        }
    return result


def _aggregate_catalog(pack: Path, queue: Path | None) -> list[dict]:
    grouped: dict[tuple[str, str], dict] = {}
    for item in build_tile_catalog(Path(pack), Path(queue) if queue and Path(queue).is_file() else None):
        tile = str(item.get("tile_id") or "").upper()
        palette = str(item.get("palette") or "").upper()
        if not tile or not palette:
            continue
        key = (tile, palette)
        row = grouped.setdefault(key, {
            "tile_id": tile,
            "palette": palette,
            "group": str(item.get("group") or "UNASSIGNED").upper(),
            "uses": 0,
            "conditions": set(),
            "locations": [],
        })
        row["uses"] += 1
        condition = str(item.get("condition") or "")
        if condition:
            row["conditions"].add(condition)
        row["locations"].append({
            "image_index": str(item.get("image_index") or ""),
            "x": int(item.get("x") or 0),
            "y": int(item.get("y") or 0),
            "condition": condition,
        })

    palette_counts: dict[str, int] = defaultdict(int)
    for tile, _palette in grouped:
        palette_counts[tile] += 1

    rows = []
    for row in grouped.values():
        row["conditions"] = sorted(row["conditions"])
        row["condition_count"] = len(row["conditions"])
        row["palette_variant_count"] = palette_counts[row["tile_id"]]
        rows.append(row)
    return rows


def _score_candidate(row: dict, *, expected_groups: set[str], category: str, sprint: dict | None) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    group = str(row.get("group") or "UNASSIGNED").upper()
    uses = int(row.get("uses", 0) or 0)
    condition_count = int(row.get("condition_count", 0) or 0)
    palette_variants = int(row.get("palette_variant_count", 1) or 1)

    if group in expected_groups:
        score += 1200
        reasons.append("regression-case-group")
    else:
        score -= 200
    score += min(uses, 50) * 8
    if uses >= 5:
        reasons.append("high-reuse")
    score += min(condition_count, 12) * 25
    if condition_count > 1:
        reasons.append("multi-condition")

    if sprint:
        score += 350
        score += min(int(sprint.get("impact_score", 0) or 0), 500) // 5
        reasons.append("current-family-aware-sprint")
        if int(sprint.get("priority", 999999) or 999999) <= 5:
            score += 100
            reasons.append("high-sprint-priority")

    if category == "ANIMATION_SEAM":
        if group in {"PLAYER", "ENEMY", "BOSS"}:
            score += 220
            reasons.append("animation-family")
        score += min(condition_count, 8) * 30
    elif category == "WRONG_PALETTE":
        score += min(max(0, palette_variants - 1), 6) * 70
        if palette_variants > 1:
            reasons.append("palette-context-variants")
    elif category == "TRANSPARENCY":
        score += min(uses, 20) * 6
        reasons.append("alpha-review-target")
    elif category == "MISSING_HD":
        if not sprint:
            score += 80
            reasons.append("outside-current-sprint")
    elif category == "OTHER":
        score += min(uses, 20) * 3

    if group == "UNASSIGNED":
        score -= 150
        reasons.append("unassigned-needs-human-check")
    return score, reasons


def build_plan(project_root: Path, pack: Path, case_key: str, category: str, *, top: int = 12) -> dict:
    root = Path(project_root)
    runtime = Path(pack)
    category = category.strip().upper()
    if category not in ART_CATEGORIES:
        raise DefectLocatorError(f"Defect locator is only for art-repair categories: {sorted(ART_CATEGORIES)}")
    if case_key not in CASE_GROUPS:
        raise DefectLocatorError(f"Unknown regression case: {case_key}")
    if not (runtime / "hires.txt").is_file():
        raise DefectLocatorError("Runtime pack is missing hires.txt")

    queue = root / "Artwork" / "ART_QUEUE.csv"
    sprint_index = _sprint_index(root)
    expected_groups = set(CASE_GROUPS[case_key])
    ranked = []
    for row in _aggregate_catalog(runtime, queue if queue.is_file() else None):
        sprint = sprint_index.get((row["tile_id"], row["palette"]))
        score, reasons = _score_candidate(row, expected_groups=expected_groups, category=category, sprint=sprint)
        family = (sprint or {}).get("family", "")
        conditions = list(row.get("conditions") or [])
        ranked.append({
            "score": score,
            "group": row["group"],
            "tile_id": row["tile_id"],
            "palette": row["palette"],
            "uses": row["uses"],
            "condition_count": row["condition_count"],
            "conditions": conditions[:8],
            "palette_variant_count": row["palette_variant_count"],
            "family": family,
            "in_current_sprint": bool(sprint),
            "target_tag": f"[SWIR_TARGET tile={row['tile_id']} palette={row['palette']}]",
            "reasons": reasons,
        })
    ranked.sort(key=lambda row: (-int(row["score"]), row["group"], row["tile_id"], row["palette"]))
    candidates = ranked[: max(1, int(top))]
    for index, row in enumerate(candidates, start=1):
        row["rank"] = index

    return {
        "schema": SCHEMA,
        "generated_utc": _now(),
        "status": "TARGET_CANDIDATES_READY" if candidates else "NO_TARGET_CANDIDATES",
        "pack_fingerprint": pack_fingerprint(runtime),
        "case_key": case_key,
        "failure_category": category,
        "expected_groups": list(CASE_GROUPS[case_key]),
        "candidate_count": len(candidates),
        "candidates": candidates,
        "policy": "Candidates narrow a real observed FAIL; they never prove gameplay coverage or auto-record regression evidence.",
        "privacy_contract": {
            "metadata_only": True,
            "absolute_local_paths": False,
            "capture_pixels": False,
            "rom_bytes": False,
            "save_states": False,
            "emulator_binaries": False,
        },
    }


def write_plan(plan: dict, output_dir: Path) -> dict:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "REGRESSION_DEFECT_TARGETS.json"
    csv_path = output / "REGRESSION_DEFECT_TARGETS.csv"
    html_path = output / "REGRESSION_DEFECT_TARGETS.html"
    json_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    fields = ["rank", "score", "group", "tile_id", "palette", "uses", "condition_count", "palette_variant_count", "family", "in_current_sprint", "target_tag", "reasons", "conditions"]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in plan["candidates"]:
            writer.writerow({**row, "reasons": " | ".join(row["reasons"]), "conditions": " | ".join(row["conditions"])})

    rows = "".join(
        "<tr>"
        f"<td>{r['rank']}</td><td>{r['score']}</td><td>{html.escape(r['group'])}</td>"
        f"<td><code>{html.escape(r['tile_id'])}</code></td><td><code>{html.escape(r['palette'])}</code></td>"
        f"<td>{r['uses']}</td><td>{r['condition_count']}</td><td>{html.escape(r['family'] or '—')}</td>"
        f"<td>{html.escape(', '.join(r['reasons']))}</td>"
        "</tr>"
        for r in plan["candidates"]
    ) or "<tr><td colspan='9'>No candidate metadata was found for this runtime/case.</td></tr>"
    document = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><title>Regression Defect Locator</title><style>body{{font:15px system-ui;max-width:1300px;margin:28px auto;padding:0 22px;background:#0d1117;color:#e6edf3}}.card{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:18px;margin:14px 0}}table{{width:100%;border-collapse:collapse}}td,th{{padding:8px;border-bottom:1px solid #30363d;text-align:left;vertical-align:top}}code{{color:#79c0ff}}</style></head><body><h1>Project #002 — Regression Defect Locator</h1><div class='card'><p>Case: <b>{html.escape(plan['case_key'])}</b> · category <b>{html.escape(plan['failure_category'])}</b></p><p>Exact runtime: <code>{html.escape(plan['pack_fingerprint'])}</code></p><p>Expected groups: {html.escape(', '.join(plan['expected_groups']))}</p><p>{html.escape(plan['policy'])}</p></div><div class='card'><table><tr><th>#</th><th>Score</th><th>Group</th><th>Tile</th><th>Palette</th><th>Uses</th><th>Conditions</th><th>Family</th><th>Why</th></tr>{rows}</table></div></body></html>"""
    html_path.write_text(document, encoding="utf-8")
    return {"json": str(json_path), "csv": str(csv_path), "dashboard": str(html_path)}


def choose(plan: dict, index: int) -> dict:
    if plan.get("schema") != SCHEMA:
        raise DefectLocatorError("Unsupported defect locator plan schema")
    candidates = list(plan.get("candidates") or [])
    selected = next((row for row in candidates if int(row.get("rank", 0) or 0) == int(index)), None)
    if selected is None:
        raise DefectLocatorError(f"Unknown candidate rank: {index}")
    context_bits = [f"group={selected['group']}"]
    if selected.get("family"):
        context_bits.append(f"family={selected['family']}")
    if selected.get("conditions"):
        context_bits.append("conditions=" + ",".join(selected["conditions"][:4]))
    return {
        "schema": SELECTION_SCHEMA,
        "selected_utc": _now(),
        "pack_fingerprint": plan["pack_fingerprint"],
        "case_key": plan["case_key"],
        "failure_category": plan["failure_category"],
        "rank": selected["rank"],
        "group": selected["group"],
        "tile_id": selected["tile_id"],
        "palette": selected["palette"],
        "family": selected.get("family", ""),
        "conditions": selected.get("conditions", []),
        "target_tag": selected["target_tag"],
        "context_note": "SWIR_CONTEXT " + " ".join(context_bits),
        "policy": "Human-selected targeting metadata for a real observed FAIL; not gameplay completion evidence.",
    }


def write_selection(selection: dict, output_dir: Path) -> Path:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    path = output / "REGRESSION_DEFECT_SELECTION.json"
    path.write_text(json.dumps(selection, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 metadata-only regression defect tile/palette/family locator")
    sub = parser.add_subparsers(dest="command", required=True)
    plan_cmd = sub.add_parser("plan")
    plan_cmd.add_argument("project_root", type=Path)
    plan_cmd.add_argument("pack", type=Path)
    plan_cmd.add_argument("case_key")
    plan_cmd.add_argument("category")
    plan_cmd.add_argument("--output", type=Path, required=True)
    plan_cmd.add_argument("--top", type=int, default=12)
    choose_cmd = sub.add_parser("choose")
    choose_cmd.add_argument("plan_json", type=Path)
    choose_cmd.add_argument("index", type=int)
    choose_cmd.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "plan":
        plan = build_plan(args.project_root, args.pack, args.case_key, args.category, top=max(1, args.top))
        outputs = write_plan(plan, args.output)
        result = {"plan": plan, "outputs": outputs}
    else:
        plan = _load_json(args.plan_json)
        selection = choose(plan, args.index)
        path = write_selection(selection, args.output)
        result = {"selection": selection, "output": str(path)}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
