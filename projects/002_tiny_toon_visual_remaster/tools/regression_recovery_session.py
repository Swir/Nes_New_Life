from __future__ import annotations

import argparse
import hashlib
import html
import json
from datetime import datetime, timezone
from pathlib import Path

from final_regression_cockpit import FAILURE_CATEGORIES, cockpit_status, record_case_result
from guided_regression_playtest import CASE_GUIDANCE
from regression_failure_router import ART_CATEGORIES, ROUTES
from release_candidate import pack_fingerprint

SCHEMA = "swir.project002.regression-recovery-session.v1"
ACTIVE_PHASES = {"REPAIR_REQUIRED", "RETEST_REQUIRED", "BLOCKED"}


class RegressionRecoverySessionError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load(path: Path) -> dict | None:
    path = Path(path)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegressionRecoverySessionError(f"Invalid recovery session state: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise RegressionRecoverySessionError("Unsupported regression recovery session schema.")
    return data


def _atomic_write(path: Path, data: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(path)


def _route_for_category(category: str) -> dict:
    category = str(category or "OTHER").upper()
    if category in ART_CATEGORIES:
        return {
            "state": "ROUTE_ART_REPAIR",
            "launcher": "Regression_Repair_Loop.bat",
            "reason": "The remembered FAIL belongs to the transactional art/family repair path.",
        }
    route = ROUTES.get(category)
    if not route:
        raise RegressionRecoverySessionError(f"Unsupported recovery failure category: {category}")
    return dict(route)


def _history_append(state: dict, event: str, **details: object) -> None:
    history = state.setdefault("history", [])
    history.append({"utc": _now(), "event": event, **details})
    if len(history) > 100:
        del history[:-100]


def _find_case(status: dict, case_key: str) -> dict | None:
    return next((row for row in status.get("cases", []) if row.get("key") == case_key), None)


def _new_session(failed_case: dict, current_fp: str) -> dict:
    category = str(failed_case.get("failure_category") or "OTHER").upper()
    route = _route_for_category(category)
    created = _now()
    seed = f"{failed_case.get('key')}|{current_fp}|{created}".encode("utf-8")
    state = {
        "schema": SCHEMA,
        "session_id": hashlib.sha256(seed).hexdigest()[:20],
        "created_utc": created,
        "updated_utc": created,
        "phase": "REPAIR_REQUIRED",
        "failed_case": {
            "order": failed_case.get("order"),
            "key": failed_case.get("key"),
            "label": failed_case.get("label"),
            "category": category,
            "failure_notes": str(failed_case.get("failure_notes") or ""),
        },
        "source_fingerprint": current_fp,
        "current_fingerprint": current_fp,
        "route_state": route["state"],
        "route_launcher": route["launcher"],
        "next_action": f"Repair the remembered {failed_case.get('key')} FAIL through {route['launcher']}. After the runtime fingerprint changes, this session will require a same-case retest before normal regression ordering resumes.",
        "history": [],
        "policy": "A remembered FAIL remains authoritative across process restarts. Runtime fingerprint drift after repair routes to the same-case retest and never auto-PASSes evidence.",
    }
    _history_append(state, "SESSION_STARTED", phase="REPAIR_REQUIRED", fingerprint=current_fp, case=failed_case.get("key"), category=category)
    return state


def sync_session(manifest: Path, pack: Path, state_path: Path) -> dict:
    manifest = Path(manifest)
    pack = Path(pack)
    state_path = Path(state_path)
    status = cockpit_status(manifest, pack)
    current_fp = pack_fingerprint(pack)
    if current_fp == "MISSING_HIRES":
        raise RegressionRecoverySessionError("Cannot recover regression without hires.txt.")
    if status.get("pack_fingerprint") != current_fp:
        raise RegressionRecoverySessionError("Runtime fingerprint changed while synchronizing recovery state.")

    state = _load(state_path)
    if state and state.get("phase") in ACTIVE_PHASES:
        failed = state.get("failed_case") or {}
        key = str(failed.get("key") or "")
        row = _find_case(status, key)
        if not row:
            raise RegressionRecoverySessionError(f"Remembered regression case no longer exists: {key}")

        previous_phase = str(state.get("phase") or "")
        previous_fp = str(state.get("current_fingerprint") or "")
        source_fp = str(state.get("source_fingerprint") or "")
        row_state = str(row.get("state") or "")
        row_recorded_fp = str(row.get("pack_fingerprint") or "")

        if row_state == "PASS" and row_recorded_fp == current_fp:
            state["phase"] = "COMPLETE"
            state["route_state"] = "ROUTE_CURRENT_REGRESSION"
            state["route_launcher"] = "Regression_Failure_Router.bat"
            state["next_action"] = "The remembered failed case now PASSes on the current fingerprint. Return to the unified regression router for the next authoritative case."
        elif row_state == "FAIL" and row_recorded_fp == current_fp:
            category = str(row.get("failure_category") or "OTHER").upper()
            route = _route_for_category(category)
            if current_fp != source_fp or category != str(failed.get("category") or ""):
                state["source_fingerprint"] = current_fp
                state["failed_case"] = {
                    "order": row.get("order"),
                    "key": row.get("key"),
                    "label": row.get("label"),
                    "category": category,
                    "failure_notes": str(row.get("failure_notes") or ""),
                }
                _history_append(state, "RETEST_FAILED", fingerprint=current_fp, case=key, category=category)
            state["phase"] = "REPAIR_REQUIRED"
            state["route_state"] = route["state"]
            state["route_launcher"] = route["launcher"]
            state["next_action"] = f"The remembered case still FAILs on this exact runtime. Repair it through {route['launcher']} before retesting."
        elif current_fp != source_fp:
            state["phase"] = "RETEST_REQUIRED"
            state["route_state"] = "ROUTE_SAME_CASE_RETEST"
            state["route_launcher"] = "Resume_Regression_Recovery.bat"
            state["next_action"] = f"Runtime changed after repair. Re-test ONLY the remembered case {key} on fingerprint {current_fp}; do not resume normal case ordering first."
        else:
            state["phase"] = "BLOCKED"
            state["route_state"] = "RECOVERY_STATE_CONFLICT"
            state["route_launcher"] = "Resume_Regression_Recovery.bat"
            state["next_action"] = "The remembered FAIL changed state without a runtime fingerprint change. Inspect FINAL_REGRESSION.json before continuing; no evidence was cleared automatically."

        state["current_fingerprint"] = current_fp
        state["updated_utc"] = _now()
        if state["phase"] != previous_phase or current_fp != previous_fp:
            _history_append(state, "SESSION_SYNC", phase=state["phase"], fingerprint=current_fp, case=key)
        _atomic_write(state_path, state)
        return state

    failed_case = next((row for row in status.get("cases", []) if row.get("state") == "FAIL"), None)
    if failed_case:
        state = _new_session(failed_case, current_fp)
        _atomic_write(state_path, state)
        return state

    if state and state.get("phase") == "COMPLETE":
        return state

    return {
        "schema": SCHEMA,
        "phase": "NO_ACTIVE_RECOVERY",
        "current_fingerprint": current_fp,
        "failed_case": None,
        "route_state": "ROUTE_CURRENT_REGRESSION",
        "route_launcher": "Regression_Failure_Router.bat",
        "next_action": "No remembered regression repair is active. Continue through the unified regression router.",
        "history": [],
        "policy": "No regression evidence is created or cleared by recovery-session synchronization.",
    }


def plan_retest(manifest: Path, pack: Path, state_path: Path) -> dict:
    state = sync_session(manifest, pack, state_path)
    if state.get("phase") != "RETEST_REQUIRED":
        raise RegressionRecoverySessionError(f"Same-case retest is not ready; recovery phase is {state.get('phase')}.")
    case = state["failed_case"]
    guide = CASE_GUIDANCE.get(case["key"])
    if not guide:
        raise RegressionRecoverySessionError(f"No guided regression route for remembered case: {case['key']}")
    return {
        "schema": SCHEMA,
        "session_id": state["session_id"],
        "phase": state["phase"],
        "planned_fingerprint": state["current_fingerprint"],
        "source_fingerprint": state["source_fingerprint"],
        "case": {
            "order": case.get("order"),
            "key": case["key"],
            "label": case.get("label"),
            "previous_category": case.get("category"),
            "previous_failure_notes": case.get("failure_notes", ""),
            "route": guide["route"],
            "cues": guide["cues"],
        },
        "next_action": "Launch this exact repaired fingerprint in verified fullscreen MesenCE, perform only the remembered case, then explicitly record PASS or FAIL.",
        "policy": "The retest is pinned to one remembered failed case and one repaired fingerprint. It cannot auto-PASS or skip to another case.",
    }


def record_retest(
    manifest: Path,
    pack: Path,
    state_path: Path,
    result: str,
    *,
    category: str = "OTHER",
    notes: str = "",
    failure_notes: str = "",
) -> dict:
    plan = plan_retest(manifest, pack, state_path)
    expected_fp = plan["planned_fingerprint"]
    actual_fp = pack_fingerprint(Path(pack))
    if actual_fp != expected_fp:
        raise RegressionRecoverySessionError("Runtime fingerprint changed after same-case retest planning; discard the observation and plan again.")
    result = result.strip().upper()
    if result not in {"PASS", "FAIL"}:
        raise RegressionRecoverySessionError("Retest result must be PASS or FAIL.")
    category = category.strip().upper() or "OTHER"
    if result == "FAIL" and category not in FAILURE_CATEGORIES:
        raise RegressionRecoverySessionError("Unknown failure category: " + category)
    evidence = record_case_result(
        Path(manifest),
        plan["case"]["key"],
        Path(pack),
        result,
        notes=notes,
        failure_category=category,
        failure_notes=failure_notes,
    )
    state = sync_session(manifest, pack, state_path)
    return {"recorded": evidence, "recovery": state}


def write_outputs(result: dict, output_dir: Path) -> dict:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "REGRESSION_RECOVERY_SESSION.json"
    html_path = output / "REGRESSION_RECOVERY_SESSION.html"
    safe = dict(result)
    safe.pop("history", None)
    json_path.write_text(json.dumps(safe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    case = result.get("failed_case") or result.get("case") or {}
    if "case" in result and isinstance(result.get("case"), dict):
        case = result["case"]
    cues = "".join(f"<li>{html.escape(str(item))}</li>" for item in case.get("cues", []))
    html_path.write_text(
        "<!doctype html><html><head><meta charset='utf-8'><title>Regression Recovery Session</title>"
        "<style>body{font:15px system-ui;max-width:1000px;margin:30px auto;padding:0 22px;background:#0d1117;color:#e6edf3}.card{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:18px;margin:14px 0}code{color:#79c0ff}.warn{color:#f2cc60}</style></head><body>"
        "<h1>Project #002 — Regression Recovery Session</h1>"
        f"<div class='card'><h2>{html.escape(str(result.get('phase') or ''))}</h2><p>Case: <code>{html.escape(str(case.get('key') or ''))}</code> — {html.escape(str(case.get('label') or ''))}</p><p>Current fingerprint: <code>{html.escape(str(result.get('current_fingerprint') or result.get('planned_fingerprint') or ''))}</code></p></div>"
        f"<div class='card'><p>{html.escape(str(result.get('next_action') or ''))}</p><ul>{cues}</ul><p class='warn'>{html.escape(str(result.get('policy') or ''))}</p></div>"
        "</body></html>",
        encoding="utf-8",
    )
    return {"json": str(json_path), "dashboard": str(html_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Persistent exact-build regression recovery session")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("sync", "plan-retest"):
        cmd = sub.add_parser(name)
        cmd.add_argument("manifest", type=Path)
        cmd.add_argument("pack", type=Path)
        cmd.add_argument("state", type=Path)
        cmd.add_argument("--output", type=Path, required=True)
    rec = sub.add_parser("record")
    rec.add_argument("manifest", type=Path)
    rec.add_argument("pack", type=Path)
    rec.add_argument("state", type=Path)
    rec.add_argument("result", choices=("PASS", "FAIL"))
    rec.add_argument("--category", choices=FAILURE_CATEGORIES, default="OTHER")
    rec.add_argument("--notes", default="")
    rec.add_argument("--failure-notes", default="")
    rec.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "sync":
        result = sync_session(args.manifest, args.pack, args.state)
    elif args.command == "plan-retest":
        result = plan_retest(args.manifest, args.pack, args.state)
    else:
        result = record_retest(args.manifest, args.pack, args.state, args.result, category=args.category, notes=args.notes, failure_notes=args.failure_notes)
        if "recovery" in result:
            display = result["recovery"]
            display["recorded"] = result["recorded"]
            result = display
    result["outputs"] = write_outputs(result, args.output)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
