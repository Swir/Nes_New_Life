from __future__ import annotations

import argparse
import hashlib
import html
import json
from datetime import datetime, timezone
from pathlib import Path

from capture_mission_control import load_manifest, snapshot_capture

METRIC_KEYS = ("tile_rules", "unique_tile_ids", "unique_palettes", "images")
STRUCTURAL_BLOCKERS = {
    "capture_scale_is_not_4x",
    "missing_referenced_images",
    "capture_regression_against_verified_history",
    "verified_mission_evidence_at_risk",
}
RECOVERABLE_GAMEPLAY_BLOCKERS = {
    "capture_regression_against_verified_history",
    "verified_mission_evidence_at_risk",
}
HARD_PREFLIGHT_BLOCKERS = STRUCTURAL_BLOCKERS - RECOVERABLE_GAMEPLAY_BLOCKERS


def capture_fingerprint(capture_dir: Path) -> str:
    capture_dir = Path(capture_dir)
    hires = capture_dir / "hires.txt"
    if not hires.is_file():
        raise ValueError("Capture folder must contain hires.txt")
    digest = hashlib.sha256()
    digest.update(hires.read_bytes())
    referenced = []
    for line in hires.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line.lower().startswith("<img>"):
            name = line[5:].strip()
            if name:
                referenced.append(name)
    for name in sorted(set(referenced)):
        path = capture_dir / name
        digest.update(name.encode("utf-8", errors="replace"))
        if path.is_file():
            digest.update(path.read_bytes())
        else:
            digest.update(b"<MISSING>")
    return digest.hexdigest()


def _recovery_state(structural_blockers: list[str], regressions: list[dict], at_risk: list[dict]) -> dict:
    blockers = set(structural_blockers)
    hard = sorted(blockers & HARD_PREFLIGHT_BLOCKERS)
    recoverable = sorted(blockers & RECOVERABLE_GAMEPLAY_BLOCKERS)
    if hard:
        mode = "HARD_BLOCKED"
    elif recoverable:
        mode = "GAMEPLAY_RECOVERY_REQUIRED"
    else:
        mode = "CLEAN"

    targets: list[dict] = []
    for row in regressions:
        deficit = max(0, int(row.get("historical_max", 0)) - int(row.get("current", 0)))
        targets.append({
            "kind": "RESTORE_CAPTURE_METRIC",
            "metric": str(row.get("metric", "")),
            "current": int(row.get("current", 0)),
            "target_minimum": int(row.get("historical_max", 0)),
            "deficit": deficit,
            "action": f"Replay gameplay that previously exposed {row.get('metric', 'capture data')} until the current capture reaches at least the verified historical maximum.",
        })
    for row in at_risk:
        targets.append({
            "kind": "REVERIFY_AT_RISK_MISSION",
            "mission": str(row.get("mission", "")),
            "session": row.get("session"),
            "metrics": list(row.get("metrics", [])),
            "action": f"Revisit gameplay for {row.get('mission', 'the affected mission')} after structural coverage has been restored; do not record new VERIFIED_IN_GAME evidence while admission is blocked.",
        })
    return {
        "mode": mode,
        "gameplay_launch_allowed": mode in {"CLEAN", "GAMEPLAY_RECOVERY_REQUIRED"},
        "mission_recording_allowed": mode == "CLEAN",
        "hard_blockers": hard,
        "recoverable_blockers": recoverable,
        "targets": targets,
    }


def build_ledger(manifest_path: Path, capture_dir: Path) -> dict:
    data = load_manifest(manifest_path)
    current = snapshot_capture(capture_dir)
    fingerprint = capture_fingerprint(capture_dir)
    sessions = list(data.get("sessions", []))
    historical_max = {key: 0 for key in METRIC_KEYS}
    regressions = []
    for session in sessions:
        snap = session.get("capture", {})
        for key in METRIC_KEYS:
            historical_max[key] = max(historical_max[key], int(snap.get(key, 0) or 0))
    for key in METRIC_KEYS:
        now = int(current.get(key, 0) or 0)
        old = int(historical_max[key])
        if now < old:
            regressions.append({"metric": key, "current": now, "historical_max": old, "delta": now - old})

    at_risk = []
    by_id = {int(s.get("id", 0)): s for s in sessions if s.get("id") is not None}
    for key, mission in data["missions"].items():
        if not mission.get("done"):
            continue
        sid = mission.get("last_session")
        session = by_id.get(int(sid)) if sid is not None else None
        if session is None:
            at_risk.append({"mission": key, "reason": "missing_session_evidence", "session": sid})
            continue
        snap = session.get("capture", {})
        lost = [metric for metric in METRIC_KEYS if int(current.get(metric, 0) or 0) < int(snap.get(metric, 0) or 0)]
        if lost:
            at_risk.append({"mission": key, "reason": "current_capture_below_verified_session", "session": sid, "metrics": lost})

    done = sum(1 for item in data["missions"].values() if item.get("done"))
    total = len(data["missions"])
    blockers = []
    if int(current.get("scale", 0) or 0) != 4:
        blockers.append("capture_scale_is_not_4x")
    if current.get("missing_images"):
        blockers.append("missing_referenced_images")
    if regressions:
        blockers.append("capture_regression_against_verified_history")
    if at_risk:
        blockers.append("verified_mission_evidence_at_risk")
    structural_blockers = [item for item in blockers if item in STRUCTURAL_BLOCKERS]
    admission_gate = "PASS" if not structural_blockers else "BLOCKED"
    recovery = _recovery_state(structural_blockers, regressions, at_risk)
    if done != total:
        blockers.append("capture_missions_incomplete")

    return {
        "schema": "swir.project002.capture-integrity-ledger.v3",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "capture_fingerprint_sha256": fingerprint,
        "capture": current,
        "historical_max": historical_max,
        "missions": {"done": done, "total": total, "percent": round((done / total) * 100, 1) if total else 0.0},
        "regressions": regressions,
        "at_risk_missions": at_risk,
        "structural_blockers": structural_blockers,
        "admission_gate": admission_gate,
        "recovery": recovery,
        "blockers": blockers,
        "integrity_gate": "PASS" if not blockers else "BLOCKED",
        "policy": "Mission completion remains explicit human gameplay evidence. Structural admission must PASS before a new mission can be recorded. Recoverable history regressions may launch MesenCE in gameplay recovery mode, but recording remains blocked until admission returns to PASS. This ledger never auto-completes a mission.",
    }


def assert_capture_admissible(manifest_path: Path, capture_dir: Path) -> dict:
    ledger = build_ledger(manifest_path, capture_dir)
    if ledger["admission_gate"] != "PASS":
        details = ", ".join(ledger["structural_blockers"]) or "unknown_capture_integrity_blocker"
        raise ValueError(f"Capture admission blocked: {details}")
    return ledger


def write_dashboard(manifest_path: Path, capture_dir: Path, output: Path) -> Path:
    ledger = build_ledger(manifest_path, capture_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    regression_rows = "".join(
        f"<tr><td>{html.escape(r['metric'])}</td><td>{r['historical_max']}</td><td>{r['current']}</td><td>{r['delta']}</td></tr>"
        for r in ledger["regressions"]
    ) or "<tr><td colspan='4'>No structural regression against verified history.</td></tr>"
    risk_rows = "".join(
        f"<tr><td><code>{html.escape(r['mission'])}</code></td><td>{html.escape(r['reason'])}</td><td>{html.escape(', '.join(r.get('metrics', [])) or str(r.get('session', '—')))}</td></tr>"
        for r in ledger["at_risk_missions"]
    ) or "<tr><td colspan='3'>No completed mission is structurally at risk.</td></tr>"
    blockers = "".join(f"<li>{html.escape(item)}</li>" for item in ledger["blockers"]) or "<li>None</li>"
    structural = "".join(f"<li>{html.escape(item)}</li>" for item in ledger["structural_blockers"]) or "<li>None</li>"
    recovery_rows = "".join(
        f"<li><b>{html.escape(item['kind'])}</b> — {html.escape(item['action'])}</li>"
        for item in ledger["recovery"]["targets"]
    ) or "<li>No recovery targets.</li>"
    output.write_text(
        f"""<!doctype html><meta charset='utf-8'><title>Project #002 Capture Integrity Ledger</title>
<style>body{{font:15px system-ui;max-width:1100px;margin:30px auto;padding:0 22px;background:#0d1117;color:#e6edf3}}.card{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:16px;margin:12px 0}}table{{width:100%;border-collapse:collapse}}td,th{{padding:8px;border-bottom:1px solid #30363d;text-align:left}}code{{color:#79c0ff}}</style>
<h1>Capture Integrity Ledger</h1><div class='card'><h2>Mission admission gate: {ledger['admission_gate']}</h2><p>Recovery mode: <b>{ledger['recovery']['mode']}</b> · gameplay launch allowed: <b>{ledger['recovery']['gameplay_launch_allowed']}</b> · mission recording allowed: <b>{ledger['recovery']['mission_recording_allowed']}</b></p><p>Missions: {ledger['missions']['done']}/{ledger['missions']['total']} ({ledger['missions']['percent']}%)</p><p>Fingerprint: <code>{ledger['capture_fingerprint_sha256']}</code></p><h3>Structural blockers</h3><ul>{structural}</ul><h3>Recovery targets</h3><ul>{recovery_rows}</ul><h3>Full release-integrity blockers</h3><ul>{blockers}</ul><p>{html.escape(ledger['policy'])}</p></div>
<div class='card'><h2>Structural regression check</h2><table><tr><th>Metric</th><th>Historical max</th><th>Current</th><th>Delta</th></tr>{regression_rows}</table></div>
<div class='card'><h2>Verified mission evidence at risk</h2><table><tr><th>Mission</th><th>Reason</th><th>Details</th></tr>{risk_rows}</table></div>""",
        encoding="utf-8",
    )
    output.with_suffix(".json").write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 capture integrity ledger")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("capture", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--admission-only", action="store_true")
    args = parser.parse_args()
    if args.output:
        print(write_dashboard(args.manifest, args.capture, args.output))
        ledger = build_ledger(args.manifest, args.capture)
    else:
        ledger = build_ledger(args.manifest, args.capture)
        print(json.dumps(ledger, indent=2))
    gate = ledger["admission_gate"] if args.admission_only else ledger["integrity_gate"]
    return 0 if gate == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())