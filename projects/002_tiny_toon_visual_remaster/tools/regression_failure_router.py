from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path

from final_regression_cockpit import cockpit_status

SCHEMA = "swir.project002.regression-failure-router.v1"

ART_CATEGORIES = {"MISSING_HD", "WRONG_PALETTE", "ANIMATION_SEAM", "TRANSPARENCY", "OTHER"}
ROUTES = {
    "CAPTURE_GAP": {
        "state": "ROUTE_CAPTURE_GAP_RECOVERY",
        "launcher": "Regression_Capture_Gap_Recovery.bat",
        "reason": "Missing real gameplay/capture coverage must be recovered before art can be trusted.",
    },
    "MAPPING": {
        "state": "ROUTE_MAPPING_REPAIR",
        "launcher": "Regression_Mapping_Repair.bat",
        "reason": "hires.txt mapping/provenance defects must be diagnosed directly instead of hidden with replacement art.",
    },
    "SCALE_OR_FILTER": {
        "state": "ROUTE_RUNTIME_REPAIR",
        "launcher": "Build_HD_Playtest.bat",
        "reason": "4x/fullscreen/filter presentation must be repaired and revalidated before visual regression can continue.",
    },
}


class RegressionFailureRouterError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_route(project_root: Path, runtime_pack: Path) -> dict:
    root = Path(project_root)
    status = cockpit_status(root / "FINAL_REGRESSION.json", Path(runtime_pack))
    case = status.get("next_case")

    if status.get("gate") == "PASS" or case is None:
        return {
            "schema": SCHEMA,
            "generated_utc": _now(),
            "state": "REGRESSION_COMPLETE",
            "launcher": "Final_Release_Gate.bat",
            "pack_fingerprint": status.get("pack_fingerprint"),
            "counts": status.get("counts"),
            "failed_case": None,
            "next_action": "All ten authoritative regression cases PASS for this exact runtime fingerprint. Continue to Final Release Gate.",
            "roadmap_policy": "Tool routing does not change ROADMAP Gate A-D.",
        }

    if case.get("state") != "FAIL":
        return {
            "schema": SCHEMA,
            "generated_utc": _now(),
            "state": "ROUTE_GUIDED_REGRESSION",
            "launcher": "Guided_Regression_Playtest.bat",
            "pack_fingerprint": status.get("pack_fingerprint"),
            "counts": status.get("counts"),
            "failed_case": None,
            "next_case": {"key": case.get("key"), "label": case.get("label"), "state": case.get("state")},
            "next_action": "No current-build FAIL is blocking. Continue the authoritative guided exact-build regression case.",
            "roadmap_policy": "No regression case can auto-PASS.",
        }

    category = str(case.get("failure_category") or "OTHER").upper()
    if category in ART_CATEGORIES:
        route = {
            "state": "ROUTE_ART_REPAIR",
            "launcher": "Regression_Repair_Loop.bat",
            "reason": "The observed defect belongs to the transactional art/family repair path.",
        }
    else:
        route = ROUTES.get(category)
    if not route:
        raise RegressionFailureRouterError(f"Unsupported regression failure category: {category}")

    return {
        "schema": SCHEMA,
        "generated_utc": _now(),
        "state": route["state"],
        "launcher": route["launcher"],
        "pack_fingerprint": status.get("pack_fingerprint"),
        "counts": status.get("counts"),
        "failed_case": {
            "order": case.get("order"),
            "key": case.get("key"),
            "label": case.get("label"),
            "category": category,
            "failure_notes": case.get("failure_notes", ""),
        },
        "reason": route["reason"],
        "next_action": f"Run {route['launcher']} for the authoritative current-build FAIL, then return to the same regression case.",
        "roadmap_policy": "Routing/repair tooling never clears regression evidence and never changes ROADMAP Gate A-D automatically.",
    }


def write_outputs(result: dict, output_dir: Path) -> dict:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "REGRESSION_FAILURE_ROUTER.json"
    html_path = output / "REGRESSION_FAILURE_ROUTER.html"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    case = result.get("failed_case") or result.get("next_case") or {}
    counts = result.get("counts") or {}
    html_path.write_text(
        "<!doctype html><html><head><meta charset='utf-8'><title>Regression Failure Router</title>"
        "<style>body{font:15px system-ui;max-width:1000px;margin:30px auto;padding:0 22px;background:#0d1117;color:#e6edf3}.card{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:18px;margin:14px 0}code{color:#79c0ff}.warn{color:#f2cc60}</style></head><body>"
        "<h1>Project #002 — Unified Regression Failure Router</h1>"
        f"<div class='card'><h2>{html.escape(str(result.get('state') or ''))}</h2><p>Launcher: <code>{html.escape(str(result.get('launcher') or ''))}</code></p><p>Case: <code>{html.escape(str(case.get('key') or ''))}</code> — {html.escape(str(case.get('label') or ''))}</p><p>PASS {counts.get('PASS',0)} · FAIL {counts.get('FAIL',0)} · STALE {counts.get('STALE',0)} · PENDING {counts.get('PENDING',0)}</p></div>"
        f"<div class='card'><h2>Why</h2><p>{html.escape(str(result.get('reason') or ''))}</p><h2>DO THIS NEXT</h2><p>{html.escape(str(result.get('next_action') or ''))}</p><p class='warn'>{html.escape(str(result.get('roadmap_policy') or ''))}</p></div>"
        "</body></html>",
        encoding="utf-8",
    )
    wrapped = dict(result)
    wrapped["outputs"] = {"json": str(json_path), "dashboard": str(html_path)}
    return wrapped


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 unified exact-build regression failure router")
    parser.add_argument("project_root", type=Path)
    parser.add_argument("runtime_pack", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = build_route(args.project_root, args.runtime_pack)
    output = args.output or args.project_root / "Reports" / "RegressionFailureRouter"
    print(json.dumps(write_outputs(result, output), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
