from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

import regression_repair_sprint as repair
from art_sprint_kit import MANIFEST_NAME, _sha256
from guided_regression_playtest import CASE_GUIDANCE

SCHEMA = "swir.project002.regression-repair-session.v1"


class RepairSessionError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _base(status: str, *, next_action: str) -> dict:
    return {
        "schema": SCHEMA,
        "generated_utc": _now(),
        "status": status,
        "next_action": next_action,
        "roadmap_policy": "Repair-session resume never auto-completes Gate A-D and never records PASS/FAIL.",
        "privacy_contract": {
            "metadata_only": True,
            "absolute_local_paths": False,
            "capture_pixels": False,
            "rom_bytes": False,
            "save_states": False,
            "emulator_binaries": False,
        },
    }


def _blocked(status: str, reason: str, *, failed_case: dict | None = None) -> dict:
    result = _base(status, next_action=reason)
    result["blocked"] = True
    result["reason"] = reason
    if failed_case:
        result["failed_case"] = failed_case
    return result


def inspect_repair_session(project_root: Path, runtime_pack: Path, *, repaired_pack: Path | None = None) -> dict:
    root = Path(project_root)
    runtime = Path(runtime_pack)
    kit = root / "Artwork" / "CurrentRepairSprint"
    manifest_path = kit / MANIFEST_NAME
    if not manifest_path.is_file():
        result = _base(
            "NO_PREPARED_REPAIR",
            next_action="Prepare a minimal repair sprint for the authoritative current-build FAIL.",
        )
        result.update({"blocked": False, "repair_items": 0, "local_board": None, "family_board_count": 0})
        return result

    try:
        manifest = repair._load_json(manifest_path)
    except repair.RepairSprintError as exc:
        return _blocked("INVALID_PREPARED_REPAIR", str(exc))
    if manifest.get("selection_mode") != "failed-regression-minimal-repair":
        return _blocked(
            "INVALID_PREPARED_REPAIR",
            "CurrentRepairSprint is not a failed-regression minimal repair sprint. Preserve it and resolve it manually before continuing.",
        )

    failed_manifest = manifest.get("failed_case") or {}
    manifest_case = str(failed_manifest.get("key") or "")
    manifest_category = str(failed_manifest.get("failure_category") or "OTHER").upper()
    failed_case = {
        "key": manifest_case,
        "label": failed_manifest.get("label"),
        "category": manifest_category,
    }

    try:
        cockpit, current_case = repair._current_failure(root, runtime)
    except repair.RepairSprintError as exc:
        return _blocked("STALE_PREPARED_REPAIR", str(exc), failed_case=failed_case)

    current_case_key = str(current_case.get("key") or "")
    if current_case_key != manifest_case:
        return _blocked(
            "STALE_PREPARED_REPAIR",
            f"Prepared repair belongs to {manifest_case or '<unknown>'}, but the authoritative current FAIL is {current_case_key or '<unknown>'}. Do not reuse this sprint.",
            failed_case=failed_case,
        )

    expected_fp = str(manifest.get("expected_runtime_fingerprint") or "")
    current_fp = str(cockpit.get("pack_fingerprint") or "")
    if not expected_fp or current_fp != expected_fp:
        return _blocked(
            "STALE_PREPARED_REPAIR",
            "Source runtime fingerprint changed since CurrentRepairSprint was prepared. Rebuild the sprint from the current authoritative FAIL.",
            failed_case=failed_case,
        )

    workspace = root / "Artwork" / "MasterWorkspace"
    items = list(manifest.get("items") or [])
    if not items:
        return _blocked("INVALID_PREPARED_REPAIR", "CurrentRepairSprint contains no repair items.", failed_case=failed_case)

    invalid: list[str] = []
    workspace_conflicts: list[str] = []
    changed_files: list[str] = []
    for item in items:
        master_file = str(item.get("master_file") or "")
        kit_file = str(item.get("kit_file") or "")
        expected_sha = str(item.get("workspace_editable_sha256_at_export") or "")
        expected_dimensions = list(item.get("dimensions") or [])
        if not master_file or not kit_file or not expected_sha or len(expected_dimensions) != 2:
            invalid.append(master_file or kit_file or "<unnamed>")
            continue
        current_master = workspace / "editable" / master_file
        editable = kit / "editable" / kit_file
        reference = kit / "reference" / kit_file
        if not current_master.is_file() or not editable.is_file() or not reference.is_file():
            invalid.append(master_file)
            continue
        if _sha256(current_master) != expected_sha:
            workspace_conflicts.append(master_file)
            continue
        try:
            with Image.open(editable) as image:
                dimensions = list(image.size)
        except OSError:
            invalid.append(master_file)
            continue
        if dimensions != expected_dimensions:
            invalid.append(master_file)
            continue
        if _sha256(editable) != expected_sha:
            changed_files.append(master_file)

    if invalid:
        return _blocked(
            "INVALID_PREPARED_REPAIR",
            "Prepared repair has missing/corrupt/resized files: " + ", ".join(sorted(set(invalid))),
            failed_case=failed_case,
        )
    if workspace_conflicts:
        return _blocked(
            "WORKSPACE_CONFLICT",
            "MasterWorkspace changed after repair export: " + ", ".join(sorted(set(workspace_conflicts))) + ". Re-export/reconcile before transactional QA.",
            failed_case=failed_case,
        )

    guide = CASE_GUIDANCE.get(manifest_case, {})
    common = {
        "blocked": False,
        "runtime_fingerprint": current_fp,
        "failed_case": failed_case,
        "repair_items": len(items),
        "edited_items": len(changed_files),
        "edited_files": changed_files,
        "local_board": manifest.get("local_board"),
        "family_board_count": int(manifest.get("family_contact_board_count", 0) or 0),
        "explicit_target": manifest.get("explicit_target"),
        "selection_sources": list(manifest.get("selection_sources") or []),
        "retest_route": guide.get("route", ""),
        "retest_cues": guide.get("cues", []),
    }

    token_path = kit / "REPAIR_RETEST_TOKEN.json"
    if token_path.is_file():
        try:
            token = repair._load_json(token_path)
        except repair.RepairSprintError as exc:
            return _blocked("INVALID_RETEST_TOKEN", str(exc), failed_case=failed_case)
        if str(token.get("case_key") or "") != manifest_case or str(token.get("source_runtime_fingerprint") or "") != expected_fp:
            return _blocked(
                "INVALID_RETEST_TOKEN",
                "Repair retest token does not belong to this prepared case/source fingerprint.",
                failed_case=failed_case,
            )
        candidate = Path(repaired_pack) if repaired_pack else root / "Build" / "RegressionRepairCandidate"
        if not (candidate / "hires.txt").is_file():
            return _blocked(
                "RETEST_CANDIDATE_MISSING",
                "Repair retest token exists but the repaired candidate pack is missing. Re-run transactional finish or restore the exact candidate.",
                failed_case=failed_case,
            )
        try:
            repair._validate_retest_token(root, candidate, token)
        except repair.RepairSprintError as exc:
            return _blocked("RETEST_TOKEN_STALE", str(exc), failed_case=failed_case)
        result = _base(
            "RETEST_READY",
            next_action="Resume directly at verified-fullscreen SAME-CASE retest; do not rebuild or re-finish the repair.",
        )
        result.update(common)
        result.update({
            "repaired_runtime_fingerprint": token.get("repaired_runtime_fingerprint"),
            "retest_token": "Artwork/CurrentRepairSprint/REPAIR_RETEST_TOKEN.json",
        })
        return result

    status = "READY_TO_FINISH" if changed_files else "READY_TO_EDIT"
    action = (
        "Resume this exact prepared sprint and run transactional QA; do not call prepare again."
        if changed_files
        else "Resume this exact prepared sprint, edit CurrentRepairSprint/editable, then run transactional QA without re-preparing it."
    )
    result = _base(status, next_action=action)
    result.update(common)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect/resume Project #002 regression repair sessions without mutating art state")
    parser.add_argument("project_root", type=Path)
    parser.add_argument("runtime_pack", type=Path)
    parser.add_argument("--repaired-pack", type=Path)
    args = parser.parse_args()
    try:
        result = inspect_repair_session(args.project_root, args.runtime_pack, repaired_pack=args.repaired_pack)
    except (RepairSessionError, ValueError, FileNotFoundError) as exc:
        print(json.dumps({"schema": SCHEMA, "status": "BLOCKED", "error": str(exc)}, ensure_ascii=False))
        return 3
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
