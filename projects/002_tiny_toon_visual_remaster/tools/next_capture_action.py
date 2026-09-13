from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "swir.project002.next-capture-action.v1"


def _read_json(path: Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Route Capture Session Plan must be a JSON object")
    return data


def resolve_next_action(route_plan: dict) -> dict:
    sessions = route_plan.get("sessions", [])
    if not isinstance(sessions, list):
        raise ValueError("Route plan sessions must be a list")

    if not sessions:
        return {
            "schema": SCHEMA,
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "status": "NO_CAPTURE_SESSION_PENDING",
            "session": None,
            "next_action": (
                "No route-aware capture session is currently pending. Run Capture Coverage Acceptance; "
                "do not mark Gate A complete unless real local gameplay evidence satisfies every requirement."
            ),
        }

    session = sessions[0]
    if not isinstance(session, dict):
        raise ValueError("Highest-priority route session must be an object")

    gaps = [row for row in session.get("gap_targets", []) if isinstance(row, dict)]
    missions = [row for row in session.get("missions", []) if isinstance(row, dict)]
    regression_count = sum(1 for row in gaps if str(row.get("kind", "")) == "CAPTURE_REGRESSION")

    compact_session = {
        "session_index": int(session.get("session_index", 1) or 1),
        "session_key": str(session.get("session_key", "")),
        "label": str(session.get("label", "")),
        "route_mode": str(session.get("route_mode", "")),
        "score": int(session.get("score", 0) or 0),
        "mission_keys": [str(row.get("key", "")) for row in missions],
        "mission_labels": [str(row.get("label", row.get("key", ""))) for row in missions],
        "gap_targets": [
            {
                "kind": str(row.get("kind", "")),
                "art_group": str(row.get("art_group", "")),
                "family": str(row.get("family", "")),
                "target": str(row.get("target", "")),
                "reason": str(row.get("reason", "")),
            }
            for row in gaps
        ],
        "instructions": [str(value) for value in session.get("instructions", [])],
        "capture_regressions": regression_count,
    }

    urgency = "RECOVER_CAPTURE_REGRESSION" if regression_count else "CAPTURE_HIGHEST_IMPACT_SESSION"
    return {
        "schema": SCHEMA,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": urgency,
        "session": compact_session,
        "next_action": (
            f"Run one fullscreen MesenCE pass for '{compact_session['label']}'. Cover all listed missions/gaps together, "
            "then return to Guided Capture Marathon for explicit VERIFIED_IN_GAME attestations and a fresh gap scan."
        ),
    }


def write_outputs(result: dict, output_dir: Path) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "NEXT_CAPTURE_ACTION.json"
    html_path = output_dir / "NEXT_CAPTURE_ACTION.html"
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    session = result.get("session")
    if session:
        missions = "".join(f"<li>{html.escape(value)}</li>" for value in session["mission_labels"]) or "<li>No unfinished authoritative mission; gap recovery only.</li>"
        gaps = "".join(
            f"<li><b>{html.escape(row['kind'])}/{html.escape(row['art_group'])}</b> — "
            f"{html.escape(row['family'] or row['target'])}: {html.escape(row['reason'])}</li>"
            for row in session["gap_targets"]
        ) or "<li>No additional advisory gap target.</li>"
        instructions = "".join(f"<li>{html.escape(value)}</li>" for value in session["instructions"])
        detail = (
            f"<h2>{html.escape(session['label'])}</h2>"
            f"<p><b>{html.escape(session['route_mode'])}</b> · score {session['score']} · regressions {session['capture_regressions']}</p>"
            f"<h3>Play once — cover together</h3><ul>{instructions}</ul>"
            f"<h3>Authoritative missions</h3><ul>{missions}</ul>"
            f"<h3>Live capture gaps</h3><ul>{gaps}</ul>"
        )
    else:
        detail = "<h2>No capture session pending</h2><p>Run Capture Coverage Acceptance and review real local evidence.</p>"

    html_path.write_text(
        "<!doctype html><html><head><meta charset='utf-8'><title>Project #002 — Next Capture Action</title>"
        "<style>body{font:15px system-ui;max-width:1000px;margin:30px auto;padding:0 20px;background:#0d1117;color:#e6edf3}"
        ".card{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:20px}li{margin:6px 0}.next{color:#79c0ff}</style>"
        "</head><body><section class='card'><h1>Tiny Toon Visual Remaster — Next Capture Action</h1>"
        f"<p>Status: <b>{html.escape(result['status'])}</b></p>{detail}"
        f"<p class='next'><b>DO THIS NEXT:</b> {html.escape(result['next_action'])}</p>"
        "<p>This report is metadata-only. It never changes Capture Mission Control or ROADMAP Gate A–D.</p>"
        "</section></body></html>",
        encoding="utf-8",
    )
    return {"json": str(json_path), "dashboard": str(html_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve the single highest-impact next Project #002 gameplay capture pass")
    parser.add_argument("route_plan", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = resolve_next_action(_read_json(args.route_plan))
    outputs = write_outputs(result, args.output)
    print(json.dumps({"result": result, "outputs": outputs}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
