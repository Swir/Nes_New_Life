from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path

from active_family_workbench import WorkbenchError, resolve_active_family_workbench, write_active_state
from capture_coverage_acceptance import build_acceptance_manifest
from capture_production_director import run_director
from hd_art_autopilot import run_autopilot

REVIEW_SCHEMA = "swir.project002.capture-review-director.v1"
GATE_REVIEW_SCHEMA = "swir.project002.gate-a-review-attestation.v1"
SCHEMA = "swir.project002.evidence-bound-art-handoff.v2"
SAFE_REVIEW_STATES = {"REVIEW_REQUIRED", "CAPTURE_WORK_REQUIRED", "GATE_A_REVIEW_COMPLETE"}
CONFIRMATION = "VERIFIED_GATE_A"
GATE_A_ITEMS = 12


class HandoffError(RuntimeError):
    pass


def _load_json(path: Path) -> dict:
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise HandoffError(f"Missing required local evidence: {path.name}") from exc
    except json.JSONDecodeError as exc:
        raise HandoffError(f"Invalid JSON: {path.name}") from exc
    if not isinstance(data, dict):
        raise HandoffError(f"{path.name}: expected a JSON object")
    return data


def _validate_attestation_chain(gate_review: dict, ledger: dict, fingerprint: str) -> dict:
    if gate_review.get("schema") != GATE_REVIEW_SCHEMA:
        raise HandoffError(f"Unsupported Gate A review schema: {gate_review.get('schema')!r}")
    if ledger.get("schema") != GATE_REVIEW_SCHEMA:
        raise HandoffError(f"Unsupported Gate A attestation schema: {ledger.get('schema')!r}")
    if str(gate_review.get("capture_fingerprint_sha256", "")) != fingerprint:
        raise HandoffError("STALE GATE A REVIEW: review handoff belongs to a different capture fingerprint.")
    if str(ledger.get("capture_fingerprint_sha256", "")) != fingerprint:
        raise HandoffError("STALE GATE A LEDGER: attestation ledger belongs to a different capture fingerprint.")

    criteria = gate_review.get("criteria")
    attestations = ledger.get("attestations")
    if not isinstance(criteria, list) or len(criteria) != GATE_A_ITEMS:
        raise HandoffError(f"Gate A review must contain exactly {GATE_A_ITEMS} criteria.")
    if not isinstance(attestations, list):
        raise HandoffError("Gate A attestation ledger has an invalid attestations payload.")

    attested: dict[int, dict] = {}
    for row in attestations:
        if not isinstance(row, dict):
            raise HandoffError("Gate A attestation rows must be objects.")
        try:
            index = int(row.get("index", 0))
        except (TypeError, ValueError) as exc:
            raise HandoffError("Gate A attestation index is invalid.") from exc
        if index < 1 or index > GATE_A_ITEMS or index in attested:
            raise HandoffError(f"Invalid or duplicate Gate A attestation index: {index}")
        if str(row.get("confirmation", "")) != CONFIRMATION:
            raise HandoffError(f"Gate A attestation {index} lacks exact {CONFIRMATION}.")
        if str(row.get("capture_fingerprint_sha256", "")) != fingerprint:
            raise HandoffError(f"Gate A attestation {index} belongs to another capture fingerprint.")
        if str(row.get("source_fingerprint_sha256", "")) != fingerprint:
            raise HandoffError(f"Gate A attestation {index} source fingerprint is stale.")
        attested[index] = row

    seen: set[int] = set()
    verified = 0
    reviewable = 0
    blocked = 0
    for row in criteria:
        if not isinstance(row, dict):
            raise HandoffError("Gate A criterion rows must be objects.")
        try:
            index = int(row.get("index", 0))
        except (TypeError, ValueError) as exc:
            raise HandoffError("Gate A criterion index is invalid.") from exc
        if index < 1 or index > GATE_A_ITEMS or index in seen:
            raise HandoffError(f"Invalid or duplicate Gate A criterion index: {index}")
        seen.add(index)
        if str(row.get("capture_fingerprint_sha256", "")) != fingerprint:
            raise HandoffError(f"Gate A criterion {index} belongs to another capture fingerprint.")

        status = str(row.get("review_status", ""))
        source_fp = str(row.get("source_fingerprint_sha256", ""))
        ledger_row = attested.get(index)
        if status == "VERIFIED_GATE_A":
            if source_fp != fingerprint:
                raise HandoffError(f"Gate A criterion {index} verified source fingerprint is stale.")
            if ledger_row is None:
                raise HandoffError(f"Gate A criterion {index} claims VERIFIED_GATE_A without matching ledger evidence.")
            if str(ledger_row.get("source_fingerprint_sha256", "")) != source_fp:
                raise HandoffError(f"Gate A criterion {index} and ledger source fingerprints differ.")
            verified += 1
        elif status == "AWAITING_HUMAN_ATTESTATION":
            if source_fp != fingerprint:
                raise HandoffError(f"Gate A criterion {index} reviewable source fingerprint is stale.")
            if ledger_row is not None:
                raise HandoffError(f"Gate A criterion {index} has ledger evidence but is not VERIFIED_GATE_A.")
            reviewable += 1
        elif status == "BLOCKED_BY_EVIDENCE":
            if ledger_row is not None:
                raise HandoffError(f"Gate A criterion {index} is blocked but has current attestation evidence.")
            blocked += 1
        else:
            raise HandoffError(f"Gate A criterion {index} has unsupported review status: {status!r}")

    phantom = sorted(set(attested) - seen)
    if phantom:
        raise HandoffError(f"Gate A ledger contains phantom criteria: {phantom}")

    return {
        "verified": verified,
        "reviewable": reviewable,
        "blocked": blocked,
        "total": GATE_A_ITEMS,
        "full_gate_a_review": verified == GATE_A_ITEMS,
    }


def validate_binding(review: dict, acceptance: dict, gate_review: dict, ledger: dict) -> dict:
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

    attestation = _validate_attestation_chain(gate_review, ledger, review_fp)
    director_summary = review.get("summary", {})
    director_verified = int(director_summary.get("verified", 0) or 0)
    if director_verified != attestation["verified"]:
        raise HandoffError(
            f"Capture Review Director verified count ({director_verified}) does not match ledger-backed Gate A review ({attestation['verified']})."
        )
    if state == "GATE_A_REVIEW_COMPLETE" and not attestation["full_gate_a_review"]:
        raise HandoffError("Capture Review Director claims GATE_A_REVIEW_COMPLETE without 12 ledger-backed VERIFIED_GATE_A attestations.")
    if state != "GATE_A_REVIEW_COMPLETE" and attestation["full_gate_a_review"]:
        raise HandoffError("Gate A ledger is fully verified but Capture Review Director state is stale; refresh review director first.")

    return {
        "capture_fingerprint_sha256": review_fp,
        "review_state": state,
        "gate_a_review_complete": attestation["full_gate_a_review"],
        "verified_gate_a": attestation["verified"],
        "reviewable_gate_a": attestation["reviewable"],
        "blocked_gate_a": attestation["blocked"],
        "acceptance_gate": str(acceptance.get("acceptance_gate", "BLOCKED")),
        "mode": "FULL_GATE_A_HANDOFF" if attestation["full_gate_a_review"] else "SAFE_INCREMENTAL_ART_HANDOFF",
    }


def _write_outputs(result: dict, output_dir: Path) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "EVIDENCE_BOUND_ART_HANDOFF.json"
    html_path = output_dir / "EVIDENCE_BOUND_ART_HANDOFF.html"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    binding = result["binding"]
    art = result.get("art") or {}
    active = result.get("active_family") or {}
    document = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><title>Evidence-bound Art Handoff</title>
<style>body{{font:15px system-ui;max-width:1250px;margin:28px auto;padding:0 22px;background:#0d1117;color:#e6edf3}}.card{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:18px;margin:14px 0}}code{{color:#79c0ff}}.ok{{color:#3fb950}}</style></head><body>
<h1>Tiny Toon Visual Remaster — Evidence-bound Art Handoff v2</h1>
<div class='card'><h2 class='ok'>{html.escape(result['status'])}</h2><p>Mode: <b>{html.escape(binding['mode'])}</b></p><p>Fingerprint: <code>{html.escape(binding['capture_fingerprint_sha256'])}</code></p><p>Ledger-backed Gate A: {binding['verified_gate_a']}/12 · reviewable {binding['reviewable_gate_a']} · blocked {binding['blocked_gate_a']}</p></div>
<div class='card'><h2>Production handoff</h2><p>Production: <b>{html.escape(str(result['production_decision']))}</b> · promotion <b>{html.escape(str(result['promotion_gate']))}</b></p><p>HD Art Autopilot: <b>{html.escape(str(art.get('status', 'NOT_RUN')))}</b></p><p>Captured unfinished: {art.get('captured_unfinished', 0)} · next batch {art.get('next_batch_count', 0)}</p><p>Active family: <b>{html.escape(str(active.get('family', '—')))}</b></p></div>
<div class='card'><h2>DO THIS NEXT</h2><p>{html.escape(result['next_action'])}</p><p>This dashboard is metadata-only. Local sprint PNG/contact-board outputs remain uncommitted ROM-derived production material.</p></div>
</body></html>"""
    html_path.write_text(document, encoding="utf-8")
    return {"json": json_path.name, "dashboard": html_path.name}


def run_handoff(
    project_root: Path,
    current_capture: Path,
    review_json: Path,
    *,
    previous_capture: Path | None = None,
    batch_size: int = 30,
    require_full_gate_a: bool = False,
) -> dict:
    project_root = Path(project_root)
    capture = Path(current_capture)
    previous = Path(previous_capture) if previous_capture else None
    review = _load_json(review_json)

    gate_dir = project_root / "Reports" / "GateAReviewAttestation"
    gate_review = _load_json(gate_dir / "GATE_A_REVIEW_HANDOFF.json")
    ledger = _load_json(gate_dir / "GATE_A_ATTESTATIONS.json")
    acceptance = build_acceptance_manifest(project_root, capture, previous_capture=previous)
    binding = validate_binding(review, acceptance, gate_review, ledger)

    if require_full_gate_a and not binding["gate_a_review_complete"]:
        raise HandoffError("Strict handoff requires all 12 Gate A criteria to have ledger-backed VERIFIED_GATE_A attestations.")

    director = run_director(
        project_root,
        capture,
        previous_capture=previous,
        promote_safe=True,
        create_sprint=False,
        top=max(1, int(batch_size)),
    )
    director_fp = str(director.get("acceptance", {}).get("capture_fingerprint_sha256", ""))
    if director_fp != binding["capture_fingerprint_sha256"]:
        raise HandoffError("Capture Production Director acceptance fingerprint changed after binding.")

    decision = director.get("decision", {})
    production_decision = str(decision.get("production_decision", "BLOCK_PRODUCTION"))
    promotion = director.get("promotion") or {}
    promotion_gate = str(promotion.get("promotion_gate", "NOT_RUN"))
    if production_decision == "BLOCK_PRODUCTION" or promotion_gate != "PROMOTED":
        raise HandoffError(f"Capture Production Director blocked art handoff: {production_decision} / {promotion_gate}")

    art = run_autopilot(project_root, capture, batch_size=max(1, int(batch_size)))
    if not bool(art.get("allowed", False)):
        raise HandoffError(f"HD Art Autopilot blocked the handoff: {art.get('status', 'UNKNOWN')}")

    active_family = None
    kit = project_root / "Artwork" / "CurrentImpactSprint"
    if kit.is_dir():
        try:
            active_family = resolve_active_family_workbench(kit)
            write_active_state(active_family, kit)
        except WorkbenchError:
            active_family = None

    art_status = str(art.get("status", "UNKNOWN"))
    if active_family:
        status = "ART_WORKBENCH_READY"
        next_action = (
            f"Redraw the active {active_family['family']} family together, then finish through transactional visual/family/Pixel QA and verified-fullscreen playtest."
        )
    elif art_status == "CAPTURED_ART_COMPLETE":
        status = "CAPTURED_ART_COMPLETE"
        next_action = str(art.get("next_action", "Continue missing capture or exact-build QA/regression."))
    elif art_status == "RESUME_EXISTING_SPRINT":
        status = "RESUME_EXISTING_SPRINT"
        next_action = str(art.get("next_action", "Finish the existing CurrentImpactSprint."))
    else:
        status = "ART_HANDOFF_READY"
        next_action = str(art.get("next_action", "Continue the exact high-impact 4x art batch."))

    result = {
        "schema": SCHEMA,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "binding": binding,
        "production_decision": production_decision,
        "promotion_gate": promotion_gate,
        "art": {
            "status": art_status,
            "captured_unfinished": art.get("visual_completion", {}).get("captured_unfinished", 0),
            "next_batch_count": art.get("visual_completion", {}).get("next_batch_count", 0),
            "sprint_status": (art.get("sprint") or {}).get("status"),
            "sprint_exported": (art.get("sprint") or {}).get("exported", 0),
        },
        "active_family": active_family,
        "next_action": next_action,
        "policy": "Never treats tooling or incremental art handoff as Gate A completion. Review, attestations and production remain bound to the exact current capture fingerprint.",
        "privacy_contract": {
            "metadata_only": True,
            "rom_bytes": False,
            "save_states": False,
            "capture_pixels": False,
            "emulator_binaries": False,
            "absolute_local_paths": False,
        },
    }
    result["outputs"] = _write_outputs(result, project_root / "Reports" / "EvidenceBoundArtHandoff")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 ledger-backed capture review -> HD art handoff")
    parser.add_argument("project_root", type=Path)
    parser.add_argument("current_capture", type=Path)
    parser.add_argument("review_json", type=Path)
    parser.add_argument("--previous-capture", type=Path)
    parser.add_argument("--batch-size", type=int, default=30)
    parser.add_argument("--require-full-gate-a", action="store_true")
    args = parser.parse_args()
    try:
        result = run_handoff(
            args.project_root,
            args.current_capture,
            args.review_json,
            previous_capture=args.previous_capture,
            batch_size=max(1, args.batch_size),
            require_full_gate_a=args.require_full_gate_a,
        )
    except (HandoffError, ValueError, FileNotFoundError) as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, ensure_ascii=False))
        return 3
    print(json.dumps({
        "status": result["status"],
        "binding": result["binding"],
        "production_decision": result["production_decision"],
        "promotion_gate": result["promotion_gate"],
        "art": result["art"],
        "active_family": result["active_family"],
        "next_action": result["next_action"],
        "outputs": result["outputs"],
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
