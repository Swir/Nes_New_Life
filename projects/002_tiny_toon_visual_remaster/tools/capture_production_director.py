from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path

from capture_coverage_acceptance import build_acceptance_manifest, write_outputs as write_acceptance_outputs
from capture_promotion_director import promote_capture

UNSAFE_KINDS = {
    "INTEGRITY_ADMISSION",
    "STRUCTURAL_CAPTURE",
    "CAPTURE_REGRESSION",
    "AT_RISK_MISSION",
    "MISSION_PROVENANCE",
}

REGRESSION_KINDS = {"CAPTURE_REGRESSION", "AT_RISK_MISSION"}


def classify_acceptance(acceptance: dict) -> dict:
    blockers = list(acceptance.get("hard_blockers", []))
    kinds = [str(row.get("kind", "")) for row in blockers]
    unsafe = [row for row in blockers if str(row.get("kind", "")) in UNSAFE_KINDS]
    mission_summary = acceptance.get("mission_summary", {})

    if any(kind in REGRESSION_KINDS for kind in kinds):
        capture_decision = "FIX_REGRESSION"
    elif unsafe:
        capture_decision = "FIX_CAPTURE_INTEGRITY"
    elif acceptance.get("acceptance_gate") == "READY_FOR_GATE_A_REVIEW":
        capture_decision = "READY_FOR_GATE_A_REVIEW"
    else:
        capture_decision = "CAPTURE_MORE"

    if unsafe:
        production_decision = "BLOCK_PRODUCTION"
    elif acceptance.get("acceptance_gate") == "READY_FOR_GATE_A_REVIEW":
        production_decision = "FULL_CAPTURE_READY"
    else:
        production_decision = "SAFE_INCREMENTAL_ART"

    if capture_decision == "FIX_REGRESSION":
        next_action = "Repair the current capture until all regression/at-risk evidence is cleared, then rerun this director."
    elif capture_decision == "FIX_CAPTURE_INTEGRITY":
        next_action = "Repair structural/integrity/provenance blockers before any production sync."
    elif capture_decision == "READY_FOR_GATE_A_REVIEW":
        next_action = "Review the real MesenCE gameplay evidence manually; only then may Gate A checklist items be changed."
    else:
        pending = int(mission_summary.get("pending", 0) or 0)
        next_action = f"Continue Guided Capture Marathon for the remaining {pending} mission(s); safe captured work may continue into incremental art production."

    return {
        "capture_decision": capture_decision,
        "production_decision": production_decision,
        "unsafe_blocker_count": len(unsafe),
        "blocker_kinds": kinds,
        "next_action": next_action,
    }


def _safe_path(value: Path | None) -> str | None:
    return value.name if value else None


def _write_report(result: dict, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "CAPTURE_PRODUCTION_DIRECTOR.json"
    html_path = output_dir / "CAPTURE_PRODUCTION_DIRECTOR.html"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    decision = result["decision"]
    blockers = result.get("acceptance", {}).get("hard_blockers", [])
    blocker_html = "".join(
        f"<li><b>{html.escape(str(row.get('kind', '')))}</b> — {html.escape(str(row.get('detail', '')))}</li>"
        for row in blockers
    ) or "<li>None</li>"
    promotion = result.get("promotion") or {}
    promotion_gate = promotion.get("promotion_gate", "NOT_RUN")
    fingerprint = result.get("acceptance", {}).get("capture_fingerprint_sha256", "")

    document = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'>
<title>Project #002 Capture Production Director</title><style>
body{{font:15px system-ui;max-width:1100px;margin:30px auto;padding:0 22px;background:#0d1117;color:#e6edf3}}
.card{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:16px;margin:12px 0}}
code{{color:#79c0ff;word-break:break-all}}.ok{{color:#3fb950}}.warn{{color:#d29922}}.bad{{color:#f85149}}
</style></head><body>
<h1>Project #002 — Capture Production Director</h1>
<div class='card'><h2>Capture decision: {html.escape(decision['capture_decision'])}</h2>
<p>Production decision: <b>{html.escape(decision['production_decision'])}</b></p>
<p>Promotion gate: <b>{html.escape(str(promotion_gate))}</b></p>
<p>Fingerprint: <code>{html.escape(str(fingerprint))}</code></p>
<p><b>DO THIS NEXT:</b> {html.escape(decision['next_action'])}</p></div>
<div class='card'><h2>Hard blockers</h2><ul>{blocker_html}</ul></div>
<div class='card'><p>This report is metadata-only. It does not contain ROM bytes, save states, capture pixels, emulator binaries or absolute local paths.</p>
<p>It never edits ROADMAP Gate A-D.</p></div>
</body></html>"""
    html_path.write_text(document, encoding="utf-8")
    return {"json": str(json_path), "dashboard": str(html_path)}


def run_director(
    project_root: Path,
    current_capture: Path,
    *,
    previous_capture: Path | None = None,
    promote_safe: bool = False,
    create_sprint: bool = False,
    top: int = 20,
) -> dict:
    project_root = Path(project_root)
    current_capture = Path(current_capture)
    previous_capture = Path(previous_capture) if previous_capture else None
    reports = project_root / "Reports"

    acceptance = build_acceptance_manifest(project_root, current_capture, previous_capture=previous_capture)
    acceptance_outputs = write_acceptance_outputs(acceptance, reports / "CaptureCoverageAcceptance")
    decision = classify_acceptance(acceptance)

    promotion = None
    if promote_safe and decision["production_decision"] != "BLOCK_PRODUCTION":
        promotion = promote_capture(
            project_root,
            current_capture,
            previous_capture=previous_capture,
            top=max(1, top),
            create_sprint=create_sprint,
        )

    result = {
        "schema": "swir.project002.capture-production-director.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "current_capture": _safe_path(current_capture),
        "previous_capture": _safe_path(previous_capture),
        "decision": decision,
        "acceptance": acceptance,
        "acceptance_outputs": acceptance_outputs,
        "promotion": promotion,
        "roadmap_policy": "This director never edits Gate A-D. Real gameplay/art/QA evidence remains authoritative.",
        "privacy_contract": {
            "metadata_only": True,
            "rom_bytes": False,
            "save_states": False,
            "capture_pixels": False,
            "emulator_binaries": False,
            "absolute_local_paths": False,
        },
    }
    result["outputs"] = _write_report(result, reports / "CaptureProductionDirector")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 one-command capture -> acceptance -> safe production director")
    parser.add_argument("project_root", type=Path)
    parser.add_argument("current_capture", type=Path)
    parser.add_argument("--previous-capture", type=Path)
    parser.add_argument("--promote-safe", action="store_true")
    parser.add_argument("--create-sprint", action="store_true")
    parser.add_argument("--top", type=int, default=20)
    args = parser.parse_args()

    result = run_director(
        args.project_root,
        args.current_capture,
        previous_capture=args.previous_capture,
        promote_safe=args.promote_safe,
        create_sprint=args.create_sprint,
        top=args.top,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    decision = result["decision"]["production_decision"]
    return 3 if decision == "BLOCK_PRODUCTION" else 0


if __name__ == "__main__":
    raise SystemExit(main())
