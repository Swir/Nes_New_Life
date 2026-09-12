from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path

from release_candidate import REGRESSION_CASES, ensure_regression_manifest, pack_fingerprint

FAILURE_CATEGORIES = (
    "MISSING_HD",
    "WRONG_PALETTE",
    "ANIMATION_SEAM",
    "TRANSPARENCY",
    "MAPPING",
    "SCALE_OR_FILTER",
    "CAPTURE_GAP",
    "OTHER",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _raw_manifest(path: Path) -> dict:
    ensure_regression_manifest(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise ValueError(f"Invalid regression manifest: {exc}") from exc
    if not isinstance(data, dict):
        data = {}
    cases = data.setdefault("cases", {})
    for key, label in REGRESSION_CASES:
        item = cases.setdefault(key, {})
        item.setdefault("label", label)
        item.setdefault("done", False)
        item.setdefault("notes", "")
        item.setdefault("pack_fingerprint", None)
        item.setdefault("completed_utc", None)
        item.setdefault("result", "PASS" if item.get("done") else "PENDING")
        item.setdefault("failure_category", "")
        item.setdefault("failure_notes", "")
        item.setdefault("tested_utc", item.get("completed_utc"))
    data.setdefault("schema", 2)
    data.setdefault("history", [])
    data.setdefault("warning", "Regression evidence is exact-build-specific; any runtime art or hires.txt change makes old PASS evidence stale.")
    return data


def _case_state(item: dict, fingerprint: str) -> str:
    recorded_fp = item.get("pack_fingerprint")
    result = str(item.get("result") or ("PASS" if item.get("done") else "PENDING")).upper()
    if recorded_fp and recorded_fp != fingerprint:
        return "STALE"
    if result == "FAIL":
        return "FAIL"
    if bool(item.get("done")) and recorded_fp == fingerprint:
        return "PASS"
    return "PENDING"


def cockpit_status(manifest_path: Path, pack_dir: Path) -> dict:
    manifest_path = Path(manifest_path)
    pack_dir = Path(pack_dir)
    fingerprint = pack_fingerprint(pack_dir)
    if fingerprint == "MISSING_HIRES":
        raise ValueError("Cannot run final regression without hires.txt")
    data = _raw_manifest(manifest_path)
    rows: list[dict] = []
    counts = {"PASS": 0, "FAIL": 0, "STALE": 0, "PENDING": 0}
    for order, (key, label) in enumerate(REGRESSION_CASES, start=1):
        item = data["cases"][key]
        state = _case_state(item, fingerprint)
        counts[state] += 1
        rows.append({
            "order": order,
            "key": key,
            "label": label,
            "state": state,
            "notes": str(item.get("notes") or ""),
            "failure_category": str(item.get("failure_category") or ""),
            "failure_notes": str(item.get("failure_notes") or ""),
            "tested_utc": item.get("tested_utc"),
            "pack_fingerprint": item.get("pack_fingerprint"),
        })
    next_row = next((row for row in rows if row["state"] == "FAIL"), None)
    if next_row is None:
        next_row = next((row for row in rows if row["state"] in {"PENDING", "STALE"}), None)
    return {
        "schema": 1,
        "generated_utc": _now(),
        "pack_fingerprint": fingerprint,
        "gate": "PASS" if counts["PASS"] == len(rows) else "BLOCKED",
        "total": len(rows),
        "counts": counts,
        "next_case": next_row,
        "cases": rows,
        "important_note": "PASS means the tester visually verified that case in MesenCE against this exact HD-pack fingerprint. The cockpit never auto-passes gameplay states.",
    }


def record_case_result(
    manifest_path: Path,
    case_key: str,
    pack_dir: Path,
    result: str,
    *,
    notes: str = "",
    failure_category: str = "OTHER",
    failure_notes: str = "",
) -> dict:
    result = result.strip().upper()
    if result not in {"PASS", "FAIL"}:
        raise ValueError("result must be PASS or FAIL")
    known = {key for key, _ in REGRESSION_CASES}
    if case_key not in known:
        raise ValueError(f"Unknown regression case: {case_key}")
    fingerprint = pack_fingerprint(Path(pack_dir))
    if fingerprint == "MISSING_HIRES":
        raise ValueError("Cannot record regression evidence for a pack without hires.txt")
    if result == "FAIL":
        failure_category = failure_category.strip().upper() or "OTHER"
        if failure_category not in FAILURE_CATEGORIES:
            raise ValueError("Unknown failure category: " + failure_category)
    else:
        failure_category = ""
        failure_notes = ""

    path = Path(manifest_path)
    data = _raw_manifest(path)
    item = data["cases"][case_key]
    timestamp = _now()
    item.update({
        "done": result == "PASS",
        "notes": notes,
        "pack_fingerprint": fingerprint,
        "completed_utc": timestamp if result == "PASS" else None,
        "result": result,
        "failure_category": failure_category,
        "failure_notes": failure_notes,
        "tested_utc": timestamp,
    })
    data["schema"] = 2
    data["history"].append({
        "utc": timestamp,
        "case": case_key,
        "result": result,
        "pack_fingerprint": fingerprint,
        "failure_category": failure_category,
        "notes": notes,
        "failure_notes": failure_notes,
    })
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return {"case": case_key, "result": result, "pack_fingerprint": fingerprint, "tested_utc": timestamp}


def reset_case(manifest_path: Path, case_key: str) -> dict:
    known = {key for key, _ in REGRESSION_CASES}
    if case_key not in known:
        raise ValueError(f"Unknown regression case: {case_key}")
    path = Path(manifest_path)
    data = _raw_manifest(path)
    item = data["cases"][case_key]
    item.update({
        "done": False,
        "notes": "",
        "pack_fingerprint": None,
        "completed_utc": None,
        "result": "PENDING",
        "failure_category": "",
        "failure_notes": "",
        "tested_utc": None,
    })
    data["history"].append({"utc": _now(), "case": case_key, "result": "RESET"})
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return item


def write_dashboard(status: dict, output_dir: Path) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "FINAL_REGRESSION_COCKPIT.json"
    html_path = output_dir / "FINAL_REGRESSION_COCKPIT.html"
    json_path.write_text(json.dumps(status, indent=2), encoding="utf-8")

    rows = []
    for case in status["cases"]:
        details = case["notes"]
        if case["state"] == "FAIL":
            details = " · ".join(part for part in [case["failure_category"], case["failure_notes"], case["notes"]] if part)
        rows.append(
            "<tr>"
            f"<td>{case['order']}</td><td class='{case['state'].lower()}'>{case['state']}</td>"
            f"<td><code>{html.escape(case['key'])}</code></td><td>{html.escape(case['label'])}</td>"
            f"<td>{html.escape(details)}</td></tr>"
        )
    next_case = status.get("next_case")
    next_text = "All cases PASS for this exact build." if next_case is None else f"{next_case['order']}. {next_case['label']} ({next_case['state']})"
    counts = status["counts"]
    document = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><title>Project #002 Final Regression Cockpit</title>
<style>body{{font:15px system-ui;max-width:1250px;margin:30px auto;padding:0 22px;background:#0d1117;color:#e6edf3}}.card{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:16px;margin:12px 0}}table{{width:100%;border-collapse:collapse}}th,td{{padding:8px;border-bottom:1px solid #30363d;text-align:left;vertical-align:top}}code{{color:#79c0ff}}.pass{{color:#3fb950}}.fail{{color:#f85149}}.stale{{color:#d29922}}.pending{{color:#8b949e}}</style></head><body>
<h1>Tiny Toon Visual Remaster — Final Regression Cockpit</h1>
<div class='card'><h2>Gate: {status['gate']}</h2><p>{html.escape(status['important_note'])}</p><p><b>Exact build:</b> <code>{status['pack_fingerprint']}</code></p><p>PASS {counts['PASS']} · FAIL {counts['FAIL']} · STALE {counts['STALE']} · PENDING {counts['PENDING']}</p><h3>DO THIS NEXT</h3><p>{html.escape(next_text)}</p></div>
<div class='card'><h2>Full-game visual regression</h2><table><tr><th>#</th><th>Status</th><th>Case</th><th>What to verify in MesenCE</th><th>Notes / failure</th></tr>{''.join(rows)}</table></div>
<div class='card'><h2>Failure categories</h2><p>{html.escape(' · '.join(FAILURE_CATEGORIES))}</p><p>A FAIL remains a release blocker until the same case is re-tested and marked PASS on the current fingerprint. Any later runtime PNG or hires.txt change makes prior PASS evidence STALE.</p></div></body></html>"""
    html_path.write_text(document, encoding="utf-8")
    return {"json": str(json_path), "dashboard": str(html_path)}


def build_and_write(manifest: Path, pack: Path, output: Path) -> dict:
    status = cockpit_status(manifest, pack)
    status["outputs"] = write_dashboard(status, output)
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 exact-build final regression cockpit")
    sub = parser.add_subparsers(dest="command", required=True)
    status = sub.add_parser("status"); status.add_argument("manifest", type=Path); status.add_argument("pack", type=Path); status.add_argument("--output", type=Path, required=True)
    for name in ("pass", "fail"):
        cmd = sub.add_parser(name); cmd.add_argument("manifest", type=Path); cmd.add_argument("case"); cmd.add_argument("pack", type=Path); cmd.add_argument("--notes", default="")
        if name == "fail":
            cmd.add_argument("--category", choices=FAILURE_CATEGORIES, default="OTHER"); cmd.add_argument("--failure-notes", default="")
    reset = sub.add_parser("reset"); reset.add_argument("manifest", type=Path); reset.add_argument("case")
    args = parser.parse_args()
    if args.command == "status":
        result = build_and_write(args.manifest, args.pack, args.output)
    elif args.command == "reset":
        result = reset_case(args.manifest, args.case)
    else:
        result = record_case_result(args.manifest, args.case, args.pack, args.command.upper(), notes=args.notes, failure_category=getattr(args, "category", "OTHER"), failure_notes=getattr(args, "failure_notes", ""))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
