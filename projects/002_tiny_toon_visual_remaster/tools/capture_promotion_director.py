from __future__ import annotations

import argparse
import csv
import html
import json
from datetime import datetime, timezone
from pathlib import Path

from animation_workbench import write_dashboard as write_animation_dashboard
from art_sprint_kit import export_sprint_kit
from capture_gap_planner import build_capture_queue, write_outputs as write_capture_gap_outputs
from capture_mission_control import ensure_manifest, mission_status
from final_art_priority import write_priority_board
from final_regression_cockpit import ensure_manifest as ensure_regression_manifest
from production_sprint import build_and_write as build_production_sprint
from production_sync import prepare_incremental
from validate_hdpack import validate
from visual_context_audit import write_dashboard as write_visual_dashboard


def _paths(project_root: Path) -> dict[str, Path]:
    root = Path(project_root)
    artwork = root / "Artwork"
    reports = root / "Reports"
    return {
        "root": root,
        "artwork": artwork,
        "reports": reports,
        "queue": artwork / "ART_QUEUE.csv",
        "workspace": artwork / "MasterWorkspace",
        "visual_review": artwork / "VISUAL_CONTEXT_REVIEW.csv",
        "animation_review": artwork / "ANIMATION_FAMILY_REVIEW.csv",
        "capture_manifest": root / "CAPTURE_MISSIONS.json",
        "regression_manifest": root / "FINAL_REGRESSION.json",
        "sprint": artwork / "CurrentArtSprint",
    }


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["priority", "kind", "group", "target", "reason"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def _next_actions(capture_gap: dict, capture_status: dict, priority: dict | None) -> list[dict]:
    actions: list[dict] = []
    regressions = [row for row in capture_gap.get("queue", []) if row.get("kind") == "CAPTURE_REGRESSION"]
    for row in regressions[:10]:
        target = row.get("family") or row.get("label") or row.get("state") or "capture coverage"
        actions.append({
            "priority": 100,
            "kind": "CAPTURE_REGRESSION",
            "group": row.get("group", ""),
            "target": target,
            "reason": "Previously observed capture evidence is missing from the candidate capture; promotion is blocked.",
        })
    if not regressions and capture_status.get("release_capture_gate") != "PASS":
        for mission in capture_status.get("next_missions", [])[:10]:
            actions.append({
                "priority": 95,
                "kind": "CAPTURE_MISSION",
                "group": "",
                "target": mission.get("label") or mission.get("key") or str(mission),
                "reason": "Explicit full-game capture mission is still unverified. Promotion may continue, but release remains blocked.",
            })
    if priority:
        for row in priority.get("top", priority.get("rows", []))[:10]:
            actions.append({
                "priority": int(row.get("priority_score", 0) or 0),
                "kind": "FINAL_ART",
                "group": row.get("group", ""),
                "target": row.get("tile_id", ""),
                "reason": ", ".join(row.get("reasons", [])) if isinstance(row.get("reasons"), list) else str(row.get("reasons", "")),
            })
    return sorted(actions, key=lambda row: -int(row.get("priority", 0)))


def _write_dashboard(result: dict, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "CAPTURE_PROMOTION.json"
    csv_path = output_dir / "CAPTURE_PROMOTION_NEXT.csv"
    html_path = output_dir / "CAPTURE_PROMOTION.html"
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    _write_csv(csv_path, result.get("next_actions", []))

    rows = "".join(
        "<tr>"
        f"<td>{html.escape(str(row.get('priority', '')))}</td>"
        f"<td>{html.escape(str(row.get('kind', '')))}</td>"
        f"<td>{html.escape(str(row.get('group', '')))}</td>"
        f"<td>{html.escape(str(row.get('target', '')))}</td>"
        f"<td>{html.escape(str(row.get('reason', '')))}</td>"
        "</tr>"
        for row in result.get("next_actions", [])
    ) or "<tr><td colspan='5'>No queued action.</td></tr>"
    gate = result.get("promotion_gate", "BLOCKED")
    document = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'>
<title>Project #002 Capture Promotion Director</title><style>
body{{font:15px system-ui;max-width:1250px;margin:30px auto;padding:0 22px;background:#0d1117;color:#e6edf3}}
.card{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:16px;margin:12px 0}}
table{{width:100%;border-collapse:collapse}}th,td{{padding:8px;border-bottom:1px solid #30363d;text-align:left}}
.pass{{color:#3fb950}}.blocked{{color:#f85149}}code{{color:#79c0ff}}</style></head><body>
<h1>Capture Promotion Director</h1>
<div class='card'><h2>Promotion gate: <span class='{'pass' if gate == 'PROMOTED' else 'blocked'}'>{html.escape(gate)}</span></h2>
<p>{html.escape(result.get('important_note', ''))}</p>
<p>Candidate: <code>{html.escape(result.get('candidate_capture', ''))}</code></p>
<p>Capture regressions: {result.get('capture_regressions', 0)}</p></div>
<div class='card'><h2>Do this next</h2><table><tr><th>Priority</th><th>Type</th><th>Group</th><th>Target</th><th>Reason</th></tr>{rows}</table></div>
</body></html>"""
    html_path.write_text(document, encoding="utf-8")
    return {"json": str(json_path), "csv": str(csv_path), "dashboard": str(html_path)}


def promote_capture(
    project_root: Path,
    current_capture: Path,
    *,
    previous_capture: Path | None = None,
    top: int = 20,
    create_sprint: bool = False,
) -> dict:
    """Validate and promote a candidate MesenCE capture into the local art-production pipeline.

    A candidate with capture regressions is never synchronized into MasterWorkspace. This preserves the
    previous production baseline and prevents a smaller/poorer capture from silently retiring useful art.
    Explicit Capture Mission Control items are never auto-completed by this function.
    """
    p = _paths(project_root)
    capture = Path(current_capture)
    previous = Path(previous_capture) if previous_capture else None
    p["reports"].mkdir(parents=True, exist_ok=True)
    p["artwork"].mkdir(parents=True, exist_ok=True)
    ensure_manifest(p["capture_manifest"])
    ensure_regression_manifest(p["regression_manifest"])

    errors, warnings, _ = validate(capture)
    if errors:
        raise ValueError("Candidate capture failed HD Pack validation: " + "; ".join(errors))

    existing_queue = p["queue"] if p["queue"].is_file() else None
    gap = build_capture_queue(
        capture,
        existing_queue,
        previous,
        existing_queue,
        p["capture_manifest"],
    )
    gap_outputs = write_capture_gap_outputs(gap, p["reports"] / "CaptureGapPlanner")
    regressions = [row for row in gap.get("queue", []) if row.get("kind") == "CAPTURE_REGRESSION"]
    capture_status = mission_status(p["capture_manifest"])

    result: dict = {
        "schema": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_capture": str(capture.resolve()),
        "previous_capture": str(previous.resolve()) if previous else None,
        "promotion_gate": "BLOCKED_REGRESSION" if regressions else "PROMOTED",
        "capture_regressions": len(regressions),
        "capture_mission_gate": capture_status.get("release_capture_gate", "BLOCKED"),
        "warnings": warnings,
        "gap_outputs": gap_outputs,
        "important_note": (
            "Promotion is blocked only by structural capture regression. Capture Mission Control remains explicit/manual and still governs full-game release coverage."
        ),
    }

    if regressions:
        result["next_actions"] = _next_actions(gap, capture_status, None)
        result["outputs"] = _write_dashboard(result, p["reports"] / "CapturePromotion")
        return result

    sync = prepare_incremental(capture, p["root"])
    visual = write_visual_dashboard(capture, p["queue"], p["visual_review"], p["reports"] / "VisualContext")
    animation = write_animation_dashboard(capture, p["queue"], p["animation_review"], p["reports"] / "AnimationWorkbench")
    priority = write_priority_board(
        capture,
        p["reports"] / "FinalArtPriority",
        queue=p["queue"],
        workspace=p["workspace"],
        visual_review=p["visual_review"],
        animation_review=p["animation_review"],
        top=max(1, top),
    )
    production = build_production_sprint(
        p["root"], capture, capture, p["reports"] / "ProductionSprint",
        previous_capture=previous, top=max(1, top),
    )

    sprint = None
    if create_sprint:
        sprint = export_sprint_kit(
            capture,
            p["workspace"],
            p["sprint"],
            queue=p["queue"],
            visual_review=p["visual_review"],
            animation_review=p["animation_review"],
            top=max(1, top),
            overwrite=True,
        )

    result.update({
        "sync": sync,
        "visual_context": visual,
        "animation_family": animation,
        "final_art_priority": priority,
        "production_sprint": production,
        "art_sprint": sprint,
    })
    result["next_actions"] = _next_actions(gap, capture_status, priority)
    result["outputs"] = _write_dashboard(result, p["reports"] / "CapturePromotion")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 regression-safe capture promotion director")
    parser.add_argument("project_root", type=Path)
    parser.add_argument("current_capture", type=Path)
    parser.add_argument("--previous-capture", type=Path)
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--create-sprint", action="store_true")
    args = parser.parse_args()
    result = promote_capture(
        args.project_root,
        args.current_capture,
        previous_capture=args.previous_capture,
        top=args.top,
        create_sprint=args.create_sprint,
    )
    print(json.dumps(result, indent=2))
    return 0 if result["promotion_gate"] == "PROMOTED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
