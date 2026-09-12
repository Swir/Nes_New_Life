from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path

from animation_workbench import review_status as animation_review_status
from art_workspace import scan_workspace
from capture_gap_planner import build_capture_queue
from capture_mission_control import mission_status
from final_art_priority import build_priority_rows
from visual_context_audit import review_status as visual_review_status


def _workspace_status(workspace: Path) -> dict:
    if not (workspace / "MASTER_TILES.json").is_file():
        return {"exists": False, "masters": 0, "edited": 0, "todo": 0, "invalid": 0, "percent_edited": 0.0}
    result = scan_workspace(workspace)
    return {"exists": True, **result}


def build_production_status(
    project_root: Path,
    current_capture: Path,
    pack_dir: Path,
    *,
    previous_capture: Path | None = None,
    top: int = 20,
) -> dict:
    root = Path(project_root)
    capture = Path(current_capture)
    pack = Path(pack_dir)
    artwork = root / "Artwork"
    reports = root / "Reports"
    queue = artwork / "ART_QUEUE.csv"
    workspace = artwork / "MasterWorkspace"
    visual_review = artwork / "VISUAL_CONTEXT_REVIEW.csv"
    animation_review = artwork / "ANIMATION_FAMILY_REVIEW.csv"
    capture_manifest = root / "CAPTURE_MISSIONS.json"

    if not (capture / "hires.txt").is_file():
        raise ValueError("Current MesenCE capture is missing hires.txt")
    if not (pack / "hires.txt").is_file():
        raise ValueError("Current production pack is missing hires.txt")

    queue_path = queue if queue.is_file() else None
    capture_gap = build_capture_queue(
        capture,
        queue_path,
        Path(previous_capture) if previous_capture else None,
        queue_path,
        capture_manifest if capture_manifest.is_file() else None,
    )
    capture_state = mission_status(capture_manifest) if capture_manifest.is_file() else {
        "release_capture_gate": "BLOCKED", "done": 0, "total": 0, "percent": 0, "next_missions": []
    }
    visual = visual_review_status(pack, queue_path, visual_review)
    animation = animation_review_status(pack, queue_path, animation_review)
    master = _workspace_status(workspace)

    priority_rows: list[dict] = []
    if queue_path and master["exists"]:
        priority_rows = build_priority_rows(
            pack,
            queue=queue_path,
            workspace=workspace,
            visual_review=visual_review if visual_review.is_file() else None,
            animation_review=animation_review if animation_review.is_file() else None,
        )[: max(1, top)]

    regressions = [row for row in capture_gap.get("queue", []) if row.get("kind") == "CAPTURE_REGRESSION"]
    next_capture = capture_gap.get("queue", [])[:10]
    next_art = priority_rows[:10]

    actions: list[dict] = []
    if regressions:
        actions.append({"priority": 100, "stage": "CAPTURE", "action": f"Resolve {len(regressions)} capture regression(s) before promoting this capture."})
    if capture_state.get("release_capture_gate") != "PASS":
        actions.append({"priority": 95, "stage": "CAPTURE", "action": f"Complete Capture Mission Control ({capture_state.get('done', 0)}/{capture_state.get('total', 0)} verified)."})
    if not queue_path:
        actions.append({"priority": 90, "stage": "ART", "action": "Generate/sync ART_QUEUE.csv from the accepted capture."})
    if not master["exists"]:
        actions.append({"priority": 88, "stage": "ART", "action": "Create/sync MasterWorkspace so captured graphics can be edited safely."})
    elif master.get("invalid", 0):
        actions.append({"priority": 87, "stage": "ART", "action": f"Repair {master['invalid']} INVALID master(s) before further composition."})
    if visual.get("gate") != "PASS":
        actions.append({"priority": 84, "stage": "REVIEW", "action": f"Clear Visual Context Review: {visual.get('pending', 0)} pending, {visual.get('stale', 0)} stale."})
    if animation.get("gate") != "PASS":
        actions.append({"priority": 72, "stage": "REVIEW", "action": f"Inspect Animation Family Review: {animation.get('pending', 0)} pending, {animation.get('stale', 0)} stale."})
    if master["exists"] and master.get("todo", 0):
        actions.append({"priority": 80, "stage": "ART", "action": f"Run the next Final Art Sprint; {master['todo']} master(s) are still TODO."})
    if not actions:
        actions.append({"priority": 50, "stage": "QA", "action": "Captured art/reviews are clear; build the exact pack, deploy playtest, and complete final regression."})

    actions.sort(key=lambda item: -item["priority"])
    return {
        "schema": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "important_note": "This dashboard accelerates local production; it does not claim unseen game states are complete.",
        "capture": capture_state,
        "capture_gap": {
            "summary": capture_gap.get("summary", {}),
            "regressions": len(regressions),
            "next": next_capture,
        },
        "visual_context": visual,
        "animation_family": animation,
        "master_workspace": master,
        "final_art": {"top_count": len(priority_rows), "next": next_art},
        "actions": actions,
        "paths": {
            "project_root": str(root),
            "current_capture": str(capture),
            "pack": str(pack),
            "reports": str(reports),
        },
    }


def write_dashboard(result: dict, output_dir: Path) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "PRODUCTION_SPRINT.json"
    html_path = output_dir / "PRODUCTION_SPRINT.html"
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    action_rows = "".join(
        f"<tr><td>{item['priority']}</td><td>{html.escape(item['stage'])}</td><td>{html.escape(item['action'])}</td></tr>"
        for item in result["actions"]
    )
    capture_rows = "".join(
        f"<tr><td>{row.get('priority', '')}</td><td>{html.escape(str(row.get('kind', '')))}</td><td>{html.escape(str(row.get('label') or row.get('family') or row.get('state') or row.get('mission') or '')))}</td></tr>"
        for row in result["capture_gap"]["next"]
    ) or "<tr><td colspan='3'>No capture-gap rows.</td></tr>"
    art_rows = "".join(
        f"<tr><td>{row.get('priority_score', '')}</td><td>{html.escape(str(row.get('group', '')))}</td><td><code>{html.escape(str(row.get('tile_id') or ''))}</code></td><td>{html.escape(', '.join(row.get('reasons', [])))}</td></tr>"
        for row in result["final_art"]["next"]
    ) or "<tr><td colspan='4'>Priority board unavailable until ART_QUEUE + MasterWorkspace exist.</td></tr>"

    capture = result["capture"]
    master = result["master_workspace"]
    visual = result["visual_context"]
    animation = result["animation_family"]
    document = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'>
<title>Project #002 Production Sprint</title><style>body{{font:15px system-ui;max-width:1250px;margin:30px auto;padding:0 22px;background:#0d1117;color:#e6edf3}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}}.card{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:16px;margin:12px 0}}table{{width:100%;border-collapse:collapse}}th,td{{padding:8px;border-bottom:1px solid #30363d;text-align:left}}code{{color:#79c0ff}}.pass{{color:#3fb950}}.blocked{{color:#f85149}}</style></head><body>
<h1>Tiny Toon Visual Remaster — Production Sprint Control Center</h1><p>{html.escape(result['important_note'])}</p>
<div class='grid'><div class='card'><b>Capture</b><p>{capture.get('done',0)}/{capture.get('total',0)} verified · gate {capture.get('release_capture_gate','BLOCKED')}</p></div><div class='card'><b>Capture regressions</b><p>{result['capture_gap']['regressions']}</p></div><div class='card'><b>Master art</b><p>{master.get('edited',0)}/{master.get('masters',0)} edited · TODO {master.get('todo',0)} · invalid {master.get('invalid',0)}</p></div><div class='card'><b>Visual review</b><p>{visual.get('gate','BLOCKED')} · pending {visual.get('pending',0)} · stale {visual.get('stale',0)}</p></div><div class='card'><b>Animation review</b><p>{animation.get('gate','BLOCKED')} · pending {animation.get('pending',0)} · stale {animation.get('stale',0)}</p></div></div>
<div class='card'><h2>Do this next</h2><table><tr><th>Priority</th><th>Stage</th><th>Action</th></tr>{action_rows}</table></div>
<div class='card'><h2>Capture next</h2><table><tr><th>Priority</th><th>Type</th><th>Target</th></tr>{capture_rows}</table></div>
<div class='card'><h2>Final art next</h2><table><tr><th>Score</th><th>Group</th><th>Tile</th><th>Why now</th></tr>{art_rows}</table></div>
</body></html>"""
    html_path.write_text(document, encoding="utf-8")
    return {"json": str(json_path), "dashboard": str(html_path)}


def build_and_write(project_root: Path, current_capture: Path, pack_dir: Path, output_dir: Path, *, previous_capture: Path | None = None, top: int = 20) -> dict:
    result = build_production_status(project_root, current_capture, pack_dir, previous_capture=previous_capture, top=top)
    result["outputs"] = write_dashboard(result, output_dir)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 unified local production sprint dashboard")
    parser.add_argument("project_root", type=Path)
    parser.add_argument("current_capture", type=Path)
    parser.add_argument("pack", type=Path)
    parser.add_argument("--previous-capture", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--top", type=int, default=20)
    args = parser.parse_args()
    output = args.output or args.project_root / "Reports" / "ProductionSprint"
    result = build_and_write(args.project_root, args.current_capture, args.pack, output, previous_capture=args.previous_capture, top=args.top)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
