from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path

REVIEW_SCHEMA = "swir.project002.gate-a-review-attestation.v1"
SCHEMA = "swir.project002.capture-review-director.v1"
READY = "AWAITING_HUMAN_ATTESTATION"
VERIFIED = "VERIFIED_GATE_A"
BLOCKED = "BLOCKED_BY_EVIDENCE"
GATE_A_ITEMS = 12


class DirectorError(RuntimeError):
    pass


def _load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise DirectorError(f"{path.name}: expected a JSON object")
    return data


def build_director(review: dict) -> dict:
    if review.get("schema") != REVIEW_SCHEMA:
        raise DirectorError(f"Unsupported Gate A review schema: {review.get('schema')!r}")
    fingerprint = str(review.get("capture_fingerprint_sha256", ""))
    if not fingerprint:
        raise DirectorError("Gate A review handoff is missing capture_fingerprint_sha256.")
    criteria = review.get("criteria")
    if not isinstance(criteria, list) or len(criteria) != GATE_A_ITEMS:
        raise DirectorError(f"Gate A review handoff must contain exactly {GATE_A_ITEMS} criteria.")

    normalized = []
    seen = set()
    for row in criteria:
        if not isinstance(row, dict):
            raise DirectorError("Gate A criterion rows must be JSON objects.")
        index = int(row.get("index", 0) or 0)
        if index < 1 or index > GATE_A_ITEMS or index in seen:
            raise DirectorError(f"Invalid or duplicate Gate A criterion index: {index}")
        seen.add(index)
        row_fp = str(row.get("capture_fingerprint_sha256", ""))
        source_fp = str(row.get("source_fingerprint_sha256", ""))
        status = str(row.get("review_status", ""))
        if row_fp != fingerprint:
            raise DirectorError(f"Criterion {index} belongs to a different capture fingerprint.")
        if status in {READY, VERIFIED} and not source_fp:
            raise DirectorError(f"Criterion {index} is reviewable/verified but lacks source fingerprint.")
        if status not in {READY, VERIFIED, BLOCKED}:
            raise DirectorError(f"Criterion {index} has unsupported review status: {status!r}")
        normalized.append({
            "index": index,
            "criterion": str(row.get("criterion", "")),
            "mission_key": str(row.get("mission_key", "")),
            "review_status": status,
            "evidence_status": str(row.get("evidence_status", "")),
            "source_fingerprint_sha256": source_fp,
            "next_action": str(row.get("next_action", "")),
        })

    normalized.sort(key=lambda item: item["index"])
    reviewable = [row for row in normalized if row["review_status"] == READY]
    verified = [row for row in normalized if row["review_status"] == VERIFIED]
    blocked = [row for row in normalized if row["review_status"] == BLOCKED]

    if reviewable:
        first = reviewable[0]
        state = "REVIEW_REQUIRED"
        action = {
            "kind": "ATTEST_NEXT_READY_CRITERION",
            "index": first["index"],
            "criterion": first["criterion"],
            "instruction": "Review the exact current local MesenCE gameplay evidence, then type VERIFIED_GATE_A only if this criterion is genuinely satisfied.",
        }
    elif blocked:
        first = blocked[0]
        state = "CAPTURE_WORK_REQUIRED"
        action = {
            "kind": "RETURN_TO_CAPTURE",
            "index": first["index"],
            "criterion": first["criterion"],
            "instruction": first["next_action"] or "Return to the next-best capture loop and gather the missing real gameplay evidence.",
        }
    else:
        state = "GATE_A_REVIEW_COMPLETE"
        action = {
            "kind": "ROADMAP_PATCH_READY",
            "criterion": "All Gate A criteria are explicitly verified for this exact capture fingerprint.",
            "instruction": "Run the ROADMAP Patch Director and review its Project/Master diff before proposing a repository change.",
        }

    return {
        "schema": SCHEMA,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "capture_fingerprint_sha256": fingerprint,
        "state": state,
        "summary": {
            "verified": len(verified),
            "reviewable": len(reviewable),
            "blocked": len(blocked),
            "total": GATE_A_ITEMS,
        },
        "review_queue": reviewable,
        "criteria": normalized,
        "next_action": action,
        "policy": "This director never records an attestation and never edits ROADMAP.md. Explicit local VERIFIED_GATE_A confirmation remains mandatory for each reviewable criterion.",
    }


def write_outputs(result: dict, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "CAPTURE_REVIEW_DIRECTOR.json"
    html_path = output_dir / "CAPTURE_REVIEW_DIRECTOR.html"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    queue_rows = "".join(
        "<tr>"
        f"<td>{row['index']}</td>"
        f"<td>{html.escape(row['criterion'])}</td>"
        f"<td>{html.escape(row['mission_key'])}</td>"
        f"<td><code>{html.escape(row['source_fingerprint_sha256'])}</code></td>"
        "</tr>"
        for row in result["review_queue"]
    ) or "<tr><td colspan='4'>No evidence-ready criteria waiting for explicit review.</td></tr>"
    action = result["next_action"]
    summary = result["summary"]
    document = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><title>Capture Review Director</title>
<style>body{{font:15px system-ui;max-width:1400px;margin:28px auto;padding:0 22px;background:#0d1117;color:#e6edf3}}.card{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:18px;margin:14px 0}}table{{width:100%;border-collapse:collapse}}td,th{{padding:8px;border-bottom:1px solid #30363d;text-align:left;vertical-align:top}}code{{color:#79c0ff}}.warn{{color:#f2cc60}}</style></head><body>
<h1>Tiny Toon Visual Remaster — Capture → Review Director</h1>
<div class='card'><h2>{html.escape(result['state'])}</h2><p>Verified: {summary['verified']}/{summary['total']} · Ready for review: {summary['reviewable']} · Blocked: {summary['blocked']}</p><p>Capture fingerprint: <code>{html.escape(result['capture_fingerprint_sha256'])}</code></p><p class='warn'>{html.escape(result['policy'])}</p></div>
<div class='card'><h2>DO THIS NEXT</h2><p><b>{html.escape(str(action.get('criterion', action.get('kind', ''))))}</b></p><p>{html.escape(str(action.get('instruction', '')))}</p></div>
<div class='card'><h2>Evidence-ready review queue</h2><table><tr><th>#</th><th>Criterion</th><th>Mission</th><th>Evidence fingerprint</th></tr>{queue_rows}</table></div>
</body></html>"""
    html_path.write_text(document, encoding="utf-8")
    return {"json": str(json_path), "dashboard": str(html_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 one-step Gate A capture review queue director")
    parser.add_argument("review_json", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_director(_load_json(args.review_json))
    outputs = write_outputs(result, args.output)
    print(json.dumps({"state": result["state"], "summary": result["summary"], "next_action": result["next_action"], "outputs": outputs}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
