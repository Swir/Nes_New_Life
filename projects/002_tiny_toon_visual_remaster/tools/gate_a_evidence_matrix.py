from __future__ import annotations

import argparse
import csv
import html
import json
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "swir.project002.gate-a-evidence-matrix.v1"
ACCEPTANCE_SCHEMA = "swir.project002.capture-coverage-acceptance.v1"

MISSION_CRITERIA = (
    ("boot_title_menu", "Boot/title/menu states"),
    ("player_idle_walk_run", "Player idle/walk/run/crouch/jump/fall/land"),
    ("player_actions_damage_death", "Player actions, damage, invulnerability and death"),
    ("world_route_1", "Every normal route and scrolling boundary"),
    ("world_route_2", "Alternate routes, secrets and revisits"),
    ("common_enemies", "Every common enemy state"),
    ("rare_enemies", "Rare/route-specific enemies"),
    ("bosses_all_phases", "Every boss phase, attack, hit/death and effect"),
    ("hud_text_status", "HUD, text, pause/status/result screens"),
    ("effects_transitions", "Effects, projectiles and transitions"),
    ("ending_credits", "Ending, credits and post-game states"),
)
REGRESSION_CRITERION = "Compare repeated captures and resolve every CAPTURE_REGRESSION before promoting a newer capture to production baseline"
CSV_FIELDS = ("index", "criterion", "mission_key", "status", "reason", "capture_fingerprint_sha256", "source_fingerprint_sha256")


def _load_json(path: Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Acceptance manifest must be a JSON object.")
    if data.get("schema") != ACCEPTANCE_SCHEMA:
        raise ValueError(f"Unsupported acceptance schema: {data.get('schema')!r}")
    return data


def build_matrix(acceptance: dict) -> dict:
    missions = {
        str(row.get("key")): row
        for row in acceptance.get("missions", [])
        if isinstance(row, dict) and row.get("key")
    }
    integrity = acceptance.get("capture_integrity", {}) if isinstance(acceptance.get("capture_integrity"), dict) else {}
    capture_fp = str(acceptance.get("capture_fingerprint_sha256", ""))
    admission_ok = integrity.get("admission_gate") == "PASS"
    structural_ok = not integrity.get("structural_blockers")
    regression_count = int(integrity.get("regression_count", 0) or 0)
    at_risk = {str(value) for value in integrity.get("at_risk_missions", [])}

    rows: list[dict] = []
    for index, (mission_key, criterion) in enumerate(MISSION_CRITERIA, start=1):
        mission = missions.get(mission_key, {})
        mission_status = str(mission.get("status", "MISSING"))
        source_fp = str(mission.get("source_fingerprint_sha256", ""))
        if mission_status != "VERIFIED_IN_GAME":
            status = "PENDING_EVIDENCE"
            reason = f"Mission {mission_key} is {mission_status}; explicit VERIFIED_IN_GAME evidence is required."
        elif mission_key in at_risk:
            status = "BLOCKED_AT_RISK"
            reason = "Previously verified mission is marked at-risk by Capture Integrity Ledger."
        elif not admission_ok or not structural_ok or regression_count > 0:
            status = "BLOCKED_CAPTURE_INTEGRITY"
            reason = "Mission evidence exists, but current capture integrity/regression admission is not clean."
        elif not source_fp:
            status = "BLOCKED_PROVENANCE"
            reason = "Verified mission is missing its source capture fingerprint."
        else:
            status = "EVIDENCE_READY_FOR_REVIEW"
            reason = "Fingerprint-bound VERIFIED_IN_GAME evidence is present and current capture integrity is clean."
        rows.append({
            "index": index,
            "criterion": criterion,
            "mission_key": mission_key,
            "status": status,
            "reason": reason,
            "capture_fingerprint_sha256": capture_fp,
            "source_fingerprint_sha256": source_fp,
        })

    if not admission_ok or not structural_ok:
        regression_status = "BLOCKED_CAPTURE_INTEGRITY"
        regression_reason = "Capture Integrity Ledger admission/structure is not clean."
    elif regression_count > 0:
        regression_status = "PENDING_REGRESSION_REPAIR"
        regression_reason = f"{regression_count} CAPTURE_REGRESSION finding(s) remain."
    elif at_risk:
        regression_status = "BLOCKED_AT_RISK"
        regression_reason = f"{len(at_risk)} verified mission(s) remain at-risk."
    else:
        regression_status = "EVIDENCE_READY_FOR_REVIEW"
        regression_reason = "Current acceptance manifest reports zero structural regressions and no at-risk verified missions."
    rows.append({
        "index": 12,
        "criterion": REGRESSION_CRITERION,
        "mission_key": "capture_regression_resolution",
        "status": regression_status,
        "reason": regression_reason,
        "capture_fingerprint_sha256": capture_fp,
        "source_fingerprint_sha256": capture_fp,
    })

    ready = sum(1 for row in rows if row["status"] == "EVIDENCE_READY_FOR_REVIEW")
    blocked = len(rows) - ready
    next_row = next((row for row in rows if row["status"] != "EVIDENCE_READY_FOR_REVIEW"), None)
    return {
        "schema": SCHEMA,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source_acceptance_schema": acceptance.get("schema"),
        "capture_fingerprint_sha256": capture_fp,
        "acceptance_gate": acceptance.get("acceptance_gate", "BLOCKED"),
        "roadmap_policy": (
            "This matrix never edits ROADMAP.md and never turns evidence readiness into completion. "
            "A checkbox may be changed only after real local gameplay evidence has been reviewed."
        ),
        "summary": {"evidence_ready": ready, "remaining": blocked, "total": len(rows)},
        "criteria": rows,
        "next_action": (
            {"kind": next_row["status"], "criterion": next_row["criterion"], "reason": next_row["reason"]}
            if next_row
            else {
                "kind": "MANUAL_GATE_A_CHECKLIST_REVIEW",
                "criterion": "All Gate A criteria have evidence ready for review",
                "reason": "Review the real local MesenCE gameplay evidence before changing any ROADMAP checkbox.",
            }
        ),
    }


def write_outputs(result: dict, output_dir: Path) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "GATE_A_EVIDENCE_MATRIX.json"
    csv_path = output_dir / "GATE_A_EVIDENCE_MATRIX.csv"
    html_path = output_dir / "GATE_A_EVIDENCE_MATRIX.html"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in CSV_FIELDS} for row in result["criteria"])

    rows = "".join(
        "<tr>"
        f"<td>{row['index']}</td><td>{html.escape(row['criterion'])}</td>"
        f"<td><code>{html.escape(row['mission_key'])}</code></td>"
        f"<td>{html.escape(row['status'])}</td><td>{html.escape(row['reason'])}</td>"
        "</tr>"
        for row in result["criteria"]
    )
    summary = result["summary"]
    next_action = result["next_action"]
    document = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><title>Project #002 Gate A Evidence Matrix</title>
<style>body{{font:15px system-ui;max-width:1300px;margin:28px auto;padding:0 22px;background:#0d1117;color:#e6edf3}}.card{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:18px;margin:14px 0}}table{{width:100%;border-collapse:collapse}}td,th{{padding:8px;border-bottom:1px solid #30363d;text-align:left;vertical-align:top}}code{{color:#79c0ff}}.warn{{color:#f2cc60}}</style></head><body>
<h1>Tiny Toon Visual Remaster — Gate A Evidence Matrix</h1>
<div class='card'><h2>Evidence-ready: {summary['evidence_ready']}/{summary['total']}</h2><p>Capture fingerprint: <code>{html.escape(result['capture_fingerprint_sha256'])}</code></p><p>Acceptance: <b>{html.escape(str(result['acceptance_gate']))}</b></p><p class='warn'>{html.escape(result['roadmap_policy'])}</p></div>
<div class='card'><h2>DO THIS NEXT</h2><p><b>{html.escape(next_action['criterion'])}</b></p><p>{html.escape(next_action['reason'])}</p></div>
<div class='card'><table><tr><th>#</th><th>Gate A criterion</th><th>Evidence source</th><th>Status</th><th>Reason</th></tr>{rows}</table></div>
</body></html>"""
    html_path.write_text(document, encoding="utf-8")
    return {"json": str(json_path), "csv": str(csv_path), "dashboard": str(html_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 fingerprint-bound Gate A evidence matrix")
    parser.add_argument("acceptance_json", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    acceptance = _load_json(args.acceptance_json)
    result = build_matrix(acceptance)
    outputs = write_outputs(result, args.output)
    print(json.dumps({"summary": result["summary"], "next_action": result["next_action"], "outputs": outputs}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
