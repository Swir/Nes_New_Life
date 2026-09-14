from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path

from capture_coverage_acceptance import build_acceptance_manifest
from capture_promotion_director import promote_capture
from high_impact_art_sprint import prepare_high_impact_sprint

REVIEW_SCHEMA = "swir.project002.capture-review-director.v1"
SCHEMA = "swir.project002.evidence-bound-art-handoff.v1"
SAFE_REVIEW_STATES = {"REVIEW_REQUIRED", "CAPTURE_WORK_REQUIRED", "GATE_A_REVIEW_COMPLETE"}


class HandoffError(RuntimeError):
    pass


def _load_json(path: Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise HandoffError(f"{path}: expected a JSON object")
    return data


def validate_binding(review: dict, acceptance: dict) -> dict:
    if review.get("schema") != REVIEW_SCHEMA:
        raise HandoffError(f"Unsupported Capture Review Director schema: {review.get('schema')!r}")
    state = str(review.get("state", ""))
    if state not in SAFE_REVIEW_STATES:
        raise HandoffError(f"Unsupported capture review state: {state!r}")
    review_fp = str(review.get("capture_fingerprint_sha256", ""))
    acceptance_fp = str(acceptance.get("capture_fingerprint_sha256", ""))
    if not review_fp or not acceptance_fp:
        raise HandoffError("Review/acceptance fingerprint is missing.")
    if review_fp != acceptance_fp:
        raise HandoffError("STALE REVIEW: Capture Review Director evidence belongs to a different capture fingerprint.")

    hard_blockers = acceptance.get("hard_blockers", [])
    unsafe_kinds = {"INTEGRITY_ADMISSION", "STRUCTURAL_CAPTURE", "CAPTURE_REGRESSION", "AT_RISK_MISSION", "MISSION_PROVENANCE"}
    unsafe = [row for row in hard_blockers if str(row.get("kind", "")) in unsafe_kinds]
    if unsafe:
        raise HandoffError("Unsafe capture evidence blocks art handoff: " + ", ".join(str(row.get("kind", "")) for row in unsafe))

    summary = review.get("summary", {})
    return {
        "capture_fingerprint_sha256": review_fp,
        "review_state": state,
        "gate_a_review_complete": state == "GATE_A_REVIEW_COMPLETE",
        "verified_gate_a": int(summary.get("verified", 0) or 0),
        "reviewable_gate_a": int(summary.get("reviewable", 0) or 0),
        "blocked_gate_a": int(summary.get("blocked", 0) or 0),
        "acceptance_gate": str(acceptance.get("acceptance_gate", "BLOCKED")),
        "mode": "FULL_GATE_A_HANDOFF" if state == "GATE_A_REVIEW_COMPLETE" else "SAFE_INCREMENTAL_ART_HANDOFF",
    }


def _write_outputs(result: dict, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "EVIDENCE_BOUND_ART_HANDOFF.json"
    html_path = output_dir / "EVIDENCE_BOUND_ART_HANDOFF.html"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    sprint = result.get("art_sprint") or {}
    document = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><title>Evidence-bound Art Handoff</title>
<style>body{{font:15px system-ui;max-width:1250px;margin:28px auto;padding:0 22px;background:#0d1117;color:#e6edf3}}.card{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:18px;margin:14px 0}}code{{color:#79c0ff}}.ok{{color:#3fb950}}</style></head><body>
<h1>Tiny Toon Visual Remaster — Evidence-bound Art Handoff</h1>
<div class='card'><h2 class='ok'>{html.escape(result['status'])}</h2><p>Mode: <b>{html.escape(result['binding']['mode'])}</b></p><p>Fingerprint: <code>{html.escape(result['binding']['capture_fingerprint_sha256'])}</code></p><p>Gate A verified: {result['binding']['verified_gate_a']}/12 · review complete: {result['binding']['gate_a_review_complete']}</p></div>
<div class='card'><h2>Production handoff</h2><p>Promotion: <b>{html.escape(str(result['promotion'].get('promotion_gate', 'UNKNOWN')))}</b></p><p>Art sprint: <b>{html.escape(str(sprint.get('status', 'NOT_CREATED')))}</b> · exported {sprint.get('exported', 0)} · missing {sprint.get('missing', 0)}</p><p>Captured-art weighted completion: {sprint.get('matrix', {}).get('overall_weighted_percent', 'n/a')}%</p></div>
<div class='card'><h2>DO THIS NEXT</h2><p>{html.escape(result['next_action'])}</p><p>This dashboard is metadata-only. Local sprint PNG/contact-board outputs remain uncommitted ROM-derived production material.</p></div>
</body></html>"""
    html_path.write_text(document, encoding="utf-8")
    return {"json": str(json_path), "dashboard": str(html_path)}


def run_handoff(project_root: Path, current_capture: Path, review_json: Path, *, previous_capture: Path | None = None, batch_size: int = 30, overwrite_sprint: bool = False) -> dict:
    project_root = Path(project_root)
    capture = Path(current_capture)
    review = _load_json(review_json)
    acceptance = build_acceptance_manifest(project_root, capture, previous_capture=Path(previous_capture) if previous_capture else None)
    binding = validate_binding(review, acceptance)

    promotion = promote_capture(project_root, capture, previous_capture=Path(previous_capture) if previous_capture else None, top=max(1, batch_size), create_sprint=False)
    if promotion.get("promotion_gate") != "PROMOTED":
        raise HandoffError(f"Capture Promotion Director blocked the handoff: {promotion.get('promotion_gate')}")
    promoted_fp = str(promotion.get("coverage_acceptance", {}).get("promotion_admission", {}).get("capture_fingerprint_sha256", ""))
    if promoted_fp != binding["capture_fingerprint_sha256"]:
        raise HandoffError("Promotion fingerprint changed after admission; refusing to prepare artwork.")

    artwork = project_root / "Artwork"
    workspace = artwork / "MasterWorkspace"
    queue = artwork / "ART_QUEUE.csv"
    kit = artwork / "CurrentImpactSprint"
    reports = project_root / "Reports" / "EvidenceBoundArtHandoff"
    sprint = prepare_high_impact_sprint(capture, workspace, kit, reports / "VisualCompletion", queue=queue if queue.is_file() else None, batch_size=max(1, batch_size), overwrite=overwrite_sprint)

    if sprint.get("status") == "BLOCKED":
        next_action = "Resolve MasterWorkspace/classification blockers before editing art. No sprint was admitted."
    elif binding["gate_a_review_complete"]:
        next_action = "Edit the exact family-aware CurrentImpactSprint batch, then finish through transactional Pixel QA and verified-fullscreen playtest."
    else:
        next_action = "Continue this safe incremental art sprint, but return to Capture Review Director afterward; Gate A is not yet fully verified."

    result = {
        "schema": SCHEMA,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "ART_HANDOFF_READY" if sprint.get("status") in {"READY", "PARTIAL"} else "ART_HANDOFF_BLOCKED",
        "binding": binding,
        "promotion": {
            "promotion_gate": promotion.get("promotion_gate"),
            "promotion_mode": promotion.get("coverage_acceptance", {}).get("promotion_admission", {}).get("mode"),
            "capture_regressions": promotion.get("capture_regressions", 0),
        },
        "art_sprint": sprint,
        "next_action": next_action,
        "policy": "Never treats tooling or an incremental art handoff as Gate A completion. Review and promotion must remain bound to the exact current capture fingerprint.",
    }
    result["outputs"] = _write_outputs(result, reports)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 fingerprint-bound capture review -> HD art handoff")
    parser.add_argument("project_root", type=Path)
    parser.add_argument("current_capture", type=Path)
    parser.add_argument("review_json", type=Path)
    parser.add_argument("--previous-capture", type=Path)
    parser.add_argument("--batch-size", type=int, default=30)
    parser.add_argument("--overwrite-sprint", action="store_true")
    args = parser.parse_args()
    try:
        result = run_handoff(args.project_root, args.current_capture, args.review_json, previous_capture=args.previous_capture, batch_size=args.batch_size, overwrite_sprint=args.overwrite_sprint)
    except (HandoffError, ValueError, FileNotFoundError) as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, ensure_ascii=False))
        return 3
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "ART_HANDOFF_READY" else 4


if __name__ == "__main__":
    raise SystemExit(main())
