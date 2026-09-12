from __future__ import annotations

import argparse
import csv
import html
import json
from datetime import datetime, timezone
from pathlib import Path

from animation_workbench import ACTION_TOKENS, build_animation_families
from capture_mission_control import mission_status

# Advisory state vocabulary. This never auto-completes capture missions and is not
# a substitute for an in-game full-playthrough verification.
EXPECTED_ACTIONS = {
    "PLAYER": ("idle", "walk", "run", "jump", "fall", "land", "crouch", "attack", "hit", "death"),
    "BOSS": ("intro", "idle", "attack", "hit", "phase", "death"),
    "ENEMY": ("idle", "walk", "attack", "hit", "death"),
}
GROUP_PRIORITY = {"BOSS": 100, "PLAYER": 90, "ENEMY": 70, "EFFECTS": 55, "UI": 45, "WORLD": 35, "UNASSIGNED": 80}
QUEUE_FIELDS = [
    "priority",
    "score",
    "kind",
    "art_group",
    "family",
    "target",
    "observed_states",
    "missing_expected_states",
    "conditions",
    "reason",
]


def _action_tokens(states: set[str] | list[str]) -> set[str]:
    found: set[str] = set()
    for state in states:
        for token in str(state).lower().replace("-", "_").split("_"):
            if token in ACTION_TOKENS:
                found.add(token)
    aliases = {
        "walking": "walk", "running": "run", "falling": "fall", "landing": "land",
        "hurt": "hit", "damage": "hit", "dead": "death", "die": "death",
        "attacking": "attack", "duck": "crouch",
    }
    return {aliases.get(token, token) for token in found}


def _primary_group(family: dict) -> str:
    groups = {str(value).upper() for value in family.get("groups", set()) if value}
    if len(groups) == 1:
        return next(iter(groups))
    if not groups:
        return "UNASSIGNED"
    # Mixed families are deliberately treated as unassigned/high-risk capture targets.
    return "UNASSIGNED"


def capture_profile(pack_dir: Path, queue: Path | None = None) -> dict:
    families = build_animation_families(Path(pack_dir), Path(queue) if queue else None)
    result: dict[str, dict] = {}
    for family in families:
        group = _primary_group(family)
        observed = _action_tokens(family.get("states", set()))
        expected = set(EXPECTED_ACTIONS.get(group, ()))
        missing = sorted(expected - observed)
        result[family["family"]] = {
            "family": family["family"],
            "art_group": group,
            "uses": family["uses"],
            "conditions": sorted(family["conditions"]),
            "tile_ids": sorted(family["tile_ids"]),
            "palettes": sorted(family["palettes"]),
            "observed_states": sorted(observed),
            "missing_expected_states": missing,
            "risk_score": family["risk_score"],
            "needs_review": family["needs_review"],
        }
    return result


def compare_profiles(previous: dict[str, dict] | None, current: dict[str, dict]) -> dict:
    previous = previous or {}
    previous_names = set(previous)
    current_names = set(current)
    new_families = sorted(current_names - previous_names)
    disappeared_families = sorted(previous_names - current_names)
    family_changes: list[dict] = []

    for name in sorted(previous_names & current_names):
        old = previous[name]
        new = current[name]
        old_conditions = set(old.get("conditions", []))
        new_conditions = set(new.get("conditions", []))
        old_states = set(old.get("observed_states", []))
        new_states = set(new.get("observed_states", []))
        added_conditions = sorted(new_conditions - old_conditions)
        removed_conditions = sorted(old_conditions - new_conditions)
        added_states = sorted(new_states - old_states)
        removed_states = sorted(old_states - new_states)
        if added_conditions or removed_conditions or added_states or removed_states:
            family_changes.append({
                "family": name,
                "added_conditions": added_conditions,
                "removed_conditions": removed_conditions,
                "added_states": added_states,
                "removed_states": removed_states,
            })

    regressions = []
    regressions.extend({"family": name, "reason": "family disappeared from current capture"} for name in disappeared_families)
    for change in family_changes:
        if change["removed_conditions"] or change["removed_states"]:
            regressions.append({
                "family": change["family"],
                "reason": "coverage present in previous capture is absent now",
                "removed_conditions": change["removed_conditions"],
                "removed_states": change["removed_states"],
            })

    return {
        "new_families": new_families,
        "disappeared_families": disappeared_families,
        "family_changes": family_changes,
        "regressions": regressions,
        "progressed": bool(new_families or any(item["added_conditions"] or item["added_states"] for item in family_changes)),
    }


def _mission_targets(capture_manifest: Path | None) -> list[dict]:
    if not capture_manifest or not Path(capture_manifest).is_file():
        return []
    status = mission_status(Path(capture_manifest))
    items: list[dict] = []
    for index, mission in enumerate(status.get("next_missions", []), 1):
        items.append({
            "priority": index,
            "score": 130 - index,
            "kind": "MISSION",
            "art_group": "GAMEPLAY",
            "family": "",
            "target": mission["key"],
            "observed_states": "",
            "missing_expected_states": "",
            "conditions": "",
            "reason": mission["label"],
        })
    return items


def build_capture_queue(
    current_pack: Path,
    queue: Path | None = None,
    previous_pack: Path | None = None,
    previous_queue: Path | None = None,
    capture_manifest: Path | None = None,
) -> dict:
    current = capture_profile(current_pack, queue)
    previous = capture_profile(previous_pack, previous_queue or queue) if previous_pack else None
    comparison = compare_profiles(previous, current)
    rows: list[dict] = _mission_targets(capture_manifest)

    for family in current.values():
        group = family["art_group"]
        missing = family["missing_expected_states"]
        base = GROUP_PRIORITY.get(group, 25)
        if missing and group in EXPECTED_ACTIONS:
            rows.append({
                "priority": 0,
                "score": base + min(30, 4 * len(missing)) + min(15, family["risk_score"]),
                "kind": "STATE_GAP",
                "art_group": group,
                "family": family["family"],
                "target": "trigger missing states",
                "observed_states": " | ".join(family["observed_states"]),
                "missing_expected_states": " | ".join(missing),
                "conditions": " | ".join(family["conditions"]),
                "reason": "Advisory state vocabulary suggests this captured family may still be incomplete",
            })
        if group == "UNASSIGNED":
            rows.append({
                "priority": 0,
                "score": 95 + min(15, family["risk_score"]),
                "kind": "CLASSIFICATION_CAPTURE",
                "art_group": group,
                "family": family["family"],
                "target": "capture a clearer gameplay context",
                "observed_states": " | ".join(family["observed_states"]),
                "missing_expected_states": "",
                "conditions": " | ".join(family["conditions"]),
                "reason": "Family is mixed or unassigned; a clearer condition/context will help classification",
            })

    for regression in comparison["regressions"]:
        rows.append({
            "priority": 0,
            "score": 160,
            "kind": "CAPTURE_REGRESSION",
            "art_group": current.get(regression["family"], previous.get(regression["family"], {}) if previous else {}).get("art_group", "UNKNOWN"),
            "family": regression["family"],
            "target": "restore previous coverage",
            "observed_states": "",
            "missing_expected_states": "",
            "conditions": "",
            "reason": regression["reason"],
        })

    rows.sort(key=lambda row: (-int(row["score"]), row["kind"], row["family"], row["target"]))
    for index, row in enumerate(rows, 1):
        row["priority"] = index

    return {
        "schema": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "important_note": (
            "This is an advisory capture planner. Missing-state suggestions come from generic animation vocabulary and never prove that a state exists in this specific game. "
            "Only explicit Capture Mission Control verification and in-game MesenCE testing can establish real coverage."
        ),
        "current_pack": str(Path(current_pack).resolve()),
        "previous_pack": str(Path(previous_pack).resolve()) if previous_pack else None,
        "families": list(current.values()),
        "comparison": comparison,
        "queue": rows,
    }


def write_outputs(result: dict, output_dir: Path) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "CAPTURE_GAP_PLAN.json"
    csv_path = output_dir / "CAPTURE_NEXT.csv"
    html_path = output_dir / "CAPTURE_GAP_PLAN.html"
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=QUEUE_FIELDS)
        writer.writeheader()
        for row in result["queue"]:
            writer.writerow({key: row.get(key, "") for key in QUEUE_FIELDS})

    top = result["queue"][:30]
    rows_html = "".join(
        "<tr>"
        f"<td>{row['priority']}</td><td>{row['score']}</td><td>{html.escape(row['kind'])}</td>"
        f"<td>{html.escape(row['art_group'])}</td><td><code>{html.escape(row['family'])}</code></td>"
        f"<td>{html.escape(row['target'])}</td><td>{html.escape(row['missing_expected_states'])}</td>"
        f"<td>{html.escape(row['reason'])}</td></tr>"
        for row in top
    ) or "<tr><td colspan='8'>No advisory capture gaps found.</td></tr>"
    regressions = result["comparison"]["regressions"]
    regression_html = "".join(
        f"<li><code>{html.escape(item['family'])}</code> — {html.escape(item['reason'])}</li>" for item in regressions
    ) or "<li>None detected.</li>"
    document = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'>
<title>Project #002 Capture Gap Planner</title><style>body{{font:15px system-ui;max-width:1250px;margin:30px auto;padding:0 22px;background:#0d1117;color:#e6edf3}}.card{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:18px;margin:14px 0}}table{{width:100%;border-collapse:collapse}}td,th{{padding:8px;border-bottom:1px solid #30363d;text-align:left;vertical-align:top}}code{{color:#79c0ff}}.warn{{color:#d29922}}</style></head><body>
<h1>Tiny Toon Visual Remaster — Capture Gap Planner</h1>
<div class='card'><p>{html.escape(result['important_note'])}</p><p>Families: <b>{len(result['families'])}</b> · queue items: <b>{len(result['queue'])}</b> · progressed vs previous: <b>{result['comparison']['progressed']}</b></p></div>
<div class='card'><h2 class='warn'>Coverage regressions</h2><ul>{regression_html}</ul></div>
<div class='card'><h2>CAPTURE NEXT — highest impact</h2><table><tr><th>#</th><th>Score</th><th>Kind</th><th>Group</th><th>Family</th><th>Target</th><th>Suggested missing states</th><th>Why</th></tr>{rows_html}</table></div>
</body></html>"""
    html_path.write_text(document, encoding="utf-8")
    return {"json": str(json_path), "csv": str(csv_path), "html": str(html_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 metadata-only capture gap planner")
    parser.add_argument("current", type=Path)
    parser.add_argument("--queue", type=Path)
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--previous-queue", type=Path)
    parser.add_argument("--capture-manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_capture_queue(
        args.current,
        args.queue,
        args.previous,
        args.previous_queue,
        args.capture_manifest,
    )
    outputs = write_outputs(result, args.output)
    print(json.dumps({"outputs": outputs, "queue_items": len(result["queue"]), "comparison": result["comparison"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
