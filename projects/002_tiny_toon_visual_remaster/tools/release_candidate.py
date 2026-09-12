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
    """Stable fingerprint for the runtime HD pack only.

    Production reports are deliberately excluded. Any change to hires.txt or a
    referenced image invalidates final regression evidence and stale Art QA.
    """
    digest = hashlib.sha256()
    hires = pack_dir / "hires.txt"
    if not hires.is_file():
        return "MISSING_HIRES"
    files = [hires, *_referenced_images(pack_dir)]
    for path in files:
        rel = path.relative_to(pack_dir).as_posix() if path.is_absolute() else str(path)
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        if path.is_file():
            digest.update(_sha256(path).encode("ascii"))
        else:
            digest.update(b"MISSING")
        digest.update(b"\0")
    return digest.hexdigest()


def default_regression_manifest() -> dict:
    return {
        "schema": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "warning": (
            "Final visual regression evidence is build-specific. Completing a case "
            "for an older HD pack does not count after runtime art/mapping changes."
        ),
        "cases": {
            key: {
                "label": label,
                "done": False,
                "notes": "",
                "pack_fingerprint": None,
                "completed_utc": None,
            }
            for key, label in REGRESSION_CASES
        },
    }


def ensure_regression_manifest(path: Path) -> Path:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(default_regression_manifest(), indent=2), encoding="utf-8")
    return path


def load_regression_manifest(path: Path) -> dict:
    ensure_regression_manifest(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    defaults = default_regression_manifest()
    incoming = data.get("cases", {}) if isinstance(data, dict) else {}
    for key, item in defaults["cases"].items():
        source = incoming.get(key)
        if not isinstance(source, dict):
            continue
        item["done"] = bool(source.get("done", False))
        item["notes"] = str(source.get("notes", ""))
        item["pack_fingerprint"] = source.get("pack_fingerprint")
        item["completed_utc"] = source.get("completed_utc")
    return defaults


def complete_regression_case(manifest_path: Path, case_key: str, pack_dir: Path, notes: str = "") -> dict:
    data = load_regression_manifest(manifest_path)
    if case_key not in data["cases"]:
        raise ValueError(f"Unknown regression case: {case_key}")
    fingerprint = pack_fingerprint(pack_dir)
    if fingerprint == "MISSING_HIRES":
        raise ValueError("Cannot record regression evidence for a pack without hires.txt")
    case = data["cases"][case_key]
    case["done"] = True
    case["notes"] = notes
    case["pack_fingerprint"] = fingerprint
    case["completed_utc"] = datetime.now(timezone.utc).isoformat()
    manifest_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return case


def regression_status(manifest_path: Path, pack_dir: Path) -> dict:
    data = load_regression_manifest(manifest_path)
    fingerprint = pack_fingerprint(pack_dir)
    rows = []
    valid_done = 0
    stale = 0
    for key, item in data["cases"].items():
        is_done = bool(item["done"])
        is_current = is_done and item.get("pack_fingerprint") == fingerprint
        if is_current:
            valid_done += 1
        elif is_done:
            stale += 1
        rows.append({"key": key, **item, "current_build": is_current})
    total = len(rows)
    return {
        "pack_fingerprint": fingerprint,
        "done_current_build": valid_done,
        "stale_evidence": stale,
        "total": total,
        "gate": "PASS" if valid_done == total and total else "BLOCKED",
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
            if group == "UNASSIGNED":
                result["unassigned"] += 1
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


def audit_release_candidate(
    pack_dir: Path,
    capture_manifest: Path,
    art_queue: Path,
    art_qa: Path,
    regression_manifest: Path,
) -> dict:
    errors, warnings, validator_stats = validate(pack_dir)
    stats = analyze(pack_dir)
    fingerprint = pack_fingerprint(pack_dir)
    capture = mission_status(capture_manifest)
    queue = _art_queue_status(art_queue)
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
    if qa["gate"] != "PASS":
        if not qa["exists"]:
            blockers.append("Pixel Art QA result is missing")
        elif qa["report_gate"] != "PASS":
            blockers.append("Pixel Art QA did not PASS")
        else:
            blockers.append("Pixel Art QA is stale: report fingerprint does not match current HD pack")
    if regression["gate"] != "PASS":
        blockers.append(
            f"Current-build full-game regression incomplete "
            f"({regression['done_current_build']}/{regression['total']}, stale={regression['stale_evidence']})"
        )

    release_ready = not blockers
    return {
        "schema": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "release_gate": "PASS" if release_ready else "BLOCKED",
        "release_ready": release_ready,
        "pack_fingerprint": fingerprint,
        "important_note": (
            "PASS requires structural validity, complete manual capture missions, a fully finished/classified "
            "art queue, current-build pixel QA, and current-build full-game visual regression evidence."
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
        f"<td>{'PASS' if case['current_build'] else ('STALE' if case['done'] else 'TODO')}</td>"
        f"<td><code>{html.escape(case['key'])}</code></td>"
        f"<td>{html.escape(case['label'])}</td>"
        f"<td>{html.escape(case.get('notes') or '')}</td>"
        "</tr>"
        for case in result["regression"]["cases"]
    )
    gate_class = "pass" if result["release_gate"] == "PASS" else "blocked"
    document = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'>
<title>Project #002 Release Candidate Gate</title>
<style>body{{font:16px system-ui;max-width:1150px;margin:34px auto;padding:0 22px;background:#0d1117;color:#e6edf3}}.card{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:18px;margin:14px 0}}.pass{{color:#3fb950}}.blocked{{color:#f85149}}table{{width:100%;border-collapse:collapse}}td,th{{padding:9px;border-bottom:1px solid #30363d;text-align:left}}code{{color:#79c0ff}}small{{color:#8b949e}}</style></head><body>
<h1>Tiny Toon Visual Remaster — Unified Release Candidate Gate</h1>
<div class='card'><h2 class='{gate_class}'>RELEASE GATE: {result['release_gate']}</h2><p>{html.escape(result['important_note'])}</p><p><small>Build fingerprint: <code>{result['pack_fingerprint']}</code></small></p><h3>Blockers</h3><ul>{blockers}</ul></div>
<div class='card'><h2>Evidence summary</h2><p>Capture: <b>{result['capture']['done']}/{result['capture']['total']}</b> · Art queue: <b>{result['art_queue']['done']}/{result['art_queue']['rows']}</b> done, <b>{result['art_queue']['unassigned']}</b> unassigned · Pixel QA: <b>{result['art_qa']['gate']}</b> · Regression: <b>{result['regression']['done_current_build']}/{result['regression']['total']}</b> current-build cases</p></div>
<div class='card'><h2>Final visual regression</h2><table><tr><th>Status</th><th>Case</th><th>Scope</th><th>Notes</th></tr>{regression_rows}</table></div>
</body></html>"""
    html_path.write_text(document, encoding="utf-8")
    return html_path


def audit_and_write(pack: Path, capture: Path, queue: Path, art_qa: Path, regression: Path, output: Path) -> dict:
    result = audit_release_candidate(pack, capture, queue, art_qa, regression)
    write_release_dashboard(result, output)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 unified, build-bound release candidate gate")
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

    result = audit_and_write(args.pack, args.capture, args.queue, args.art_qa, args.regression, args.output)
    print(json.dumps(result, indent=2))
    if result["release_gate"] != "PASS":
        return 2
    if args.command == "package":
        print(package_hd_pack(args.pack, args.zip))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
