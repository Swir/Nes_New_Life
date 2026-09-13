from __future__ import annotations

import argparse
import csv
import html
import json
from datetime import datetime, timezone
from pathlib import Path

from capture_mission_control import load_manifest

SCHEMA = "swir.project002.route-capture-sequencer.v1"

# These are workflow bundles, not reconstructed level names. They only group already
# authoritative capture missions into fewer gameplay passes. No bundle can complete a
# mission and no route name claims knowledge that was not observed in the user's game.
SESSION_TEMPLATES = [
    {
        "key": "startup_core_controls",
        "label": "Startup + core player-state sweep",
        "route_mode": "STARTUP_THEN_EARLY_GAMEPLAY",
        "mission_keys": ["boot_title_menu", "player_idle_walk_run"],
        "preferred_groups": ["UI", "PLAYER"],
        "support_groups": ["EFFECTS"],
        "instructions": [
            "Cold boot once and exhaust title/menu animations before entering gameplay.",
            "Immediately exercise core movement states in the first safe gameplay area.",
            "Keep short-lived startup/player effects visible long enough for MesenCE capture.",
        ],
    },
    {
        "key": "primary_route_sweep",
        "label": "Primary route + common-enemy sweep",
        "route_mode": "NORMAL_ROUTE_PASS",
        "mission_keys": ["world_route_1", "common_enemies"],
        "preferred_groups": ["WORLD", "ENEMY"],
        "support_groups": ["PLAYER", "EFFECTS", "UI", "UNASSIGNED"],
        "instructions": [
            "Traverse the normal route continuously instead of restarting for separate world/enemy missions.",
            "At each common enemy, wait for movement/attack/hit/death states before continuing.",
            "Push scrolling boundaries and allow transitions/projectiles to finish visibly.",
        ],
    },
    {
        "key": "alternate_route_sweep",
        "label": "Alternate route + rare-state sweep",
        "route_mode": "ALTERNATE_SECRET_REVISIT_PASS",
        "mission_keys": ["world_route_2", "rare_enemies"],
        "preferred_groups": ["WORLD", "ENEMY"],
        "support_groups": ["PLAYER", "EFFECTS", "UNASSIGNED"],
        "instructions": [
            "Use alternate branches, secrets and revisits as one dedicated pass.",
            "Pause for uncommon enemies/states rather than defeating or leaving immediately.",
            "Prefer contexts that expose unresolved mixed/UNASSIGNED capture families.",
        ],
    },
    {
        "key": "boss_combat_sweep",
        "label": "Boss + player combat/damage sweep",
        "route_mode": "BOSS_AND_COMBAT_PASS",
        "mission_keys": ["bosses_all_phases", "player_actions_damage_death"],
        "preferred_groups": ["BOSS", "PLAYER"],
        "support_groups": ["EFFECTS", "UI"],
        "instructions": [
            "Use boss encounters to trigger player attacks, damage/invulnerability and death/respawn where practical.",
            "Let every boss phase and major attack play before advancing the fight.",
            "Capture boss/projectile/transition effects in the same pass instead of a separate effect-only restart.",
        ],
    },
    {
        "key": "ending_ui_effects_sweep",
        "label": "HUD/result/effects + ending sweep",
        "route_mode": "LATE_GAME_RESULT_ENDING_PASS",
        "mission_keys": ["hud_text_status", "effects_transitions", "ending_credits"],
        "preferred_groups": ["UI", "EFFECTS"],
        "support_groups": ["WORLD", "PLAYER", "BOSS", "ENEMY", "UNASSIGNED"],
        "instructions": [
            "Exercise pause/status/result UI during the late-game pass instead of launching a separate UI-only session.",
            "Allow doors/fades/flashes/projectiles and other short-lived effects to finish visibly.",
            "Finish the game and let ending/credits/post-game states play without skipping.",
        ],
    },
]

SESSION_FIELDS = [
    "session_index",
    "session_key",
    "label",
    "route_mode",
    "score",
    "mission_keys",
    "gap_count",
    "top_gap_targets",
]


def _load_gap_plan(path: Path | None) -> dict:
    if not path or not Path(path).is_file():
        return {"queue": [], "comparison": {"regressions": []}}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Capture Gap Plan must be a JSON object")
    queue = data.get("queue", [])
    if not isinstance(queue, list):
        raise ValueError("Capture Gap Plan queue must be a list")
    return data


def _pending_missions(manifest_path: Path) -> dict[str, dict]:
    manifest = load_manifest(Path(manifest_path))
    return {
        key: value
        for key, value in manifest.get("missions", {}).items()
        if isinstance(value, dict) and not bool(value.get("done", False))
    }


def _gap_signature(row: dict) -> tuple[str, str, str, str]:
    return (
        str(row.get("kind", "")),
        str(row.get("art_group", "")),
        str(row.get("family", "")),
        str(row.get("target", "")),
    )


def _session_affinity(template: dict, row: dict) -> int:
    group = str(row.get("art_group", "")).upper()
    kind = str(row.get("kind", "")).upper()
    target = str(row.get("target", ""))
    mission_keys = set(template["mission_keys"])
    score = 0

    if kind == "MISSION" and target in mission_keys:
        score += 1000
    if group in template["preferred_groups"]:
        score += 200
    elif group in template["support_groups"]:
        score += 80
    if kind == "CAPTURE_REGRESSION":
        score += 300
    elif kind == "CLASSIFICATION_CAPTURE":
        score += 120
    elif kind == "STATE_GAP":
        score += 100

    # Tie-break affinities keep the same family of work in one pass where possible.
    if group == "UI" and template["key"] in {"startup_core_controls", "ending_ui_effects_sweep"}:
        score += 30
    if group == "EFFECTS" and template["key"] in {"boss_combat_sweep", "ending_ui_effects_sweep"}:
        score += 25
    if group == "WORLD" and template["key"] in {"primary_route_sweep", "alternate_route_sweep"}:
        score += 20
    if group == "ENEMY" and template["key"] in {"primary_route_sweep", "alternate_route_sweep"}:
        score += 20
    return score


def build_session_plan(
    manifest_path: Path,
    gap_plan_path: Path | None = None,
    *,
    max_gap_targets_per_session: int = 8,
) -> dict:
    pending = _pending_missions(Path(manifest_path))
    gap_plan = _load_gap_plan(gap_plan_path)
    raw_queue = [row for row in gap_plan.get("queue", []) if isinstance(row, dict)]

    sessions: list[dict] = []
    by_key: dict[str, dict] = {}
    for template in SESSION_TEMPLATES:
        mission_rows = []
        for mission_key in template["mission_keys"]:
            if mission_key not in pending:
                continue
            item = pending[mission_key]
            mission_rows.append({
                "key": mission_key,
                "label": str(item.get("label", mission_key)),
                "group": str(item.get("group", "")),
                "priority": int(item.get("priority", 0)),
            })
        session = {
            "session_key": template["key"],
            "label": template["label"],
            "route_mode": template["route_mode"],
            "instructions": list(template["instructions"]),
            "missions": mission_rows,
            "mission_keys": [row["key"] for row in mission_rows],
            "gap_targets": [],
            "score": sum(row["priority"] for row in mission_rows),
        }
        sessions.append(session)
        by_key[template["key"]] = session

    # Assign each advisory gap exactly once to the highest-affinity gameplay pass.
    seen_gaps: set[tuple[str, str, str, str]] = set()
    template_lookup = {template["key"]: template for template in SESSION_TEMPLATES}
    for row in raw_queue:
        signature = _gap_signature(row)
        if signature in seen_gaps:
            continue
        seen_gaps.add(signature)
        ranked = sorted(
            SESSION_TEMPLATES,
            key=lambda template: (
                -_session_affinity(template, row),
                SESSION_TEMPLATES.index(template),
            ),
        )
        chosen = ranked[0]
        if _session_affinity(chosen, row) <= 0:
            chosen = template_lookup["primary_route_sweep"]
        compact = {
            "kind": str(row.get("kind", "")),
            "art_group": str(row.get("art_group", "")),
            "family": str(row.get("family", "")),
            "target": str(row.get("target", "")),
            "reason": str(row.get("reason", "")),
            "score": int(row.get("score", 0) or 0),
            "missing_expected_states": str(row.get("missing_expected_states", "")),
            "conditions": str(row.get("conditions", "")),
        }
        by_key[chosen["key"]]["gap_targets"].append(compact)
        by_key[chosen["key"]]["score"] += min(200, max(0, compact["score"]))

    # Keep the most important gap targets visible; the underlying Gap Planner still
    # retains the full queue. Never hide regressions behind lower-priority hints.
    for session in sessions:
        session["gap_targets"].sort(
            key=lambda row: (
                0 if row["kind"] == "CAPTURE_REGRESSION" else 1,
                -int(row["score"]),
                row["art_group"],
                row["family"],
            )
        )
        session["gap_targets"] = session["gap_targets"][:max_gap_targets_per_session]
        if any(row["kind"] == "CAPTURE_REGRESSION" for row in session["gap_targets"]):
            session["score"] += 500
        session["reason"] = (
            f"{len(session['missions'])} pending authoritative mission(s) + "
            f"{len(session['gap_targets'])} highest-affinity capture gap(s)"
        )

    active = [session for session in sessions if session["missions"] or session["gap_targets"]]
    # Regression-bearing sessions first, then session score, then stable template order.
    order = {template["key"]: index for index, template in enumerate(SESSION_TEMPLATES)}
    active.sort(
        key=lambda session: (
            0 if any(row["kind"] == "CAPTURE_REGRESSION" for row in session["gap_targets"]) else 1,
            -int(session["score"]),
            order[session["session_key"]],
        )
    )
    for index, session in enumerate(active, 1):
        session["session_index"] = index

    mission_order = [mission["key"] for session in active for mission in session["missions"]]
    missing_pending = sorted(set(pending) - set(mission_order))
    if missing_pending:
        raise RuntimeError("Pending missions missing from sequencer templates: " + ", ".join(missing_pending))
    if len(mission_order) != len(set(mission_order)):
        raise RuntimeError("Sequencer assigned a pending mission more than once")

    return {
        "schema": SCHEMA,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "important_note": (
            "This plan only reduces gameplay restarts by grouping compatible work. "
            "Every mission still requires explicit VERIFIED_IN_GAME attestation and current capture-integrity PASS. "
            "Gap targets are advisory and never create ROADMAP completion."
        ),
        "pending_mission_count": len(pending),
        "planned_session_count": len(active),
        "mission_order": mission_order,
        "sessions": active,
        "capture_regression_present": any(
            row.get("kind") == "CAPTURE_REGRESSION"
            for session in active
            for row in session["gap_targets"]
        ),
    }


def write_outputs(plan: dict, output_dir: Path) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "ROUTE_CAPTURE_SESSION_PLAN.json"
    csv_path = output_dir / "ROUTE_CAPTURE_SESSIONS.csv"
    html_path = output_dir / "ROUTE_CAPTURE_SESSION_PLAN.html"
    json_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SESSION_FIELDS)
        writer.writeheader()
        for session in plan["sessions"]:
            writer.writerow({
                "session_index": session["session_index"],
                "session_key": session["session_key"],
                "label": session["label"],
                "route_mode": session["route_mode"],
                "score": session["score"],
                "mission_keys": " | ".join(session["mission_keys"]),
                "gap_count": len(session["gap_targets"]),
                "top_gap_targets": " | ".join(
                    f"{row['kind']}:{row['art_group']}:{row['family'] or row['target']}"
                    for row in session["gap_targets"]
                ),
            })

    cards = []
    for session in plan["sessions"]:
        missions = "".join(
            f"<li><b>{html.escape(row['group'])}</b> — <code>{html.escape(row['key'])}</code>: {html.escape(row['label'])}</li>"
            for row in session["missions"]
        ) or "<li>No unfinished authoritative mission in this bundle; bundle exists only for current gap recovery.</li>"
        gaps = "".join(
            f"<li><b>{html.escape(row['kind'])}/{html.escape(row['art_group'])}</b> — "
            f"<code>{html.escape(row['family'])}</code> {html.escape(row['target'])}: {html.escape(row['reason'])}</li>"
            for row in session["gap_targets"]
        ) or "<li>No additional advisory gap target.</li>"
        instructions = "".join(f"<li>{html.escape(item)}</li>" for item in session["instructions"])
        cards.append(
            "<section class='card'>"
            f"<h2>Session {session['session_index']}: {html.escape(session['label'])}</h2>"
            f"<p><b>{html.escape(session['route_mode'])}</b> · score {session['score']} · {html.escape(session['reason'])}</p>"
            f"<h3>Play once, cover together</h3><ul>{instructions}</ul>"
            f"<h3>Authoritative missions to verify</h3><ul>{missions}</ul>"
            f"<h3>Live gap targets folded into this pass</h3><ul>{gaps}</ul>"
            "</section>"
        )
    body = "".join(cards) or "<section class='card'><h2>No capture work is currently planned.</h2></section>"
    html_path.write_text(
        "<!doctype html><html><head><meta charset='utf-8'><title>Project #002 Route Capture Session Plan</title>"
        "<style>body{font:15px system-ui;max-width:1100px;margin:30px auto;padding:0 22px;background:#0d1117;color:#e6edf3}"
        ".hero,.card{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:18px;margin:14px 0}"
        "code{color:#79c0ff}li{margin:5px 0}.warn{color:#f2cc60}</style></head><body>"
        f"<section class='hero'><h1>Tiny Toon Visual Remaster — Route Capture Session Sequencer</h1>"
        f"<p><b>{plan['pending_mission_count']}</b> pending mission(s) compressed into <b>{plan['planned_session_count']}</b> gameplay session bundle(s).</p>"
        f"<p class='warn'>{html.escape(plan['important_note'])}</p></section>{body}</body></html>",
        encoding="utf-8",
    )
    return {"json": str(json_path), "csv": str(csv_path), "html": str(html_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 route-aware capture session sequencer")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--gap-plan", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-gap-targets", type=int, default=8)
    args = parser.parse_args()
    plan = build_session_plan(
        args.manifest,
        args.gap_plan,
        max_gap_targets_per_session=max(1, args.max_gap_targets),
    )
    outputs = write_outputs(plan, args.output)
    print(json.dumps({"outputs": outputs, "plan": plan}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
