from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path

from capture_coverage_acceptance import build_acceptance_manifest
from capture_gap_planner import build_capture_queue, write_outputs as write_gap_outputs
from final_regression_cockpit import cockpit_status
from release_candidate import pack_fingerprint
from route_capture_sequencer import build_session_plan, write_outputs as write_route_outputs

SCHEMA = "swir.project002.regression-capture-gap-recovery.v1"
TOKEN_SCHEMA = "swir.project002.regression-capture-gap-token.v1"

CASE_MISSIONS = {
    "boot_title_menu": ("boot_title_menu",),
    "player_movement": ("player_idle_walk_run",),
    "player_actions_damage_death": ("player_actions_damage_death",),
    "world_route_1": ("world_route_1", "common_enemies"),
    "world_route_2": ("world_route_2", "rare_enemies"),
    "enemies": ("common_enemies", "rare_enemies"),
    "bosses": ("bosses_all_phases",),
    "hud_text_status": ("hud_text_status",),
    "effects_transitions": ("effects_transitions",),
    "ending_credits": ("ending_credits",),
}

CASE_GROUPS = {
    "boot_title_menu": ("UI",),
    "player_movement": ("PLAYER",),
    "player_actions_damage_death": ("PLAYER", "EFFECTS"),
    "world_route_1": ("WORLD", "ENEMY"),
    "world_route_2": ("WORLD", "ENEMY"),
    "enemies": ("ENEMY",),
    "bosses": ("BOSS", "EFFECTS"),
    "hud_text_status": ("UI",),
    "effects_transitions": ("EFFECTS",),
    "ending_credits": ("UI", "WORLD"),
}


class CaptureGapRecoveryError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> dict:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CaptureGapRecoveryError(f"Missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CaptureGapRecoveryError(f"Invalid JSON: {path}") from exc
    if not isinstance(data, dict):
        raise CaptureGapRecoveryError(f"Expected JSON object: {path}")
    return data


def _require_capture_gap_failure(project_root: Path, runtime_pack: Path) -> tuple[dict, dict]:
    manifest = Path(project_root) / "FINAL_REGRESSION.json"
    status = cockpit_status(manifest, Path(runtime_pack))
    case = status.get("next_case")
    if not case or case.get("state") != "FAIL":
        raise CaptureGapRecoveryError("No authoritative current-build regression FAIL is waiting for recovery.")
    if str(case.get("failure_category") or "").upper() != "CAPTURE_GAP":
        raise CaptureGapRecoveryError(
            f"Current FAIL is {case.get('failure_category') or 'unclassified'}, not CAPTURE_GAP; use the normal regression repair route."
        )
    key = str(case.get("key") or "")
    if key not in CASE_MISSIONS:
        raise CaptureGapRecoveryError(f"Unsupported regression case for capture recovery: {key}")
    return status, case


def _choose_session(route_plan: dict, case_key: str) -> dict | None:
    sessions = [row for row in route_plan.get("sessions", []) if isinstance(row, dict)]
    if not sessions:
        return None
    missions = set(CASE_MISSIONS.get(case_key, ()))
    groups = set(CASE_GROUPS.get(case_key, ()))
    ranked: list[tuple[int, int, dict]] = []
    for order, session in enumerate(sessions):
        session_missions = {
            str(row.get("key") or "")
            for row in session.get("missions", [])
            if isinstance(row, dict)
        }
        session_groups = {
            str(row.get("art_group") or "").upper()
            for row in session.get("gap_targets", [])
            if isinstance(row, dict)
        }
        score = len(missions & session_missions) * 1000 + len(groups & session_groups) * 200
        if any(str(row.get("kind") or "") == "CAPTURE_REGRESSION" for row in session.get("gap_targets", []) if isinstance(row, dict)):
            score += 300
        score += int(session.get("score", 0) or 0)
        ranked.append((score, -order, session))
    ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return ranked[0][2]


def _compact_session(session: dict | None) -> dict | None:
    if not session:
        return None
    return {
        "session_key": str(session.get("session_key") or ""),
        "label": str(session.get("label") or ""),
        "route_mode": str(session.get("route_mode") or ""),
        "instructions": [str(value) for value in session.get("instructions", [])],
        "mission_keys": [str(row.get("key") or "") for row in session.get("missions", []) if isinstance(row, dict)],
        "gap_targets": [
            {
                "kind": str(row.get("kind") or ""),
                "art_group": str(row.get("art_group") or ""),
                "family": str(row.get("family") or ""),
                "target": str(row.get("target") or ""),
                "reason": str(row.get("reason") or ""),
            }
            for row in session.get("gap_targets", [])
            if isinstance(row, dict)
        ],
    }


def _mission_snapshot(acceptance: dict, mission_keys: tuple[str, ...]) -> list[dict]:
    wanted = set(mission_keys)
    return [
        {
            "key": str(row.get("key") or ""),
            "label": str(row.get("label") or ""),
            "group": str(row.get("group") or ""),
            "status": str(row.get("status") or ""),
            "same_as_current_capture": bool(row.get("same_as_current_capture", False)),
        }
        for row in acceptance.get("missions", [])
        if isinstance(row, dict) and str(row.get("key") or "") in wanted
    ]


def plan_recovery(
    project_root: Path,
    runtime_pack: Path,
    current_capture: Path,
    *,
    previous_capture: Path | None = None,
    output_dir: Path | None = None,
) -> dict:
    root = Path(project_root)
    runtime = Path(runtime_pack)
    capture = Path(current_capture)
    status, case = _require_capture_gap_failure(root, runtime)
    case_key = str(case["key"])
    mission_keys = CASE_MISSIONS[case_key]

    acceptance = build_acceptance_manifest(root, capture, previous_capture=previous_capture)
    art_queue = root / "Artwork" / "ART_QUEUE.csv"
    gap_plan = build_capture_queue(
        capture,
        art_queue if art_queue.is_file() else None,
        previous_capture,
        art_queue if previous_capture and art_queue.is_file() else None,
        root / "CAPTURE_MISSIONS.json",
    )

    out = Path(output_dir) if output_dir else root / "Reports" / "RegressionCaptureGapRecovery"
    gap_dir = out / "gap"
    route_dir = out / "route"
    gap_outputs = write_gap_outputs(gap_plan, gap_dir)
    route_plan = build_session_plan(root / "CAPTURE_MISSIONS.json", Path(gap_outputs["json"]))
    route_outputs = write_route_outputs(route_plan, route_dir)
    preferred = _choose_session(route_plan, case_key)

    source_counts = dict(acceptance.get("source_counts") or {})
    token = {
        "schema": TOKEN_SCHEMA,
        "generated_utc": _now(),
        "case_key": case_key,
        "case_label": str(case.get("label") or case_key),
        "failure_category": "CAPTURE_GAP",
        "failure_notes": str(case.get("failure_notes") or ""),
        "source_runtime_fingerprint": str(status.get("pack_fingerprint") or pack_fingerprint(runtime)),
        "source_capture_fingerprint": str(acceptance.get("capture_fingerprint_sha256") or ""),
        "target_mission_keys": list(mission_keys),
        "target_groups": list(CASE_GROUPS.get(case_key, ())),
        "preferred_session_key": str((preferred or {}).get("session_key") or ""),
        "source_counts": source_counts,
    }
    token_path = out / "REGRESSION_CAPTURE_GAP_TOKEN.json"
    out.mkdir(parents=True, exist_ok=True)
    token_path.write_text(json.dumps(token, indent=2), encoding="utf-8")

    target_missions = _mission_snapshot(acceptance, mission_keys)
    result = {
        "schema": SCHEMA,
        "generated_utc": _now(),
        "status": "CAPTURE_GAP_RECOVERY_PLANNED",
        "runtime_fingerprint": token["source_runtime_fingerprint"],
        "capture_fingerprint": token["source_capture_fingerprint"],
        "failed_case": {
            "key": case_key,
            "label": token["case_label"],
            "failure_notes": token["failure_notes"],
        },
        "target_missions": target_missions,
        "preferred_session": _compact_session(preferred),
        "token": "REGRESSION_CAPTURE_GAP_TOKEN.json",
        "gap_plan": {"queue_items": len(gap_plan.get("queue", [])), "outputs": gap_outputs},
        "route_plan": {"planned_sessions": int(route_plan.get("planned_session_count", 0) or 0), "outputs": route_outputs},
        "next_action": (
            "Run the preferred route-aware Guided Capture Marathon session against the local ROM, explicitly verify the listed mission(s), "
            "then verify the refreshed capture before sending it through the evidence-bound HD art handoff."
        ),
        "roadmap_policy": "This recovery plan never auto-passes regression, capture missions or ROADMAP Gate A-D.",
        "privacy_contract": {"metadata_only": True, "absolute_local_paths": False, "capture_pixels": False, "rom_bytes": False},
    }
    return _write_outputs(result, out)


def verify_recovery(
    project_root: Path,
    current_capture: Path,
    token_path: Path,
    *,
    previous_capture: Path | None = None,
    output_dir: Path | None = None,
) -> dict:
    root = Path(project_root)
    capture = Path(current_capture)
    token = _read_json(Path(token_path))
    if token.get("schema") != TOKEN_SCHEMA:
        raise CaptureGapRecoveryError("Invalid capture-gap recovery token schema.")

    acceptance = build_acceptance_manifest(root, capture, previous_capture=previous_capture)
    current_fp = str(acceptance.get("capture_fingerprint_sha256") or "")
    source_fp = str(token.get("source_capture_fingerprint") or "")
    blockers: list[str] = []

    if not current_fp:
        blockers.append("Current capture fingerprint is missing.")
    elif current_fp == source_fp:
        blockers.append("Capture fingerprint did not change; the failed regression gap has not been demonstrably refreshed.")

    integrity = acceptance.get("capture_integrity") or {}
    if integrity.get("admission_gate") != "PASS":
        blockers.append("Capture Integrity admission is not PASS.")
    if int(integrity.get("regression_count", 0) or 0) > 0:
        blockers.append("The refreshed capture contains CAPTURE_REGRESSION and cannot replace the failed source capture.")
    if integrity.get("structural_blockers"):
        blockers.append("The refreshed capture has structural blockers.")

    mission_keys = tuple(str(value) for value in token.get("target_mission_keys", []) if value)
    mission_rows = _mission_snapshot(acceptance, mission_keys)
    indexed = {row["key"]: row for row in mission_rows}
    missing = [key for key in mission_keys if key not in indexed]
    unverified = [key for key in mission_keys if key in indexed and indexed[key]["status"] != "VERIFIED_IN_GAME"]
    stale = [key for key in mission_keys if key in indexed and not indexed[key]["same_as_current_capture"]]
    if missing:
        blockers.append("Target capture mission(s) are missing from current acceptance evidence: " + ", ".join(missing))
    if unverified:
        blockers.append("Target capture mission(s) are not VERIFIED_IN_GAME: " + ", ".join(unverified))
    if stale:
        blockers.append("Target capture mission provenance is not bound to the refreshed capture: " + ", ".join(stale))

    source_counts = token.get("source_counts") or {}
    current_counts = acceptance.get("source_counts") or {}
    deltas = {
        key: int(current_counts.get(key, 0) or 0) - int(source_counts.get(key, 0) or 0)
        for key in {"mapping_count", "unique_tile_ids", "unique_palettes", "condition_count", "referenced_images"}
    }

    status = "CAPTURE_RECOVERED_READY_FOR_HD_HANDOFF" if not blockers else "CAPTURE_RECOVERY_BLOCKED"
    result = {
        "schema": SCHEMA,
        "generated_utc": _now(),
        "status": status,
        "case_key": str(token.get("case_key") or ""),
        "case_label": str(token.get("case_label") or ""),
        "source_capture_fingerprint": source_fp,
        "current_capture_fingerprint": current_fp,
        "target_missions": mission_rows,
        "capture_deltas": deltas,
        "blockers": blockers,
        "next_action": (
            "Run Evidence_Bound_Art_Handoff.bat on this refreshed capture, complete the exact new/affected 4x art through transactional QA, then re-run the SAME regression case."
            if not blockers
            else "Resolve the listed capture blocker(s) and repeat only the targeted route-aware capture session before touching art or regression evidence."
        ),
        "roadmap_policy": "Capture recovery readiness is not a PASS. The same regression case still requires real verified-fullscreen MesenCE re-test on the repaired runtime fingerprint.",
        "privacy_contract": {"metadata_only": True, "absolute_local_paths": False, "capture_pixels": False, "rom_bytes": False},
    }
    out = Path(output_dir) if output_dir else root / "Reports" / "RegressionCaptureGapRecovery"
    return _write_outputs(result, out)


def _write_outputs(result: dict, output_dir: Path) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "REGRESSION_CAPTURE_GAP_RECOVERY.json"
    html_path = output_dir / "REGRESSION_CAPTURE_GAP_RECOVERY.html"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    preferred = result.get("preferred_session") or {}
    mission_rows = result.get("target_missions") or []
    missions_html = "".join(
        f"<li><code>{html.escape(str(row.get('key') or ''))}</code> — {html.escape(str(row.get('label') or ''))} · {html.escape(str(row.get('status') or ''))}</li>"
        for row in mission_rows
    ) or "<li>No target mission metadata available.</li>"
    blockers_html = "".join(f"<li>{html.escape(str(item))}</li>" for item in result.get("blockers", [])) or "<li>None.</li>"
    session_html = (
        f"<p><b>{html.escape(str(preferred.get('label') or ''))}</b> · <code>{html.escape(str(preferred.get('session_key') or ''))}</code> · {html.escape(str(preferred.get('route_mode') or ''))}</p>"
        if preferred else "<p>No route session is currently available; refresh Capture Gap Planner / Route Sequencer.</p>"
    )
    html_path.write_text(
        "<!doctype html><html><head><meta charset='utf-8'><title>Project #002 Regression Capture Gap Recovery</title>"
        "<style>body{font:15px system-ui;max-width:1050px;margin:30px auto;padding:0 22px;background:#0d1117;color:#e6edf3}.card{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:18px;margin:14px 0}code{color:#79c0ff}.warn{color:#f2cc60}</style>"
        "</head><body><h1>Tiny Toon Visual Remaster — Regression Capture Gap Recovery</h1>"
        f"<div class='card'><h2>{html.escape(str(result.get('status') or ''))}</h2><p>Case: <code>{html.escape(str(result.get('case_key') or (result.get('failed_case') or {}).get('key') or ''))}</code></p><p class='warn'>{html.escape(str(result.get('roadmap_policy') or ''))}</p></div>"
        f"<div class='card'><h2>Target capture missions</h2><ul>{missions_html}</ul><h3>Preferred route session</h3>{session_html}</div>"
        f"<div class='card'><h2>Blockers</h2><ul>{blockers_html}</ul><h2>DO THIS NEXT</h2><p>{html.escape(str(result.get('next_action') or ''))}</p></div>"
        "</body></html>",
        encoding="utf-8",
    )
    wrapped = dict(result)
    wrapped["outputs"] = {"json": str(json_path), "dashboard": str(html_path)}
    return wrapped


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 regression CAPTURE_GAP recovery director")
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan")
    plan.add_argument("project_root", type=Path)
    plan.add_argument("runtime_pack", type=Path)
    plan.add_argument("current_capture", type=Path)
    plan.add_argument("--previous-capture", type=Path)
    plan.add_argument("--output", type=Path)

    verify = sub.add_parser("verify")
    verify.add_argument("project_root", type=Path)
    verify.add_argument("current_capture", type=Path)
    verify.add_argument("token", type=Path)
    verify.add_argument("--previous-capture", type=Path)
    verify.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.command == "plan":
        result = plan_recovery(
            args.project_root,
            args.runtime_pack,
            args.current_capture,
            previous_capture=args.previous_capture,
            output_dir=args.output,
        )
    else:
        result = verify_recovery(
            args.project_root,
            args.current_capture,
            args.token,
            previous_capture=args.previous_capture,
            output_dir=args.output,
        )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("status") != "CAPTURE_RECOVERY_BLOCKED" else 3


if __name__ == "__main__":
    raise SystemExit(main())
