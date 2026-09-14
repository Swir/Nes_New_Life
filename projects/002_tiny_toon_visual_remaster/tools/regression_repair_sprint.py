from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from active_family_workbench import WorkbenchError, resolve_active_family_workbench
from art_sprint_kit import MANIFEST_NAME, _make_board, _sha256
from family_contact_board import generate_family_contact_boards
from final_regression_cockpit import FAILURE_CATEGORIES, cockpit_status, record_case_result
from guided_regression_playtest import CASE_GUIDANCE
from release_candidate import pack_fingerprint
from transactional_art_commit import transactional_finish_sprint

SCHEMA = "swir.project002.regression-repair-sprint.v1"
RETEST_SCHEMA = "swir.project002.regression-repair-retest.v1"
ART_REPAIR_CATEGORIES = {"MISSING_HD", "WRONG_PALETTE", "ANIMATION_SEAM", "TRANSPARENCY", "OTHER"}
CASE_GROUPS = {
    "boot_title_menu": ("UI", "WORLD"),
    "player_movement": ("PLAYER",),
    "player_actions_damage_death": ("PLAYER",),
    "world_route_1": ("WORLD",),
    "world_route_2": ("WORLD",),
    "enemies": ("ENEMY",),
    "bosses": ("BOSS",),
    "hud_text_status": ("UI",),
    "effects_transitions": ("EFFECTS",),
    "ending_credits": ("UI", "WORLD"),
}
NON_ART_ROUTES = {
    "CAPTURE_GAP": ("CAPTURE_REVIEW_REQUIRED", "Capture_Review_Director.bat", "Gather the missing real gameplay/capture evidence before attempting an art repair."),
    "MAPPING": ("MAPPING_REPAIR_REQUIRED", "Final_Regression_Cockpit.bat", "Repair hires.txt mapping provenance first; do not hide a mapping defect with replacement pixels."),
    "SCALE_OR_FILTER": ("RUNTIME_REPAIR_REQUIRED", "Build_HD_Playtest.bat", "Repair 4x/fullscreen/runtime presentation first; artwork should remain unchanged."),
}
_TARGET_RE = re.compile(r"\[SWIR_TARGET\s+tile=([^\s\]]+)(?:\s+palette=([^\s\]]+))?\]", re.IGNORECASE)


class RepairSprintError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> dict:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RepairSprintError(f"Missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RepairSprintError(f"Invalid JSON: {path}") from exc
    if not isinstance(data, dict):
        raise RepairSprintError(f"Expected JSON object: {path}")
    return data


def _current_failure(project_root: Path, runtime_pack: Path) -> tuple[dict, dict]:
    status = cockpit_status(Path(project_root) / "FINAL_REGRESSION.json", Path(runtime_pack))
    case = status.get("next_case")
    if not case or case.get("state") != "FAIL":
        raise RepairSprintError("No authoritative current-build FAIL is waiting for repair.")
    return status, case


def _failure_target(notes: str) -> tuple[str, str] | None:
    match = _TARGET_RE.search(notes or "")
    if not match:
        return None
    return match.group(1).upper(), (match.group(2) or "").upper()


def _family_key(item: dict) -> tuple[str, str, str]:
    return (
        str(item.get("group", "UNASSIGNED")).upper(),
        str(item.get("seed_tile_id") or item.get("tile_id") or "").upper(),
        str(item.get("seed_palette") or item.get("palette") or "").upper(),
    )


def select_repair_items(case: dict, source_manifest: dict, active_family: dict | None) -> list[dict]:
    items = list(source_manifest.get("items") or [])
    if not items:
        raise RepairSprintError("CurrentImpactSprint contains no editable items to target.")

    explicit = _failure_target(str(case.get("failure_notes") or ""))
    if explicit:
        tile, palette = explicit
        exact = [
            row for row in items
            if str(row.get("tile_id", "")).upper() == tile
            and (not palette or str(row.get("palette", "")).upper() == palette)
        ]
        if exact:
            family_keys = {_family_key(row) for row in exact}
            expanded = [row for row in items if _family_key(row) in family_keys]
            return expanded or exact

    if active_family:
        files = {str(value) for value in active_family.get("editable_files", [])}
        family_items = [row for row in items if str(row.get("kit_file")) in files]
        if family_items:
            return family_items

    groups = set(CASE_GROUPS.get(str(case.get("key", "")), ()))
    grouped = [row for row in items if str(row.get("group", "")).upper() in groups]
    if grouped:
        first_key = _family_key(grouped[0])
        family = [row for row in grouped if _family_key(row) == first_key]
        return family or grouped[:12]
    raise RepairSprintError("No repair target for this failed case exists in CurrentImpactSprint. Refresh the evidence-bound art handoff/high-impact sprint first.")


def _route_only(status: dict, case: dict, category: str) -> dict:
    state, launcher, action = NON_ART_ROUTES[category]
    guide = CASE_GUIDANCE.get(str(case.get("key")), {})
    return {
        "schema": SCHEMA,
        "generated_utc": _now(),
        "status": state,
        "runtime_fingerprint": status["pack_fingerprint"],
        "failed_case": {"key": case.get("key"), "label": case.get("label"), "category": category},
        "repair_sprint_created": False,
        "launcher": launcher,
        "next_action": action,
        "retest_route": guide.get("route", ""),
        "retest_cues": guide.get("cues", []),
        "privacy_contract": {"metadata_only": True, "absolute_local_paths": False, "capture_pixels": False, "rom_bytes": False},
    }


def prepare_repair_sprint(project_root: Path, runtime_pack: Path, *, overwrite: bool = False) -> dict:
    root = Path(project_root)
    runtime = Path(runtime_pack)
    status, case = _current_failure(root, runtime)
    category = str(case.get("failure_category") or "OTHER").upper()
    if category in NON_ART_ROUTES:
        result = _route_only(status, case, category)
        return _write_outputs(result, root / "Reports" / "RegressionRepairSprint")
    if category not in ART_REPAIR_CATEGORIES:
        raise RepairSprintError(f"Unsupported repair category: {category}")

    source_kit = root / "Artwork" / "CurrentImpactSprint"
    source_manifest = _load_json(source_kit / MANIFEST_NAME)
    try:
        active = resolve_active_family_workbench(source_kit)
    except WorkbenchError:
        active = None
    selected = select_repair_items(case, source_manifest, active)

    workspace = root / "Artwork" / "MasterWorkspace"
    if not (workspace / "MASTER_TILES.json").is_file():
        raise RepairSprintError("MasterWorkspace is missing MASTER_TILES.json.")
    repair_kit = root / "Artwork" / "CurrentRepairSprint"
    if repair_kit.exists() and any(repair_kit.iterdir()):
        if not overwrite:
            raise RepairSprintError("CurrentRepairSprint is not empty. Finish/archive it or rerun with --overwrite.")
        shutil.rmtree(repair_kit)
    editable_dir = repair_kit / "editable"
    reference_dir = repair_kit / "reference"
    editable_dir.mkdir(parents=True, exist_ok=True)
    reference_dir.mkdir(parents=True, exist_ok=True)

    fresh_items: list[dict] = []
    for index, source in enumerate(selected, start=1):
        master_file = str(source.get("master_file") or "")
        current = workspace / "editable" / master_file
        original = workspace / "original" / master_file
        if not master_file or not current.is_file() or not original.is_file():
            raise RepairSprintError(f"Repair target is missing from current MasterWorkspace: {master_file or '<unnamed>'}")
        with Image.open(current) as image:
            dimensions = list(image.size)
        kit_file = f"{index:03d}_{master_file}"
        shutil.copy2(current, editable_dir / kit_file)
        shutil.copy2(original, reference_dir / kit_file)
        item = dict(source)
        item.update({
            "priority": index,
            "kit_file": kit_file,
            "dimensions": dimensions,
            "workspace_editable_sha256_at_export": _sha256(current),
            "workspace_original_sha256": _sha256(original),
            "repair_case": case.get("key"),
            "repair_category": category,
        })
        fresh_items.append(item)

    board = _make_board(fresh_items, repair_kit)
    family_boards = generate_family_contact_boards(fresh_items, repair_kit)
    manifest = {
        "schema": 5,
        "generated_utc": _now(),
        "selection_mode": "failed-regression-minimal-repair",
        "expected_runtime_fingerprint": status["pack_fingerprint"],
        "failed_case": {"key": case.get("key"), "label": case.get("label"), "failure_category": category, "failure_notes": case.get("failure_notes", "")},
        "source_sprint_schema": source_manifest.get("schema"),
        "exported": len(fresh_items),
        "local_board": board,
        "family_contact_boards": "FAMILY_CONTACT_BOARDS.json",
        "family_contact_board_count": family_boards.get("family_count", 0),
        "instructions": [
            "This is a minimal repair sprint for one authoritative failed regression case.",
            "It was re-exported from the current MasterWorkspace, not copied from stale sprint pixels/hashes.",
            "Edit only editable/*.png; preserve filenames, dimensions and alpha canvas.",
            "Finish through regression_repair_sprint.py finish so master visual QA, animation-family QA, hires.txt preservation and Pixel QA remain transactional.",
            "After COMMITTED QA, immediately re-test the exact failed case using the generated fingerprint-bound REPAIR_RETEST_TOKEN.json.",
        ],
        "items": fresh_items,
    }
    (repair_kit / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    guide = CASE_GUIDANCE.get(str(case.get("key")), {})
    result = {
        "schema": SCHEMA,
        "generated_utc": _now(),
        "status": "REPAIR_SPRINT_READY",
        "runtime_fingerprint": status["pack_fingerprint"],
        "failed_case": {"key": case.get("key"), "label": case.get("label"), "category": category},
        "repair_sprint_created": True,
        "repair_items": len(fresh_items),
        "active_family": None if active is None else {"family": active.get("family"), "members": active.get("members"), "priority": active.get("priority")},
        "local_board": board,
        "family_board_count": family_boards.get("family_count", 0),
        "launcher": "Regression_Repair_Loop.bat",
        "next_action": "Edit only CurrentRepairSprint/editable, then run transactional repair finish and immediately re-test this exact failed case.",
        "retest_route": guide.get("route", ""),
        "retest_cues": guide.get("cues", []),
        "privacy_contract": {"metadata_only": True, "absolute_local_paths": False, "capture_pixels": False, "rom_bytes": False},
    }
    return _write_outputs(result, root / "Reports" / "RegressionRepairSprint")


def finish_repair(project_root: Path, runtime_pack: Path, *, output_pack: Path | None = None) -> dict:
    root = Path(project_root)
    runtime = Path(runtime_pack)
    kit = root / "Artwork" / "CurrentRepairSprint"
    manifest = _load_json(kit / MANIFEST_NAME)
    if manifest.get("selection_mode") != "failed-regression-minimal-repair":
        raise RepairSprintError("CurrentRepairSprint is not a regression repair sprint.")
    status, case = _current_failure(root, runtime)
    expected_case = str((manifest.get("failed_case") or {}).get("key") or "")
    if str(case.get("key")) != expected_case:
        raise RepairSprintError(f"Authoritative failed case changed from {expected_case} to {case.get('key')}; discard/rebuild repair sprint.")
    expected_fp = str(manifest.get("expected_runtime_fingerprint") or "")
    if status.get("pack_fingerprint") != expected_fp:
        raise RepairSprintError("Runtime fingerprint changed since repair sprint export; discard/rebuild repair sprint.")

    workspace = root / "Artwork" / "MasterWorkspace"
    target = Path(output_pack) if output_pack else root / "Build" / "RegressionRepairCandidate"
    transaction = transactional_finish_sprint(runtime, workspace, kit, target, overwrite=True)
    if transaction.get("transaction_status") != "COMMITTED":
        result = {
            "schema": SCHEMA,
            "generated_utc": _now(),
            "status": "REPAIR_QA_BLOCKED",
            "runtime_fingerprint": expected_fp,
            "failed_case": manifest.get("failed_case"),
            "transaction": transaction,
            "next_action": transaction.get("next_action", "Fix repair sprint QA blockers before re-testing."),
            "privacy_contract": {"metadata_only": True, "absolute_local_paths": False, "capture_pixels": False, "rom_bytes": False},
        }
        return _write_outputs(result, root / "Reports" / "RegressionRepairSprint")

    repaired_fp = pack_fingerprint(target)
    token = {
        "schema": RETEST_SCHEMA,
        "generated_utc": _now(),
        "case_key": expected_case,
        "case_label": (manifest.get("failed_case") or {}).get("label"),
        "failure_category": (manifest.get("failed_case") or {}).get("failure_category"),
        "source_runtime_fingerprint": expected_fp,
        "repaired_runtime_fingerprint": repaired_fp,
    }
    token_path = kit / "REPAIR_RETEST_TOKEN.json"
    token_path.write_text(json.dumps(token, indent=2), encoding="utf-8")
    guide = CASE_GUIDANCE.get(expected_case, {})
    result = {
        "schema": SCHEMA,
        "generated_utc": _now(),
        "status": "REPAIR_COMMITTED_RETEST_REQUIRED",
        "source_runtime_fingerprint": expected_fp,
        "repaired_runtime_fingerprint": repaired_fp,
        "failed_case": manifest.get("failed_case"),
        "transaction": {"transaction_status": transaction.get("transaction_status"), "qa_gate": transaction.get("qa_gate"), "mapping_preserved": transaction.get("mapping_preserved"), "committed_files": transaction.get("committed_files", [])},
        "retest_token": "Artwork/CurrentRepairSprint/REPAIR_RETEST_TOKEN.json",
        "retest_route": guide.get("route", ""),
        "retest_cues": guide.get("cues", []),
        "next_action": "Launch the repaired exact build in verified-fullscreen MesenCE and re-test the SAME failed case now. A PASS does not waive other stale/pending cases.",
        "privacy_contract": {"metadata_only": True, "absolute_local_paths": False, "capture_pixels": False, "rom_bytes": False},
    }
    return _write_outputs(result, root / "Reports" / "RegressionRepairSprint")


def _validate_retest_token(project_root: Path, repaired_pack: Path, token: dict) -> None:
    if token.get("schema") != RETEST_SCHEMA:
        raise RepairSprintError("Invalid repair retest token schema.")
    current_fp = pack_fingerprint(Path(repaired_pack))
    if current_fp != token.get("repaired_runtime_fingerprint"):
        raise RepairSprintError("Repair retest token belongs to a different repaired runtime fingerprint.")
    manifest = _load_json(Path(project_root) / "FINAL_REGRESSION.json")
    history = list(manifest.get("history") or [])
    source_fp = token.get("source_runtime_fingerprint")
    case_key = token.get("case_key")
    category = token.get("failure_category")
    if not any(
        row.get("case") == case_key
        and str(row.get("result", "")).upper() == "FAIL"
        and row.get("pack_fingerprint") == source_fp
        and str(row.get("failure_category", "")).upper() == str(category or "").upper()
        for row in history
    ):
        raise RepairSprintError("Repair retest token is not backed by the original authoritative FAIL history.")


def record_retest(project_root: Path, repaired_pack: Path, result: str, *, category: str = "OTHER", notes: str = "", failure_notes: str = "") -> dict:
    root = Path(project_root)
    token_path = root / "Artwork" / "CurrentRepairSprint" / "REPAIR_RETEST_TOKEN.json"
    token = _load_json(token_path)
    _validate_retest_token(root, repaired_pack, token)
    case_key = str(token["case_key"])
    evidence = record_case_result(root / "FINAL_REGRESSION.json", case_key, Path(repaired_pack), result, notes=notes, failure_category=category, failure_notes=failure_notes)
    after = cockpit_status(root / "FINAL_REGRESSION.json", Path(repaired_pack))
    recorded = str(result).upper()
    if recorded == "PASS":
        action = "Repair target PASSed on the repaired fingerprint. Continue the authoritative cockpit from its first remaining FAIL/STALE/PENDING case; all 10 current-build PASSes are still required."
    else:
        action = "Repair target still FAILs on the repaired fingerprint. Keep this case first, refine the repair target and repeat transactional QA + exact-case re-test."
    output = {
        "schema": SCHEMA,
        "generated_utc": _now(),
        "status": f"REPAIR_RETEST_{recorded}",
        "recorded": evidence,
        "repaired_runtime_fingerprint": token.get("repaired_runtime_fingerprint"),
        "cockpit_counts": after.get("counts", {}),
        "cockpit_gate": after.get("gate"),
        "next_authoritative_case": after.get("next_case"),
        "next_action": action,
        "roadmap_policy": "Repair retest evidence never auto-completes Gate A-D; final Gate C still requires 10/10 current-build PASS.",
        "privacy_contract": {"metadata_only": True, "absolute_local_paths": False, "capture_pixels": False, "rom_bytes": False},
    }
    return _write_outputs(output, root / "Reports" / "RegressionRepairSprint")


def _write_outputs(result: dict, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "REGRESSION_REPAIR_SPRINT.json"
    html_path = output_dir / "REGRESSION_REPAIR_SPRINT.html"
    safe = dict(result)
    safe.pop("outputs", None)
    json_path.write_text(json.dumps(safe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    failed = result.get("failed_case") or {}
    counts = result.get("cockpit_counts") or {}
    cues = "".join(f"<li>{html.escape(str(c))}</li>" for c in result.get("retest_cues", []))
    document = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><title>Regression Repair Sprint</title><style>body{{font:15px system-ui;max-width:1150px;margin:28px auto;padding:0 22px;background:#0d1117;color:#e6edf3}}.card{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:18px;margin:14px 0}}code{{color:#79c0ff}}.warn{{color:#f2cc60}}</style></head><body><h1>Project #002 — Regression Defect → Repair Sprint</h1><div class='card'><h2>{html.escape(str(result.get('status','UNKNOWN')))}</h2><p>Case: <code>{html.escape(str(failed.get('key') or (result.get('recorded') or {}).get('case','—')))}</code> · {html.escape(str(failed.get('label','')))}</p><p>Category: {html.escape(str(failed.get('category') or failed.get('failure_category') or '—'))}</p><p>Repair items: {html.escape(str(result.get('repair_items','—')))}</p><p>Current cockpit: PASS {counts.get('PASS','—')} · FAIL {counts.get('FAIL','—')} · STALE {counts.get('STALE','—')} · PENDING {counts.get('PENDING','—')}</p></div><div class='card'><h2>Exact repair re-test</h2><p><b>Route:</b> {html.escape(str(result.get('retest_route','')))}</p><ul>{cues}</ul></div><div class='card'><h2>DO THIS NEXT</h2><p>{html.escape(str(result.get('next_action','')))}</p><p class='warn'>This report is metadata-only. Local repair PNG/contact boards remain uncommitted production material.</p></div></body></html>"""
    html_path.write_text(document, encoding="utf-8")
    result["outputs"] = {"json": json_path.name, "dashboard": html_path.name}
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 failed-regression -> minimal repair sprint -> exact-case retest director")
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare"); prepare.add_argument("project_root", type=Path); prepare.add_argument("runtime_pack", type=Path); prepare.add_argument("--overwrite", action="store_true")
    finish = sub.add_parser("finish"); finish.add_argument("project_root", type=Path); finish.add_argument("runtime_pack", type=Path); finish.add_argument("--output-pack", type=Path)
    retest = sub.add_parser("retest"); retest.add_argument("project_root", type=Path); retest.add_argument("repaired_pack", type=Path); retest.add_argument("result", choices=("PASS", "FAIL")); retest.add_argument("--category", choices=FAILURE_CATEGORIES, default="OTHER"); retest.add_argument("--notes", default=""); retest.add_argument("--failure-notes", default="")
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            result = prepare_repair_sprint(args.project_root, args.runtime_pack, overwrite=args.overwrite)
        elif args.command == "finish":
            result = finish_repair(args.project_root, args.runtime_pack, output_pack=args.output_pack)
        else:
            result = record_retest(args.project_root, args.repaired_pack, args.result, category=args.category, notes=args.notes, failure_notes=args.failure_notes)
    except (RepairSprintError, ValueError, FileNotFoundError) as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, ensure_ascii=False))
        return 3
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
