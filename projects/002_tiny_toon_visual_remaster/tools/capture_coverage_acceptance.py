from __future__ import annotations

import argparse
import csv
import html
import json
from datetime import datetime, timezone
from pathlib import Path

from capture_gap_planner import EXPECTED_ACTIONS, capture_profile
from capture_mission_control import MISSION_ITEMS, load_manifest
from local_capture_bridge import GROUP_ORDER, build_safe_evidence

SCHEMA = "swir.project002.capture-coverage-acceptance.v1"
REQUIRED_GROUPS = ("PLAYER", "BOSS", "ENEMY", "WORLD", "UI", "EFFECTS")
CSV_FIELDS = (
    "section",
    "key",
    "group",
    "status",
    "mapping_count",
    "family_count",
    "verified_in_game",
    "source_session",
    "source_fingerprint",
    "detail",
)


def _mission_rows(project_root: Path, evidence: dict) -> list[dict]:
    manifest_path = Path(project_root) / "CAPTURE_MISSIONS.json"
    manifest = load_manifest(manifest_path)
    bindings = {
        str(row.get("mission")): row
        for row in evidence.get("capture_integrity", {}).get("mission_evidence", {}).get("bindings", [])
        if isinstance(row, dict)
    }
    rows: list[dict] = []
    for key, label, group, priority in MISSION_ITEMS:
        mission = manifest.get("missions", {}).get(key, {})
        binding = bindings.get(key, {})
        done = bool(mission.get("done", False))
        verified = bool(binding.get("verified_in_game", False))
        source_fp = str(binding.get("capture_fingerprint_sha256", ""))
        if not done:
            status = "PENDING"
        elif not verified or not source_fp:
            status = "UNTRUSTED"
        else:
            status = "VERIFIED_IN_GAME"
        rows.append({
            "key": key,
            "label": label,
            "group": group,
            "priority": priority,
            "status": status,
            "done": done,
            "verified_in_game": verified,
            "source_session": binding.get("session"),
            "source_fingerprint_sha256": source_fp,
            "same_as_current_capture": bool(binding.get("same_as_current_capture", False)),
        })
    return rows


def _group_rows(capture: Path, evidence: dict, queue: Path | None) -> list[dict]:
    profile = capture_profile(Path(capture), queue)
    families_by_group: dict[str, list[dict]] = {group: [] for group in GROUP_ORDER}
    for family in profile.values():
        group = str(family.get("art_group", "UNASSIGNED")).upper()
        families_by_group.setdefault(group, []).append(family)

    mapping_groups = evidence.get("hd_pack", {}).get("groups", {})
    rows: list[dict] = []
    for group in GROUP_ORDER:
        families = families_by_group.get(group, [])
        missing_states: set[str] = set()
        state_gap_families = 0
        for family in families:
            missing = [str(value) for value in family.get("missing_expected_states", [])]
            if missing:
                state_gap_families += 1
                missing_states.update(missing)
        mappings = int(mapping_groups.get(group, 0) or 0)
        if group in REQUIRED_GROUPS and mappings <= 0:
            signal = "NO_CAPTURE_SIGNAL"
        elif mappings > 0:
            signal = "CAPTURE_SIGNAL_PRESENT"
        else:
            signal = "OPTIONAL_EMPTY"
        rows.append({
            "group": group,
            "mapping_count": mappings,
            "family_count": len(families),
            "state_gap_families": state_gap_families,
            "advisory_missing_states": sorted(missing_states),
            "expected_state_vocabulary": list(EXPECTED_ACTIONS.get(group, ())),
            "signal": signal,
            "important_note": "Group/state signals are structural guidance only. They never prove whole-game capture completeness.",
        })
    return rows


def build_acceptance_manifest(
    project_root: Path,
    capture: Path,
    *,
    previous_capture: Path | None = None,
) -> dict:
    project_root = Path(project_root)
    capture = Path(capture)
    evidence = build_safe_evidence(project_root, capture, previous_capture=previous_capture)
    queue = project_root / "Artwork" / "ART_QUEUE.csv"
    group_rows = _group_rows(capture, evidence, queue if queue.is_file() else None)
    mission_rows = _mission_rows(project_root, evidence)

    integrity = evidence.get("capture_integrity", {})
    mission_evidence = integrity.get("mission_evidence", {})
    blockers: list[dict] = []

    if integrity.get("admission_gate") != "PASS":
        blockers.append({"kind": "INTEGRITY_ADMISSION", "detail": "Capture Integrity Ledger admission is not PASS."})
    if integrity.get("structural_blockers"):
        blockers.append({"kind": "STRUCTURAL_CAPTURE", "detail": f"{len(integrity.get('structural_blockers', []))} structural blocker(s) remain."})
    if int(integrity.get("regression_count", 0) or 0) > 0:
        blockers.append({"kind": "CAPTURE_REGRESSION", "detail": f"{integrity.get('regression_count')} structural regression(s) remain."})
    if integrity.get("at_risk_missions"):
        blockers.append({"kind": "AT_RISK_MISSION", "detail": f"{len(integrity.get('at_risk_missions', []))} previously verified mission(s) are at risk."})

    pending = [row for row in mission_rows if row["status"] == "PENDING"]
    untrusted = [row for row in mission_rows if row["status"] == "UNTRUSTED"]
    if pending:
        blockers.append({"kind": "MISSION_COVERAGE", "detail": f"{len(pending)} authoritative capture mission(s) are still pending."})
    if untrusted:
        blockers.append({"kind": "MISSION_PROVENANCE", "detail": f"{len(untrusted)} completed mission(s) lack fingerprint-bound VERIFIED_IN_GAME provenance."})

    empty_groups = [row["group"] for row in group_rows if row["group"] in REQUIRED_GROUPS and row["mapping_count"] <= 0]
    if empty_groups:
        blockers.append({"kind": "GROUP_SIGNAL", "detail": "No captured mapping signal for required production group(s): " + ", ".join(empty_groups)})

    advisory_state_gaps = [
        {
            "group": row["group"],
            "families": row["state_gap_families"],
            "missing_states": row["advisory_missing_states"],
        }
        for row in group_rows
        if row["state_gap_families"] > 0
    ]

    current_fp = str(evidence.get("hd_pack", {}).get("capture_fingerprint", ""))
    mission_total = len(mission_rows)
    verified_total = sum(1 for row in mission_rows if row["status"] == "VERIFIED_IN_GAME")
    gate = "READY_FOR_GATE_A_REVIEW" if not blockers else "BLOCKED"

    next_action: dict
    if blockers:
        first = blockers[0]
        next_action = {"kind": first["kind"], "action": first["detail"]}
    elif advisory_state_gaps:
        first = advisory_state_gaps[0]
        next_action = {
            "kind": "ADVISORY_STATE_REVIEW",
            "action": f"Review {first['group']} animation families for advisory missing states before manually accepting Gate A.",
        }
    else:
        next_action = {
            "kind": "MANUAL_GATE_A_REVIEW",
            "action": "All hard capture acceptance checks are clean. Review real MesenCE gameplay evidence before changing any ROADMAP Gate A checkbox.",
        }

    return {
        "schema": SCHEMA,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "capture_fingerprint_sha256": current_fp,
        "acceptance_gate": gate,
        "roadmap_policy": "This manifest never edits or auto-completes Gate A-D. READY_FOR_GATE_A_REVIEW means only that hard metadata/provenance blockers are cleared; real local gameplay evidence remains authoritative.",
        "privacy_contract": evidence.get("privacy_contract", {}),
        "capture_integrity": {
            "admission_gate": integrity.get("admission_gate", "BLOCKED"),
            "integrity_gate": integrity.get("integrity_gate", "BLOCKED"),
            "regression_count": int(integrity.get("regression_count", 0) or 0),
            "structural_blockers": list(integrity.get("structural_blockers", [])),
            "at_risk_missions": list(integrity.get("at_risk_missions", [])),
        },
        "mission_summary": {
            "verified": verified_total,
            "total": mission_total,
            "untrusted_completed": len(untrusted),
            "pending": len(pending),
            "transport_verified_done": int(mission_evidence.get("verified_done", 0) or 0),
        },
        "missions": mission_rows,
        "groups": group_rows,
        "advisory_state_gaps": advisory_state_gaps,
        "hard_blockers": blockers,
        "next_action": next_action,
        "source_counts": {
            "mapping_count": int(evidence.get("hd_pack", {}).get("mapping_count", 0) or 0),
            "unique_tile_ids": int(evidence.get("hd_pack", {}).get("unique_tile_ids", 0) or 0),
            "unique_palettes": int(evidence.get("hd_pack", {}).get("unique_palettes", 0) or 0),
            "condition_count": int(evidence.get("hd_pack", {}).get("condition_count", 0) or 0),
            "referenced_images": len(evidence.get("hd_pack", {}).get("images", [])),
        },
    }


def _csv_rows(result: dict) -> list[dict]:
    rows: list[dict] = []
    for mission in result["missions"]:
        rows.append({
            "section": "mission",
            "key": mission["key"],
            "group": mission["group"],
            "status": mission["status"],
            "mapping_count": "",
            "family_count": "",
            "verified_in_game": mission["verified_in_game"],
            "source_session": mission.get("source_session") or "",
            "source_fingerprint": mission.get("source_fingerprint_sha256", ""),
            "detail": mission["label"],
        })
    for group in result["groups"]:
        rows.append({
            "section": "group",
            "key": group["group"],
            "group": group["group"],
            "status": group["signal"],
            "mapping_count": group["mapping_count"],
            "family_count": group["family_count"],
            "verified_in_game": "",
            "source_session": "",
            "source_fingerprint": result["capture_fingerprint_sha256"],
            "detail": "advisory missing states: " + (" | ".join(group["advisory_missing_states"]) or "none detected"),
        })
    return rows


def write_outputs(result: dict, output_dir: Path) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "CAPTURE_COVERAGE_ACCEPTANCE.json"
    csv_path = output_dir / "CAPTURE_COVERAGE_MATRIX.csv"
    html_path = output_dir / "CAPTURE_COVERAGE_ACCEPTANCE.html"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(_csv_rows(result))

    mission_html = "".join(
        "<tr>"
        f"<td><code>{html.escape(row['key'])}</code></td><td>{html.escape(row['group'])}</td>"
        f"<td>{html.escape(row['status'])}</td><td>{html.escape(str(row.get('source_session') or '—'))}</td>"
        f"<td><code>{html.escape(row.get('source_fingerprint_sha256') or '—')}</code></td><td>{html.escape(row['label'])}</td>"
        "</tr>"
        for row in result["missions"]
    )
    group_html = "".join(
        "<tr>"
        f"<td>{html.escape(row['group'])}</td><td>{row['mapping_count']}</td><td>{row['family_count']}</td>"
        f"<td>{html.escape(row['signal'])}</td><td>{row['state_gap_families']}</td>"
        f"<td>{html.escape(', '.join(row['advisory_missing_states']) or '—')}</td>"
        "</tr>"
        for row in result["groups"]
    )
    blocker_html = "".join(
        f"<li><b>{html.escape(row['kind'])}</b> — {html.escape(row['detail'])}</li>" for row in result["hard_blockers"]
    ) or "<li>None. Metadata/provenance checks are clean; real gameplay review is still required.</li>"
    document = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><title>Project #002 Capture Coverage Acceptance</title>
<style>body{{font:15px system-ui;max-width:1280px;margin:30px auto;padding:0 22px;background:#0d1117;color:#e6edf3}}.card{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:18px;margin:14px 0}}table{{width:100%;border-collapse:collapse}}td,th{{padding:8px;border-bottom:1px solid #30363d;text-align:left;vertical-align:top}}code{{color:#79c0ff;word-break:break-all}}.warn{{color:#f2cc60}}</style></head><body>
<h1>Tiny Toon Visual Remaster — Capture Coverage Acceptance</h1>
<div class='card'><h2>Gate: {html.escape(result['acceptance_gate'])}</h2><p>Fingerprint: <code>{html.escape(result['capture_fingerprint_sha256'])}</code></p><p>Verified missions: <b>{result['mission_summary']['verified']}/{result['mission_summary']['total']}</b> · pending {result['mission_summary']['pending']} · untrusted completed {result['mission_summary']['untrusted_completed']}</p><p class='warn'>{html.escape(result['roadmap_policy'])}</p></div>
<div class='card'><h2>Hard blockers</h2><ul>{blocker_html}</ul><p><b>DO THIS NEXT:</b> {html.escape(result['next_action']['action'])}</p></div>
<div class='card'><h2>Authoritative mission provenance</h2><table><tr><th>Mission</th><th>Group</th><th>Status</th><th>Session</th><th>Source fingerprint</th><th>Gameplay target</th></tr>{mission_html}</table></div>
<div class='card'><h2>Structural coverage matrix</h2><table><tr><th>Group</th><th>Mappings</th><th>Families</th><th>Signal</th><th>Families with advisory gaps</th><th>Advisory missing states</th></tr>{group_html}</table></div>
</body></html>"""
    html_path.write_text(document, encoding="utf-8")
    return {"json": str(json_path), "csv": str(csv_path), "dashboard": str(html_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 fingerprint-bound capture coverage acceptance manifest")
    parser.add_argument("project_root", type=Path)
    parser.add_argument("capture", type=Path)
    parser.add_argument("--previous-capture", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or (args.project_root / "Reports" / "CaptureCoverageAcceptance")
    result = build_acceptance_manifest(args.project_root, args.capture, previous_capture=args.previous_capture)
    outputs = write_outputs(result, output)
    print(json.dumps({
        "acceptance_gate": result["acceptance_gate"],
        "fingerprint": result["capture_fingerprint_sha256"],
        "verified_missions": result["mission_summary"]["verified"],
        "total_missions": result["mission_summary"]["total"],
        "hard_blockers": result["hard_blockers"],
        "next_action": result["next_action"],
        "outputs": outputs,
    }, indent=2))
    return 0 if result["acceptance_gate"] == "READY_FOR_GATE_A_REVIEW" else 2


if __name__ == "__main__":
    raise SystemExit(main())
