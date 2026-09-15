from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path

from final_regression_cockpit import FAILURE_CATEGORIES, cockpit_status, record_case_result
from guided_regression_playtest import CASE_GUIDANCE
from release_candidate import pack_fingerprint
from regression_capture_gap_recovery import TOKEN_SCHEMA as RECOVERY_TOKEN_SCHEMA

SCHEMA = "swir.project002.regression-capture-gap-retest.v1"
RETEST_TOKEN_SCHEMA = "swir.project002.regression-capture-gap-retest-token.v1"


class CaptureGapRetestError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> dict:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CaptureGapRetestError(f"Missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CaptureGapRetestError(f"Invalid JSON: {path}") from exc
    if not isinstance(data, dict):
        raise CaptureGapRetestError(f"Expected JSON object: {path}")
    return data


def _history_has_source_fail(project_root: Path, case_key: str, source_runtime_fp: str) -> bool:
    manifest = _load_json(Path(project_root) / "FINAL_REGRESSION.json")
    for row in manifest.get("history", []):
        if not isinstance(row, dict):
            continue
        if (
            str(row.get("case") or "") == case_key
            and str(row.get("result") or "").upper() == "FAIL"
            and str(row.get("failure_category") or "").upper() == "CAPTURE_GAP"
            and str(row.get("pack_fingerprint") or "") == source_runtime_fp
        ):
            return True
    return False


def prepare_retest(
    project_root: Path,
    repaired_pack: Path,
    recovery_token_path: Path,
    recovery_report_path: Path,
    *,
    output_dir: Path | None = None,
) -> dict:
    root = Path(project_root)
    pack = Path(repaired_pack)
    recovery_token = _load_json(Path(recovery_token_path))
    recovery_report = _load_json(Path(recovery_report_path))

    if recovery_token.get("schema") != RECOVERY_TOKEN_SCHEMA:
        raise CaptureGapRetestError("Invalid regression capture-gap recovery token schema.")
    if recovery_report.get("status") != "CAPTURE_RECOVERED_READY_FOR_HD_HANDOFF":
        raise CaptureGapRetestError("Capture-gap recovery is not verified ready for HD handoff.")

    case_key = str(recovery_token.get("case_key") or "")
    case_label = str(recovery_token.get("case_label") or case_key)
    source_runtime_fp = str(recovery_token.get("source_runtime_fingerprint") or "")
    source_capture_fp = str(recovery_token.get("source_capture_fingerprint") or "")
    recovered_capture_fp = str(recovery_report.get("current_capture_fingerprint") or "")
    if not case_key or not source_runtime_fp or not source_capture_fp or not recovered_capture_fp:
        raise CaptureGapRetestError("Capture-gap recovery evidence is incomplete.")
    if recovered_capture_fp == source_capture_fp:
        raise CaptureGapRetestError("Recovered capture fingerprint is identical to the failed source capture.")
    if not _history_has_source_fail(root, case_key, source_runtime_fp):
        raise CaptureGapRetestError("Original CAPTURE_GAP FAIL is not backed by authoritative regression history.")

    repaired_runtime_fp = pack_fingerprint(pack)
    if repaired_runtime_fp == "MISSING_HIRES":
        raise CaptureGapRetestError("Repaired runtime pack is missing hires.txt.")
    if repaired_runtime_fp == source_runtime_fp:
        raise CaptureGapRetestError("Runtime fingerprint did not change after capture recovery + HD art production.")

    guide = CASE_GUIDANCE.get(case_key)
    if not guide:
        raise CaptureGapRetestError(f"No guided regression definition exists for {case_key}.")

    token = {
        "schema": RETEST_TOKEN_SCHEMA,
        "generated_utc": _now(),
        "case_key": case_key,
        "case_label": case_label,
        "source_runtime_fingerprint": source_runtime_fp,
        "source_capture_fingerprint": source_capture_fp,
        "recovered_capture_fingerprint": recovered_capture_fp,
        "repaired_runtime_fingerprint": repaired_runtime_fp,
        "target_mission_keys": list(recovery_token.get("target_mission_keys") or []),
    }
    out = Path(output_dir) if output_dir else root / "Reports" / "RegressionCaptureGapRetest"
    out.mkdir(parents=True, exist_ok=True)
    token_path = out / "REGRESSION_CAPTURE_GAP_RETEST_TOKEN.json"
    token_path.write_text(json.dumps(token, indent=2), encoding="utf-8")

    result = {
        "schema": SCHEMA,
        "generated_utc": _now(),
        "status": "SAME_CASE_RETEST_READY",
        "case": {"key": case_key, "label": case_label},
        "source_runtime_fingerprint": source_runtime_fp,
        "repaired_runtime_fingerprint": repaired_runtime_fp,
        "route": guide["route"],
        "cues": guide["cues"],
        "token": "REGRESSION_CAPTURE_GAP_RETEST_TOKEN.json",
        "next_action": "Launch this repaired exact build in verified-fullscreen MesenCE and re-test ONLY the original CAPTURE_GAP regression case.",
        "roadmap_policy": "Recovery + rebuilt art never auto-PASSes regression. Explicit same-case local MesenCE evidence is mandatory.",
        "privacy_contract": {"metadata_only": True, "rom_bytes": False, "capture_pixels": False, "absolute_local_paths": False},
    }
    return _write_outputs(result, out)


def record_retest(
    project_root: Path,
    repaired_pack: Path,
    token_path: Path,
    result: str,
    *,
    category: str = "OTHER",
    notes: str = "",
    failure_notes: str = "",
    output_dir: Path | None = None,
) -> dict:
    root = Path(project_root)
    pack = Path(repaired_pack)
    token = _load_json(Path(token_path))
    if token.get("schema") != RETEST_TOKEN_SCHEMA:
        raise CaptureGapRetestError("Invalid same-case capture-gap retest token schema.")
    case_key = str(token.get("case_key") or "")
    source_runtime_fp = str(token.get("source_runtime_fingerprint") or "")
    expected_fp = str(token.get("repaired_runtime_fingerprint") or "")
    current_fp = pack_fingerprint(pack)
    if current_fp != expected_fp:
        raise CaptureGapRetestError("Repaired runtime fingerprint changed since retest was prepared; discard this observation and rebuild the retest token.")
    if not _history_has_source_fail(root, case_key, source_runtime_fp):
        raise CaptureGapRetestError("Original CAPTURE_GAP FAIL is no longer backed by authoritative regression history.")

    result = result.strip().upper()
    if result not in {"PASS", "FAIL"}:
        raise CaptureGapRetestError("result must be PASS or FAIL")
    if result == "FAIL":
        category = category.strip().upper() or "OTHER"
        if category not in FAILURE_CATEGORIES:
            raise CaptureGapRetestError("Unknown failure category: " + category)
    else:
        category = ""
        failure_notes = ""

    recorded = record_case_result(
        root / "FINAL_REGRESSION.json",
        case_key,
        pack,
        result,
        notes=notes,
        failure_category=category,
        failure_notes=failure_notes,
    )
    after = cockpit_status(root / "FINAL_REGRESSION.json", pack)
    state = "CAPTURE_GAP_RETEST_PASS" if result == "PASS" else "CAPTURE_GAP_RETEST_FAIL"
    next_case = after.get("next_case")
    if result == "PASS":
        next_action = (
            "All 10 regression cases PASS on this exact repaired build; continue to Final Release Gate."
            if after.get("gate") == "PASS"
            else f"Same capture-gap case PASSed. Continue authoritative regression with {next_case.get('key') if next_case else 'the next current-build case'}."
        )
    else:
        next_action = "The same case still FAILs. Route the new failure category through the authoritative repair/capture path and do not advance regression."

    payload = {
        "schema": SCHEMA,
        "generated_utc": _now(),
        "status": state,
        "case": {"key": case_key, "label": token.get("case_label")},
        "recorded": recorded,
        "cockpit_gate": after.get("gate"),
        "counts": after.get("counts"),
        "next_case": next_case,
        "next_action": next_action,
        "roadmap_policy": "Gate C still requires 10/10 PASS on the final exact runtime fingerprint.",
        "privacy_contract": {"metadata_only": True, "rom_bytes": False, "capture_pixels": False, "absolute_local_paths": False},
    }
    out = Path(output_dir) if output_dir else root / "Reports" / "RegressionCaptureGapRetest"
    return _write_outputs(payload, out)


def _write_outputs(result: dict, output_dir: Path) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "REGRESSION_CAPTURE_GAP_RETEST.json"
    html_path = output_dir / "REGRESSION_CAPTURE_GAP_RETEST.html"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    cues = "".join(f"<li>{html.escape(str(item))}</li>" for item in result.get("cues", []))
    case = result.get("case") or {}
    html_path.write_text(
        "<!doctype html><html><head><meta charset='utf-8'><title>Capture Gap Same-Case Retest</title>"
        "<style>body{font:15px system-ui;max-width:1000px;margin:30px auto;padding:0 22px;background:#0d1117;color:#e6edf3}.card{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:18px;margin:14px 0}code{color:#79c0ff}.warn{color:#f2cc60}</style></head><body>"
        "<h1>Project #002 — Capture Gap Same-Case Retest</h1>"
        f"<div class='card'><h2>{html.escape(str(result.get('status') or ''))}</h2><p>Case: <code>{html.escape(str(case.get('key') or ''))}</code> — {html.escape(str(case.get('label') or ''))}</p><p class='warn'>{html.escape(str(result.get('roadmap_policy') or ''))}</p></div>"
        f"<div class='card'><h2>Route</h2><p>{html.escape(str(result.get('route') or ''))}</p><ul>{cues}</ul></div>"
        f"<div class='card'><h2>DO THIS NEXT</h2><p>{html.escape(str(result.get('next_action') or ''))}</p></div>"
        "</body></html>",
        encoding="utf-8",
    )
    wrapped = dict(result)
    wrapped["outputs"] = {"json": str(json_path), "dashboard": str(html_path)}
    return wrapped


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 recovered CAPTURE_GAP same-case retest director")
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("project_root", type=Path)
    prepare.add_argument("repaired_pack", type=Path)
    prepare.add_argument("recovery_token", type=Path)
    prepare.add_argument("recovery_report", type=Path)
    prepare.add_argument("--output", type=Path)

    record = sub.add_parser("record")
    record.add_argument("project_root", type=Path)
    record.add_argument("repaired_pack", type=Path)
    record.add_argument("token", type=Path)
    record.add_argument("result", choices=("PASS", "FAIL"))
    record.add_argument("--category", choices=FAILURE_CATEGORIES, default="OTHER")
    record.add_argument("--notes", default="")
    record.add_argument("--failure-notes", default="")
    record.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.command == "prepare":
        payload = prepare_retest(args.project_root, args.repaired_pack, args.recovery_token, args.recovery_report, output_dir=args.output)
    else:
        payload = record_retest(
            args.project_root,
            args.repaired_pack,
            args.token,
            args.result,
            category=args.category,
            notes=args.notes,
            failure_notes=args.failure_notes,
            output_dir=args.output,
        )
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
