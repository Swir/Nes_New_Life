from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path

from guided_regression_playtest import build_session
from regression_recovery_session import sync_session
from release_candidate import pack_fingerprint

SCHEMA = "swir.project002.final-regression-auto-continue.v1"


class RegressionAutoContinueError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_plan(manifest: Path, pack: Path, recovery_state: Path) -> dict:
    manifest = Path(manifest)
    pack = Path(pack)
    recovery_state = Path(recovery_state)

    fingerprint = pack_fingerprint(pack)
    if fingerprint == "MISSING_HIRES":
        raise RegressionAutoContinueError("Cannot continue final regression without hires.txt.")

    recovery = sync_session(manifest, pack, recovery_state)
    phase = str(recovery.get("phase") or "")

    if phase == "RETEST_REQUIRED":
        case = recovery.get("failed_case") or {}
        return {
            "schema": SCHEMA,
            "generated_utc": _now(),
            "state": "SAME_CASE_RETEST_REQUIRED",
            "pack_fingerprint": fingerprint,
            "launcher": "Resume_Regression_Recovery.bat",
            "case": case,
            "counts": None,
            "next_action": f"Re-test the remembered failed case {case.get('key')} on the repaired exact build before normal regression ordering resumes.",
            "policy": "A recovery lock always outranks normal regression ordering. No PASS can be inferred automatically.",
        }

    if phase in {"REPAIR_REQUIRED", "BLOCKED"}:
        case = recovery.get("failed_case") or {}
        return {
            "schema": SCHEMA,
            "generated_utc": _now(),
            "state": "RECOVERY_REPAIR_REQUIRED" if phase == "REPAIR_REQUIRED" else "RECOVERY_BLOCKED",
            "pack_fingerprint": fingerprint,
            "launcher": "Resume_Regression_Recovery.bat",
            "case": case,
            "counts": None,
            "next_action": recovery.get("next_action"),
            "policy": "Repair/recovery must complete before another normal regression case is allowed.",
        }

    guided = build_session(manifest, pack)
    if guided.get("pack_fingerprint") != fingerprint:
        raise RegressionAutoContinueError("Runtime fingerprint changed while planning final regression continuation.")

    if guided.get("state") == "REGRESSION_COMPLETE":
        return {
            "schema": SCHEMA,
            "generated_utc": _now(),
            "state": "REGRESSION_COMPLETE",
            "pack_fingerprint": fingerprint,
            "launcher": "Final_Release_Gate.bat",
            "case": None,
            "counts": guided.get("counts"),
            "next_action": "All ten authoritative cases PASS on this exact fingerprint. Run the Final Release Gate.",
            "policy": "Completion is accepted only from ten explicit current-build PASS records.",
        }

    case = guided.get("next_case") or {}
    if case.get("prior_state") == "FAIL":
        raise RegressionAutoContinueError("A current-build FAIL escaped recovery-session routing; refusing to continue normal regression ordering.")

    return {
        "schema": SCHEMA,
        "generated_utc": _now(),
        "state": "PLAYTEST_CASE_REQUIRED",
        "pack_fingerprint": fingerprint,
        "launcher": "Guided_Regression_Playtest.bat",
        "case": case,
        "counts": guided.get("counts"),
        "next_action": f"Run case {case.get('order')}/10 ({case.get('key')}) in verified-fullscreen MesenCE and explicitly record PASS or FAIL. A PASS immediately advances this director to the next authoritative case.",
        "policy": "The director can sequence cases, but every PASS/FAIL remains a real human observation from the exact current build.",
    }


def write_outputs(plan: dict, output_dir: Path) -> dict:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "FINAL_REGRESSION_AUTO_CONTINUE.json"
    html_path = output / "FINAL_REGRESSION_AUTO_CONTINUE.html"
    json_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    case = plan.get("case") or {}
    counts = plan.get("counts") or {}
    cues = "".join(f"<li>{html.escape(str(item))}</li>" for item in case.get("cues", []))
    html_path.write_text(
        "<!doctype html><html><head><meta charset='utf-8'><title>Final Regression Auto-Continue</title>"
        "<style>body{font:15px system-ui;max-width:1050px;margin:30px auto;padding:0 22px;background:#0d1117;color:#e6edf3}.card{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:18px;margin:14px 0}code{color:#79c0ff}.warn{color:#f2cc60}</style></head><body>"
        "<h1>Project #002 — Final Regression Auto-Continue Director</h1>"
        f"<div class='card'><h2>{html.escape(str(plan.get('state') or ''))}</h2><p>Fingerprint: <code>{html.escape(str(plan.get('pack_fingerprint') or ''))}</code></p><p>Case: <code>{html.escape(str(case.get('key') or ''))}</code> — {html.escape(str(case.get('label') or ''))}</p><p>PASS {counts.get('PASS','—')} · FAIL {counts.get('FAIL','—')} · STALE {counts.get('STALE','—')} · PENDING {counts.get('PENDING','—')}</p></div>"
        f"<div class='card'><h2>DO THIS NEXT</h2><p>{html.escape(str(plan.get('next_action') or ''))}</p><ul>{cues}</ul><p class='warn'>{html.escape(str(plan.get('policy') or ''))}</p></div>"
        "</body></html>",
        encoding="utf-8",
    )
    return {"json": str(json_path), "dashboard": str(html_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 final regression auto-continue director")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("pack", type=Path)
    parser.add_argument("recovery_state", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    plan = build_plan(args.manifest, args.pack, args.recovery_state)
    plan["outputs"] = write_outputs(plan, args.output)
    print(json.dumps(plan, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
