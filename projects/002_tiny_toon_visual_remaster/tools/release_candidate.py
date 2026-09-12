from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
from datetime import datetime, timezone
from pathlib import Path

from capture_mission_control import mission_status
from hd_readiness import package_hd_pack
from hdpack_pipeline import analyze
from validate_hdpack import validate
from visual_context_audit import review_status as visual_context_status

REGRESSION_CASES = [
    ("boot_title_menu", "Boot, title, menu navigation and menu animations"),
    ("player_movement", "Idle, walk, run, crouch, jump, fall and landing"),
    ("player_actions_damage_death", "Actions/attacks, damage, invulnerability and death"),
    ("world_route_1", "Primary route: every level and scrolling boundary"),
    ("world_route_2", "Alternate routes, secrets, revisits and uncommon transitions"),
    ("enemies", "Common and rare enemies: movement, attacks, hit and death"),
    ("bosses", "Every boss intro, phase, attack, hit/death state and effect"),
    ("hud_text_status", "HUD, counters, dialogs, pause/status and result screens"),
    ("effects_transitions", "Projectiles, particles, doors, fades and special effects"),
    ("ending_credits", "Ending, credits and post-game states"),
]

REGRESSION_STATES = ("PASS", "FAIL", "STALE", "PENDING")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _referenced_images(pack_dir: Path) -> list[Path]:
    hires = pack_dir / "hires.txt"
    if not hires.is_file():
        return []
    images: list[Path] = []
    for raw in hires.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = raw.strip()
        if line.lower().startswith("<img>"):
            images.append(pack_dir / line[5:].strip())
    return images


def pack_fingerprint(pack_dir: Path) -> str:
    digest = hashlib.sha256()
    hires = pack_dir / "hires.txt"
    if not hires.is_file():
        return "MISSING_HIRES"
    for path in [hires, *_referenced_images(pack_dir)]:
        rel = path.relative_to(pack_dir).as_posix() if path.is_absolute() else str(path)
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update((_sha256(path) if path.is_file() else "MISSING").encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def _default_case(label: str) -> dict:
    return {
        "label": label,
        "done": False,
        "notes": "",
        "pack_fingerprint": None,
        "completed_utc": None,
        "result": "PENDING",
        "failure_category": "",
        "failure_notes": "",
        "tested_utc": None,
    }


def default_regression_manifest() -> dict:
    return {
        "schema": 2,
        "created_utc": _now(),
        "warning": (
            "Final visual regression evidence is exact-build-specific. "
            "Any runtime PNG or hires.txt change makes earlier PASS evidence stale."
        ),
        "cases": {key: _default_case(label) for key, label in REGRESSION_CASES},
        "history": [],
    }


def ensure_regression_manifest(path: Path) -> Path:
    path = Path(path)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(default_regression_manifest(), indent=2), encoding="utf-8")
    return path


def load_regression_manifest(path: Path) -> dict:
    """Load old or new regression evidence without discarding cockpit metadata."""
    path = ensure_regression_manifest(Path(path))
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise ValueError(f"Invalid regression manifest: {exc}") from exc
    if not isinstance(raw, dict):
        raw = {}

    result = default_regression_manifest()
    result["created_utc"] = raw.get("created_utc", result["created_utc"])
    result["history"] = list(raw.get("history", [])) if isinstance(raw.get("history"), list) else []

    incoming = raw.get("cases", {}) if isinstance(raw.get("cases"), dict) else {}
    for key, label in REGRESSION_CASES:
        target = result["cases"][key]
        source = incoming.get(key)
        if not isinstance(source, dict):
            continue
        target["label"] = str(source.get("label") or label)
        target["done"] = bool(source.get("done", False))
        target["notes"] = str(source.get("notes", ""))
        target["pack_fingerprint"] = source.get("pack_fingerprint")
        target["completed_utc"] = source.get("completed_utc")
        legacy_result = "PASS" if target["done"] else "PENDING"
        target["result"] = str(source.get("result") or legacy_result).upper()
        if target["result"] not in {"PASS", "FAIL", "PENDING"}:
            target["result"] = legacy_result
        target["failure_category"] = str(source.get("failure_category", ""))
        target["failure_notes"] = str(source.get("failure_notes", ""))
        target["tested_utc"] = source.get("tested_utc") or source.get("completed_utc")

    result["schema"] = 2
    return result


def _regression_case_state(item: dict, fingerprint: str) -> str:
    recorded = item.get("pack_fingerprint")
    result = str(item.get("result") or ("PASS" if item.get("done") else "PENDING")).upper()
    if recorded and recorded != fingerprint:
        return "STALE"
    if result == "FAIL":
        return "FAIL"
    if result == "PASS" and bool(item.get("done")) and recorded == fingerprint:
        return "PASS"
    return "PENDING"


def complete_regression_case(manifest_path: Path, case_key: str, pack_dir: Path, notes: str = "") -> dict:
    """Compatibility PASS recorder; Final Regression Cockpit remains the preferred UI."""
    path = Path(manifest_path)
    data = load_regression_manifest(path)
    if case_key not in data["cases"]:
        raise ValueError(f"Unknown regression case: {case_key}")
    fingerprint = pack_fingerprint(Path(pack_dir))
    if fingerprint == "MISSING_HIRES":
        raise ValueError("Cannot record regression evidence for a pack without hires.txt")
    timestamp = _now()
    case = data["cases"][case_key]
    case.update(
        done=True,
        notes=notes,
        pack_fingerprint=fingerprint,
        completed_utc=timestamp,
        result="PASS",
        failure_category="",
        failure_notes="",
        tested_utc=timestamp,
    )
    data["history"].append(
        {
            "utc": timestamp,
            "case": case_key,
            "result": "PASS",
            "pack_fingerprint": fingerprint,
            "source": "release_candidate.complete_regression_case",
            "notes": notes,
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return case


def regression_status(manifest_path: Path, pack_dir: Path) -> dict:
    """Authoritative release view of Final Regression Cockpit evidence."""
    data = load_regression_manifest(Path(manifest_path))
    fingerprint = pack_fingerprint(Path(pack_dir))
    rows: list[dict] = []
    counts = {state: 0 for state in REGRESSION_STATES}

    for order, (key, label) in enumerate(REGRESSION_CASES, start=1):
        item = data["cases"][key]
        state = _regression_case_state(item, fingerprint)
        counts[state] += 1
        rows.append(
            {
                "order": order,
                "key": key,
                "label": label,
                **item,
                "state": state,
                "current_build": state == "PASS",
            }
        )

    next_case = next((row for row in rows if row["state"] == "FAIL"), None)
    if next_case is None:
        next_case = next((row for row in rows if row["state"] in {"STALE", "PENDING"}), None)

    total = len(rows)
    return {
        "schema": 2,
        "manifest_schema": int(data.get("schema", 2) or 2),
        "pack_fingerprint": fingerprint,
        "done_current_build": counts["PASS"],
        "stale_evidence": counts["STALE"],
        "failed_current_build": counts["FAIL"],
        "pending": counts["PENDING"],
        "counts": counts,
        "total": total,
        "gate": "PASS" if counts["PASS"] == total and total else "BLOCKED",
        "next_case": next_case,
        "history_entries": len(data.get("history", [])),
        "cases": rows,
    }


def _art_queue_status(path: Path) -> dict:
    result = {"exists": path.is_file(), "rows": 0, "done": 0, "todo": 0, "unassigned": 0}
    if not path.is_file():
        return result
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            result["rows"] += 1
            status = (row.get("status") or "TODO").strip().upper()
            group = (row.get("art_group") or "UNASSIGNED").strip().upper()
            if status in {"DONE", "COMPLETE", "COMPLETED", "FINAL"}:
                result["done"] += 1
            else:
                result["todo"] += 1
            result["unassigned"] += int(group == "UNASSIGNED")
    return result


def _load_art_qa(path: Path, current_fingerprint: str) -> dict:
    report = path / "ART_QA_RESULT.json" if path.is_dir() else path
    result = {
        "exists": report.is_file(),
        "gate": "BLOCKED",
        "report_gate": None,
        "fingerprint_matches": False,
        "report_fingerprint": None,
        "path": str(report),
    }
    if not report.is_file():
        return result
    data = json.loads(report.read_text(encoding="utf-8"))
    result["report_gate"] = data.get("qa_gate")
    result["report_fingerprint"] = data.get("output_pack_fingerprint")
    result["fingerprint_matches"] = result["report_fingerprint"] == current_fingerprint
    if result["report_gate"] == "PASS" and result["fingerprint_matches"]:
        result["gate"] = "PASS"
    return result


def _visual_context_status(pack_dir: Path, art_queue: Path, visual_review: Path | None) -> dict:
    if visual_review is None:
        return {
            "exists": False,
            "gate": "BLOCKED",
            "families": 0,
            "review_required": 0,
            "reviewed": 0,
            "pending": 0,
            "stale": 0,
        }
    return visual_context_status(pack_dir, art_queue, visual_review)


def audit_release_candidate(
    pack_dir: Path,
    capture_manifest: Path,
    art_queue: Path,
    art_qa: Path,
    regression_manifest: Path,
    visual_review: Path | None = None,
) -> dict:
    errors, warnings, validator_stats = validate(pack_dir)
    stats = analyze(pack_dir)
    fingerprint = pack_fingerprint(pack_dir)
    capture = mission_status(capture_manifest)
    queue = _art_queue_status(art_queue)
    context = _visual_context_status(pack_dir, art_queue, visual_review)
    qa = _load_art_qa(art_qa, fingerprint)
    regression = regression_status(regression_manifest, pack_dir)

    blockers: list[str] = []
    if errors:
        blockers.append("HD Pack validator reports structural errors")
    if stats.missing_images:
        blockers.append("Referenced HD PNG files are missing")
    if stats.scale < 4:
        blockers.append("HD Pack scale is below the 4x Project #002 target")
    if capture["release_capture_gate"] != "PASS":
        blockers.append(f"Capture missions incomplete ({capture['done']}/{capture['total']})")
    if not queue["exists"] or queue["rows"] == 0:
        blockers.append("Art queue is missing or empty")
    else:
        if queue["todo"]:
            blockers.append(f"Art queue contains {queue['todo']} unfinished entries")
        if queue["unassigned"]:
            blockers.append(f"Art queue contains {queue['unassigned']} unassigned entries")
    if context["gate"] != "PASS":
        if not context["exists"]:
            blockers.append("Visual Context Review is missing")
        else:
            blockers.append(
                f"Visual Context Review incomplete (pending={context['pending']}, stale={context['stale']})"
            )
    if qa["gate"] != "PASS":
        if not qa["exists"]:
            blockers.append("Pixel Art QA result is missing")
        elif qa["report_gate"] != "PASS":
            blockers.append("Pixel Art QA did not PASS")
        else:
            blockers.append("Pixel Art QA is stale: report fingerprint does not match current HD pack")
    if regression["gate"] != "PASS":
        counts = regression["counts"]
        blockers.append(
            "Final Regression Cockpit is not green "
            f"(PASS={counts['PASS']}/{regression['total']}, FAIL={counts['FAIL']}, "
            f"STALE={counts['STALE']}, PENDING={counts['PENDING']})"
        )

    release_ready = not blockers
    return {
        "schema": 3,
        "generated_utc": _now(),
        "release_gate": "PASS" if release_ready else "BLOCKED",
        "release_ready": release_ready,
        "pack_fingerprint": fingerprint,
        "important_note": (
            "PASS requires structural validity, complete capture missions, a finished/classified art queue, "
            "a current Visual Context Review, current-build Pixel QA and 10/10 PASS in the authoritative "
            "Final Regression Cockpit for this exact HD-pack fingerprint."
        ),
        "pack": {
            "scale": stats.scale,
            "images": len(stats.images),
            "tile_rules": stats.tile_rules,
            "unique_tile_ids": stats.unique_tile_ids,
            "unique_palettes": stats.unique_palettes,
            "missing_images": list(stats.missing_images),
        },
        "validator": {"errors": errors, "warnings": warnings, "stats": validator_stats},
        "capture": capture,
        "art_queue": queue,
        "visual_context": context,
        "art_qa": qa,
        "regression": regression,
        "blockers": blockers,
    }


def write_release_dashboard(result: dict, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "RELEASE_CANDIDATE.json"
    html_path = output_dir / "RELEASE_CANDIDATE.html"
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    blockers = "".join(f"<li>{html.escape(item)}</li>" for item in result["blockers"]) or "<li>None</li>"

    regression_rows = "".join(
        "<tr>"
        f"<td class='{case['state'].lower()}'>{case['state']}</td>"
        f"<td><code>{html.escape(case['key'])}</code></td>"
        f"<td>{html.escape(case['label'])}</td>"
        f"<td>{html.escape(case.get('failure_category') or '')}</td>"
        f"<td>{html.escape(case.get('failure_notes') or case.get('notes') or '')}</td>"
        "</tr>"
        for case in result["regression"]["cases"]
    )
    gate_class = "pass" if result["release_gate"] == "PASS" else "blocked"
    context = result["visual_context"]
    counts = result["regression"]["counts"]
    next_case = result["regression"].get("next_case")
    next_text = "All regression cases PASS for this exact build."
    if next_case:
        next_text = f"{next_case['order']}. {next_case['label']} ({next_case['state']})"

    document = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><title>Project #002 Release Candidate Gate</title>
<style>body{{font:16px system-ui;max-width:1200px;margin:34px auto;padding:0 22px;background:#0d1117;color:#e6edf3}}.card{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:18px;margin:14px 0}}.pass{{color:#3fb950}}.fail,.blocked{{color:#f85149}}.stale{{color:#d29922}}.pending{{color:#8b949e}}table{{width:100%;border-collapse:collapse}}td,th{{padding:9px;border-bottom:1px solid #30363d;text-align:left;vertical-align:top}}code{{color:#79c0ff}}small{{color:#8b949e}}</style></head><body>
<h1>Tiny Toon Visual Remaster — Authoritative Final Release Gate</h1>
<div class='card'><h2 class='{gate_class}'>RELEASE GATE: {result['release_gate']}</h2><p>{html.escape(result['important_note'])}</p><p><small>Exact build fingerprint: <code>{result['pack_fingerprint']}</code></small></p><h3>Blockers</h3><ul>{blockers}</ul></div>
<div class='card'><h2>Evidence summary</h2><p>Capture: <b>{result['capture']['done']}/{result['capture']['total']}</b> · Art queue: <b>{result['art_queue']['done']}/{result['art_queue']['rows']}</b> done · Visual context: <b>{context['gate']}</b> ({context['reviewed']}/{context['review_required']}) · Pixel QA: <b>{result['art_qa']['gate']}</b> · Final regression: <b>{counts['PASS']}/{result['regression']['total']}</b> PASS</p><p>FAIL {counts['FAIL']} · STALE {counts['STALE']} · PENDING {counts['PENDING']}</p><h3>DO THIS NEXT</h3><p>{html.escape(next_text)}</p></div>
<div class='card'><h2>Final Regression Cockpit evidence</h2><table><tr><th>Status</th><th>Case</th><th>Scope</th><th>Failure category</th><th>Notes / failure</th></tr>{regression_rows}</table></div></body></html>"""
    html_path.write_text(document, encoding="utf-8")
    return html_path


def audit_and_write(
    pack: Path,
    capture: Path,
    queue: Path,
    art_qa: Path,
    regression: Path,
    visual_review: Path,
    output: Path,
) -> dict:
    result = audit_release_candidate(pack, capture, queue, art_qa, regression, visual_review)
    write_release_dashboard(result, output)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 authoritative, exact-build release candidate gate")
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init-regression")
    init.add_argument("manifest", type=Path)
    complete = commands.add_parser("complete-regression")
    complete.add_argument("manifest", type=Path)
    complete.add_argument("case")
    complete.add_argument("pack", type=Path)
    complete.add_argument("--notes", default="")
    for name in ("audit", "package"):
        cmd = commands.add_parser(name)
        cmd.add_argument("pack", type=Path)
        cmd.add_argument("--capture", type=Path, required=True)
        cmd.add_argument("--queue", type=Path, required=True)
        cmd.add_argument("--visual-review", type=Path, required=True)
        cmd.add_argument("--art-qa", type=Path, required=True)
        cmd.add_argument("--regression", type=Path, required=True)
        cmd.add_argument("--output", type=Path, required=True)
        if name == "package":
            cmd.add_argument("--zip", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "init-regression":
        print(ensure_regression_manifest(args.manifest))
        return 0
    if args.command == "complete-regression":
        print(json.dumps(complete_regression_case(args.manifest, args.case, args.pack, args.notes), indent=2))
        return 0
    result = audit_and_write(
        args.pack,
        args.capture,
        args.queue,
        args.art_qa,
        args.regression,
        args.visual_review,
        args.output,
    )
    print(json.dumps(result, indent=2))
    if result["release_gate"] != "PASS":
        return 2
    if args.command == "package":
        print(package_hd_pack(args.pack, args.zip))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
