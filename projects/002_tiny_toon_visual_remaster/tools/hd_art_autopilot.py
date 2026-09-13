from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path

from capture_integrity_ledger import capture_fingerprint
from high_impact_art_sprint import prepare_high_impact_sprint
from visual_completion_matrix import build_and_write as build_visual_completion

SAFE_PRODUCTION = {"SAFE_INCREMENTAL_ART", "FULL_CAPTURE_READY"}


def evaluate_autopilot(director: dict, current_fingerprint: str, *, sprint_exists: bool, next_batch_count: int) -> dict:
    decision = director.get("decision", {})
    acceptance = director.get("acceptance", {})
    promotion = director.get("promotion") or {}
    expected = str(acceptance.get("capture_fingerprint_sha256", ""))
    production = str(decision.get("production_decision", "BLOCK_PRODUCTION"))
    promotion_gate = str(promotion.get("promotion_gate", "NOT_RUN"))

    if not expected or expected != current_fingerprint:
        return {
            "status": "BLOCKED_STALE_CAPTURE",
            "allowed": False,
            "next_action": "Rerun the Capture -> HD production path because the current capture fingerprint changed after the production decision.",
        }
    if production not in SAFE_PRODUCTION or promotion_gate != "PROMOTED":
        return {
            "status": "BLOCKED_UNSAFE_PRODUCTION",
            "allowed": False,
            "next_action": "Resolve capture integrity/regression/provenance blockers and rerun guarded capture promotion before preparing art.",
        }
    if sprint_exists:
        return {
            "status": "RESUME_EXISTING_SPRINT",
            "allowed": True,
            "next_action": "Finish the existing CurrentImpactSprint before generating a replacement; existing artist work was preserved.",
        }
    if next_batch_count <= 0:
        return {
            "status": "CAPTURED_ART_COMPLETE",
            "allowed": True,
            "next_action": "No captured high-impact art remains. Continue missing gameplay capture or proceed to exact-build Pixel QA/regression as appropriate.",
        }
    return {
        "status": "PREPARE_HIGH_IMPACT_SPRINT",
        "allowed": True,
        "next_action": "Prepare the exact Visual Completion Matrix high-impact batch and open it for the next 4x art pass.",
    }


def _write_report(result: dict, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "HD_ART_AUTOPILOT.json"
    html_path = output_dir / "HD_ART_AUTOPILOT.html"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    status = html.escape(str(result.get("status", "UNKNOWN")))
    next_action = html.escape(str(result.get("next_action", "")))
    fp = html.escape(str(result.get("capture_fingerprint_sha256", "")))
    matrix = result.get("visual_completion", {})
    sprint = result.get("sprint", {}) or {}
    document = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><title>Project #002 HD Art Autopilot</title>
<style>body{{font:15px system-ui;max-width:1050px;margin:30px auto;padding:0 22px;background:#0d1117;color:#e6edf3}}.card{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:16px;margin:12px 0}}code{{color:#79c0ff;word-break:break-all}}.ok{{color:#3fb950}}.warn{{color:#d29922}}.bad{{color:#f85149}}</style></head><body>
<h1>Project #002 — HD Art Autopilot</h1><div class='card'><h2>{status}</h2><p>Capture fingerprint: <code>{fp}</code></p><p>Captured-art weighted completion: <b>{html.escape(str(matrix.get('overall_weighted_percent', '—')))}%</b></p><p>Captured unfinished: <b>{html.escape(str(matrix.get('captured_unfinished', '—')))}</b></p><p>Exact next batch: <b>{html.escape(str(matrix.get('next_batch_count', 0)))}</b></p><p>Sprint exported: <b>{html.escape(str(sprint.get('exported', 0)))}</b></p><p><b>DO THIS NEXT:</b> {next_action}</p></div>
<div class='card'><p>Fail-closed and metadata-only. This report stores no ROM bytes, save states, capture pixels, emulator binaries or absolute local paths. It never edits ROADMAP Gate A-D.</p></div></body></html>"""
    html_path.write_text(document, encoding="utf-8")
    return {"json": json_path.name, "dashboard": html_path.name}


def run_autopilot(project_root: Path, current_capture: Path, *, batch_size: int = 30) -> dict:
    root = Path(project_root)
    capture = Path(current_capture)
    director_path = root / "Reports" / "CaptureProductionDirector" / "CAPTURE_PRODUCTION_DIRECTOR.json"
    if not director_path.is_file():
        raise FileNotFoundError("Capture Production Director decision is missing; run guarded Capture -> HD production first.")

    director = json.loads(director_path.read_text(encoding="utf-8-sig"))
    fingerprint = capture_fingerprint(capture)
    artwork = root / "Artwork"
    workspace = artwork / "MasterWorkspace"
    queue = artwork / "ART_QUEUE.csv"
    kit = artwork / "CurrentImpactSprint"
    reports = root / "Reports" / "VisualCompletion"

    if not (workspace / "MASTER_TILES.json").is_file():
        raise FileNotFoundError("MasterWorkspace is not ready; guarded capture promotion must sync production state first.")

    matrix = build_visual_completion(
        capture,
        reports,
        queue=queue if queue.is_file() else None,
        workspace=workspace,
        batch_size=max(1, int(batch_size)),
    )
    sprint_exists = kit.exists() and any(kit.iterdir())
    decision = evaluate_autopilot(
        director,
        fingerprint,
        sprint_exists=sprint_exists,
        next_batch_count=len(matrix.get("next_batch", [])),
    )

    sprint = None
    if decision["status"] == "PREPARE_HIGH_IMPACT_SPRINT":
        sprint = prepare_high_impact_sprint(
            capture,
            workspace,
            kit,
            reports,
            queue=queue if queue.is_file() else None,
            batch_size=max(1, int(batch_size)),
            overwrite=False,
        )
        decision = {
            "status": "HIGH_IMPACT_SPRINT_READY" if sprint.get("status") == "READY" else "HIGH_IMPACT_SPRINT_PARTIAL",
            "allowed": True,
            "next_action": "Edit only CurrentImpactSprint/editable/*.png, preserve dimensions/alpha/filenames, then finish through the QA-gated High-Impact Art Sprint importer.",
        }

    result = {
        "schema": "swir.project002.hd-art-autopilot.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": decision["status"],
        "allowed": decision["allowed"],
        "capture_fingerprint_sha256": fingerprint,
        "production_decision": director.get("decision", {}).get("production_decision", "UNKNOWN"),
        "promotion_gate": (director.get("promotion") or {}).get("promotion_gate", "NOT_RUN"),
        "visual_completion": {
            "overall_weighted_percent": matrix.get("overall_weighted_percent", 0),
            "captured_unfinished": matrix.get("captured_unfinished", 0),
            "blocking_items": matrix.get("blocking_items", 0),
            "next_batch_count": len(matrix.get("next_batch", [])),
        },
        "sprint": None if sprint is None else {
            "status": sprint.get("status"),
            "exported": sprint.get("exported", 0),
            "missing": sprint.get("missing", 0),
            "selection_mode": sprint.get("selection_mode"),
        },
        "next_action": decision["next_action"],
        "roadmap_policy": "Automation never edits Gate A-D; real local gameplay/art/QA evidence remains authoritative.",
        "privacy_contract": {
            "metadata_only": True,
            "rom_bytes": False,
            "save_states": False,
            "capture_pixels": False,
            "emulator_binaries": False,
            "absolute_local_paths": False,
        },
    }
    result["outputs"] = _write_report(result, root / "Reports" / "HDArtAutopilot")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 fingerprint-bound safe capture -> exact high-impact 4x art autopilot")
    parser.add_argument("project_root", type=Path)
    parser.add_argument("current_capture", type=Path)
    parser.add_argument("--batch-size", type=int, default=30)
    args = parser.parse_args()
    result = run_autopilot(args.project_root, args.current_capture, batch_size=max(1, args.batch_size))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 3 if not result["allowed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
