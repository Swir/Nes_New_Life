from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path

MATRIX_SCHEMA = "swir.project002.gate-a-evidence-matrix.v1"
SCHEMA = "swir.project002.gate-a-review-attestation.v1"
CONFIRMATION = "VERIFIED_GATE_A"
TOTAL_ROADMAP_ITEMS = 52
GATE_A_ITEMS = 12


class ReviewError(RuntimeError):
    pass


def _load_json(path: Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ReviewError("Input must be a JSON object.")
    return data


def _load_matrix(path: Path) -> dict:
    data = _load_json(path)
    if data.get("schema") != MATRIX_SCHEMA:
        raise ReviewError(f"Unsupported Gate A evidence matrix schema: {data.get('schema')!r}")
    fingerprint = str(data.get("capture_fingerprint_sha256", ""))
    if not fingerprint:
        raise ReviewError("Gate A matrix is missing capture_fingerprint_sha256.")
    criteria = data.get("criteria")
    if not isinstance(criteria, list) or len(criteria) != GATE_A_ITEMS:
        raise ReviewError(f"Gate A matrix must contain exactly {GATE_A_ITEMS} criteria.")
    return data


def _empty_ledger(fingerprint: str) -> dict:
    return {
        "schema": SCHEMA,
        "capture_fingerprint_sha256": fingerprint,
        "attestations": [],
    }


def _load_ledger(path: Path, fingerprint: str) -> dict:
    if not path.is_file():
        return _empty_ledger(fingerprint)
    data = _load_json(path)
    if data.get("schema") != SCHEMA:
        raise ReviewError(f"Unsupported attestation schema: {data.get('schema')!r}")
    if str(data.get("capture_fingerprint_sha256", "")) != fingerprint:
        raise ReviewError("Attestation ledger belongs to a different capture fingerprint; stale evidence is rejected.")
    if not isinstance(data.get("attestations"), list):
        raise ReviewError("Attestation ledger has invalid attestations payload.")
    return data


def build_review(matrix: dict, ledger: dict) -> dict:
    fingerprint = str(matrix["capture_fingerprint_sha256"])
    if str(ledger.get("capture_fingerprint_sha256", "")) != fingerprint:
        raise ReviewError("Matrix and attestation ledger fingerprints differ.")
    attested = {
        int(row["index"]): row
        for row in ledger.get("attestations", [])
        if isinstance(row, dict) and str(row.get("index", "")).isdigit()
    }
    rows = []
    for source in matrix["criteria"]:
        index = int(source["index"])
        evidence_status = str(source.get("status", ""))
        att = attested.get(index)
        if att:
            review_status = "VERIFIED_GATE_A"
            next_action = "Already explicitly reviewed against this exact capture fingerprint."
        elif evidence_status == "EVIDENCE_READY_FOR_REVIEW":
            review_status = "AWAITING_HUMAN_ATTESTATION"
            next_action = "Review the real local MesenCE gameplay evidence, then attest only if this criterion is genuinely satisfied."
        else:
            review_status = "BLOCKED_BY_EVIDENCE"
            next_action = str(source.get("reason", "Evidence is not ready."))
        rows.append({
            "index": index,
            "criterion": str(source.get("criterion", "")),
            "mission_key": str(source.get("mission_key", "")),
            "evidence_status": evidence_status,
            "review_status": review_status,
            "capture_fingerprint_sha256": fingerprint,
            "source_fingerprint_sha256": str(source.get("source_fingerprint_sha256", "")),
            "next_action": next_action,
        })

    verified = sum(row["review_status"] == "VERIFIED_GATE_A" for row in rows)
    reviewable = sum(row["review_status"] == "AWAITING_HUMAN_ATTESTATION" for row in rows)
    blocked = GATE_A_ITEMS - verified - reviewable
    projected_completed = verified
    projected_percent = round(projected_completed * 100.0 / TOTAL_ROADMAP_ITEMS, 1)
    first = next((row for row in rows if row["review_status"] == "AWAITING_HUMAN_ATTESTATION"), None)
    if first is None:
        first = next((row for row in rows if row["review_status"] == "BLOCKED_BY_EVIDENCE"), None)
    return {
        "schema": SCHEMA,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "capture_fingerprint_sha256": fingerprint,
        "policy": "Only explicit VERIFIED_GATE_A attestations for EVIDENCE_READY_FOR_REVIEW rows count. This tool never edits ROADMAP.md automatically.",
        "summary": {
            "verified_gate_a": verified,
            "awaiting_human_attestation": reviewable,
            "blocked_by_evidence": blocked,
            "gate_a_total": GATE_A_ITEMS,
        },
        "roadmap_patch_preview": {
            "verified_gate_a_indexes": [row["index"] for row in rows if row["review_status"] == "VERIFIED_GATE_A"],
            "projected_completed_over_52": projected_completed,
            "projected_remaining_over_52": TOTAL_ROADMAP_ITEMS - projected_completed,
            "projected_percent": projected_percent,
            "note": "Preview assumes no Gate B-D checkbox changes and must be reconciled against current ROADMAP before any PR is created.",
        },
        "criteria": rows,
        "next_action": (
            {
                "index": first["index"],
                "criterion": first["criterion"],
                "kind": first["review_status"],
                "instruction": first["next_action"],
            }
            if first
            else {
                "kind": "GATE_A_ATTESTATION_COMPLETE",
                "criterion": "All 12 Gate A criteria are explicitly attested for this capture fingerprint.",
                "instruction": "Prepare a reviewed metadata-only roadmap update PR; do not infer Gate B-D completion.",
            }
        ),
    }


def attest(matrix: dict, ledger: dict, index: int, confirmation: str, reviewer: str) -> dict:
    if confirmation != CONFIRMATION:
        raise ReviewError(f"Refusing attestation: exact confirmation token {CONFIRMATION!r} is required.")
    if not reviewer.strip():
        raise ReviewError("Reviewer identity/label is required.")
    criterion = next((row for row in matrix["criteria"] if int(row.get("index", 0)) == index), None)
    if criterion is None:
        raise ReviewError(f"Unknown Gate A criterion index: {index}")
    if criterion.get("status") != "EVIDENCE_READY_FOR_REVIEW":
        raise ReviewError(f"Criterion {index} is not evidence-ready: {criterion.get('status')}")
    fingerprint = str(matrix["capture_fingerprint_sha256"])
    source_fp = str(criterion.get("source_fingerprint_sha256", ""))
    if not source_fp:
        raise ReviewError("Evidence-ready criterion unexpectedly lacks source fingerprint.")

    rows = [row for row in ledger.get("attestations", []) if int(row.get("index", -1)) != index]
    rows.append({
        "index": index,
        "criterion": str(criterion.get("criterion", "")),
        "mission_key": str(criterion.get("mission_key", "")),
        "confirmation": CONFIRMATION,
        "reviewer": reviewer.strip(),
        "attested_utc": datetime.now(timezone.utc).isoformat(),
        "capture_fingerprint_sha256": fingerprint,
        "source_fingerprint_sha256": source_fp,
    })
    rows.sort(key=lambda row: int(row["index"]))
    ledger["attestations"] = rows
    return ledger


def write_outputs(review: dict, ledger: dict, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = output_dir / "GATE_A_ATTESTATIONS.json"
    review_path = output_dir / "GATE_A_REVIEW_HANDOFF.json"
    html_path = output_dir / "GATE_A_REVIEW_HANDOFF.html"
    ledger_path.write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    review_path.write_text(json.dumps(review, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    rows = "".join(
        "<tr>"
        f"<td>{row['index']}</td><td>{html.escape(row['criterion'])}</td>"
        f"<td>{html.escape(row['evidence_status'])}</td><td>{html.escape(row['review_status'])}</td>"
        f"<td>{html.escape(row['next_action'])}</td></tr>"
        for row in review["criteria"]
    )
    s = review["summary"]
    p = review["roadmap_patch_preview"]
    n = review["next_action"]
    document = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><title>Gate A Review & Attestation</title>
<style>body{{font:15px system-ui;max-width:1400px;margin:28px auto;padding:0 22px;background:#0d1117;color:#e6edf3}}.card{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:18px;margin:14px 0}}table{{width:100%;border-collapse:collapse}}td,th{{padding:8px;border-bottom:1px solid #30363d;text-align:left;vertical-align:top}}code{{color:#79c0ff}}.warn{{color:#f2cc60}}</style></head><body>
<h1>Tiny Toon Visual Remaster — Gate A Review & Attestation</h1>
<div class='card'><h2>Explicitly verified: {s['verified_gate_a']}/{s['gate_a_total']}</h2><p>Awaiting human review: {s['awaiting_human_attestation']} · Blocked: {s['blocked_by_evidence']}</p><p>Capture fingerprint: <code>{html.escape(review['capture_fingerprint_sha256'])}</code></p><p class='warn'>{html.escape(review['policy'])}</p></div>
<div class='card'><h2>DO THIS NEXT</h2><p><b>{html.escape(str(n.get('criterion', n.get('kind', ''))))}</b></p><p>{html.escape(str(n.get('instruction', '')))}</p></div>
<div class='card'><h2>Roadmap patch preview</h2><p>{p['projected_completed_over_52']}/52 = {p['projected_percent']}% if these reviewed Gate A attestations are later reconciled and accepted into ROADMAP.</p></div>
<div class='card'><table><tr><th>#</th><th>Gate A criterion</th><th>Evidence</th><th>Review</th><th>Action</th></tr>{rows}</table></div>
</body></html>"""
    html_path.write_text(document, encoding="utf-8")
    return {"ledger": str(ledger_path), "review": str(review_path), "dashboard": str(html_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 fingerprint-bound Gate A review and attestation handoff")
    parser.add_argument("matrix_json", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--attest-index", type=int)
    parser.add_argument("--confirmation", default="")
    parser.add_argument("--reviewer", default="")
    args = parser.parse_args()

    matrix = _load_matrix(args.matrix_json)
    ledger_path = args.output / "GATE_A_ATTESTATIONS.json"
    ledger = _load_ledger(ledger_path, str(matrix["capture_fingerprint_sha256"]))
    if args.attest_index is not None:
        ledger = attest(matrix, ledger, args.attest_index, args.confirmation, args.reviewer)
    review = build_review(matrix, ledger)
    outputs = write_outputs(review, ledger, args.output)
    print(json.dumps({"summary": review["summary"], "next_action": review["next_action"], "roadmap_patch_preview": review["roadmap_patch_preview"], "outputs": outputs}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
