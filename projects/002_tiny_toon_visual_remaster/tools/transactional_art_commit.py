from __future__ import annotations

import json
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from animation_consistency_gate import audit_animation_consistency
from art_sprint_kit import MANIFEST_NAME, _sha256, import_sprint_kit
from art_workspace import apply_workspace, scan_workspace
from visual_quality_gate import audit_workspace_visual_quality


def _load_manifest(kit_dir: Path) -> dict:
    path = Path(kit_dir) / MANIFEST_NAME
    if not path.is_file():
        raise ValueError(f"Missing sprint manifest: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _changed_manifest_items(manifest: dict, kit_dir: Path) -> list[dict]:
    changed: list[dict] = []
    for item in manifest.get("items", []):
        kit_file = Path(kit_dir) / "editable" / item["kit_file"]
        if not kit_file.is_file():
            raise ValueError(f"Missing sprint editable file: {item['kit_file']}")
        if _sha256(kit_file) != item["workspace_editable_sha256_at_export"]:
            changed.append(item)
    return changed


def _assert_real_workspace_fresh(workspace: Path, items: list[dict]) -> None:
    for item in items:
        target = Path(workspace) / "editable" / item["master_file"]
        if not target.is_file():
            raise ValueError(f"MasterWorkspace target disappeared: {item['master_file']}")
        current = _sha256(target)
        expected = item["workspace_editable_sha256_at_export"]
        if current != expected:
            raise ValueError(
                "Transactional art commit blocked by stale MasterWorkspace file: "
                f"{item['master_file']}. Re-export the sprint or reconcile the newer master first."
            )


def _atomic_copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(f".{target.name}.swir-tx-{uuid.uuid4().hex}.tmp")
    shutil.copy2(source, temp)
    os.replace(temp, target)


def _restore_files(backup_root: Path, workspace: Path, names: list[str], state_existed: bool) -> None:
    for name in names:
        backup = backup_root / "editable" / name
        target = Path(workspace) / "editable" / name
        if backup.is_file():
            _atomic_copy(backup, target)
    state_backup = backup_root / "ART_STATE.csv"
    state_target = Path(workspace) / "ART_STATE.csv"
    if state_existed and state_backup.is_file():
        _atomic_copy(state_backup, state_target)
    elif not state_existed and state_target.exists():
        state_target.unlink()


def transactional_finish_sprint(
    pack_dir: Path,
    workspace: Path,
    kit_dir: Path,
    output_pack: Path,
    *,
    overwrite: bool = False,
) -> dict:
    """Stage sprint edits, run visual/family/pack QA, then commit only an all-green candidate.

    The authoritative MasterWorkspace and output pack remain untouched when catastrophic
    master-tile visual regressions, animation-family geometry inconsistencies, Pixel QA
    failures, hires.txt mapping changes or stale workspace conflicts are detected.
    """
    pack_dir = Path(pack_dir)
    workspace = Path(workspace)
    kit_dir = Path(kit_dir)
    output_pack = Path(output_pack)
    manifest = _load_manifest(kit_dir)
    changed = _changed_manifest_items(manifest, kit_dir)
    _assert_real_workspace_fresh(workspace, changed)

    if output_pack.exists() and not overwrite:
        raise FileExistsError(f"Output pack already exists: {output_pack}")

    tx_parent = workspace.parent / ".ArtTransactions"
    tx_parent.mkdir(parents=True, exist_ok=True)
    tx_root = tx_parent / f"tx-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    staged_workspace = tx_root / "MasterWorkspace"
    staged_output = tx_root / "CandidatePack"
    backup_root = tx_root / "Rollback"
    previous_output = tx_root / "PreviousOutput"
    tx_root.mkdir(parents=True, exist_ok=False)

    committed_files: list[str] = []
    output_swapped = False
    state_target = workspace / "ART_STATE.csv"
    state_existed = state_target.is_file()

    try:
        shutil.copytree(workspace, staged_workspace)
        imported = import_sprint_kit(staged_workspace, kit_dir)
        visual_report_path = kit_dir / "ART_VISUAL_QUALITY_GATE.json"
        visual_quality = audit_workspace_visual_quality(staged_workspace, changed, visual_report_path)

        if visual_quality.get("qa_gate") != "PASS":
            result = {
                "schema": "swir.project002.transactional-art-commit.v3",
                "generated_utc": datetime.now(timezone.utc).isoformat(),
                "changed_candidates": len(changed),
                "imported": int(imported.get("imported", 0)),
                "imported_files": list(imported.get("imported_files", [])),
                "visual_quality_gate": visual_quality,
                "animation_consistency_gate": {"qa_gate": "NOT_RUN"},
                "qa_gate": "NOT_RUN",
                "mapping_preserved": False,
                "workspace_committed": False,
                "output_committed": False,
                "transaction_status": "BLOCKED_VISUAL_QA",
                "next_action": "Fix catastrophic master-tile visual regressions listed in ART_VISUAL_QUALITY_GATE.json; authoritative state was not modified.",
                "roadmap_policy": "A transaction commit is production evidence only; it never edits Gate A-D automatically.",
            }
            (kit_dir / "TRANSACTIONAL_ART_FINISH.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            return result

        animation_report_path = kit_dir / "ART_ANIMATION_CONSISTENCY_GATE.json"
        animation_consistency = audit_animation_consistency(staged_workspace, changed, animation_report_path)
        if animation_consistency.get("qa_gate") != "PASS":
            result = {
                "schema": "swir.project002.transactional-art-commit.v3",
                "generated_utc": datetime.now(timezone.utc).isoformat(),
                "changed_candidates": len(changed),
                "imported": int(imported.get("imported", 0)),
                "imported_files": list(imported.get("imported_files", [])),
                "visual_quality_gate": visual_quality,
                "animation_consistency_gate": animation_consistency,
                "qa_gate": "NOT_RUN",
                "mapping_preserved": False,
                "workspace_committed": False,
                "output_committed": False,
                "transaction_status": "BLOCKED_ANIMATION_CONSISTENCY",
                "next_action": "Repair family/palette frame geometry listed in ART_ANIMATION_CONSISTENCY_GATE.json; authoritative state was not modified.",
                "roadmap_policy": "A transaction commit is production evidence only; it never edits Gate A-D automatically.",
            }
            (kit_dir / "TRANSACTIONAL_ART_FINISH.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            return result

        applied = apply_workspace(pack_dir, staged_workspace, staged_output, overwrite=True)
        qa_gate = str(applied.get("pixel_qa", {}).get("qa_gate", "FAIL"))
        mapping_preserved = bool(applied.get("mapping_preserved", False))

        base_result = {
            "schema": "swir.project002.transactional-art-commit.v3",
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "changed_candidates": len(changed),
            "imported": int(imported.get("imported", 0)),
            "imported_files": list(imported.get("imported_files", [])),
            "visual_quality_gate": visual_quality,
            "animation_consistency_gate": animation_consistency,
            "qa_gate": qa_gate,
            "mapping_preserved": mapping_preserved,
            "workspace_committed": False,
            "output_committed": False,
            "roadmap_policy": "A transaction commit is production evidence only; it never edits Gate A-D automatically.",
        }

        if qa_gate != "PASS" or not mapping_preserved:
            base_result["transaction_status"] = "BLOCKED_QA"
            base_result["next_action"] = "Fix Pixel QA or hires.txt preservation in the sprint; MasterWorkspace was not modified."
            (kit_dir / "TRANSACTIONAL_ART_FINISH.json").write_text(json.dumps(base_result, indent=2) + "\n", encoding="utf-8")
            return base_result

        _assert_real_workspace_fresh(workspace, changed)

        (backup_root / "editable").mkdir(parents=True, exist_ok=True)
        for item in changed:
            name = item["master_file"]
            shutil.copy2(workspace / "editable" / name, backup_root / "editable" / name)
        if state_existed:
            shutil.copy2(state_target, backup_root / "ART_STATE.csv")

        if output_pack.exists():
            output_pack.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(output_pack), str(previous_output))
        output_pack.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(staged_output), str(output_pack))
        output_swapped = True

        for item in changed:
            name = item["master_file"]
            _atomic_copy(staged_workspace / "editable" / name, workspace / "editable" / name)
            committed_files.append(name)
        scan_workspace(workspace)

        result = dict(base_result)
        result.update({
            "transaction_status": "COMMITTED",
            "workspace_committed": True,
            "output_committed": True,
            "committed_files": committed_files,
            "next_action": "Candidate passed master-tile visual QA, animation consistency QA, Pixel QA and hires.txt preservation and was committed atomically.",
        })
        (kit_dir / "TRANSACTIONAL_ART_FINISH.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        return result
    except Exception:
        if committed_files:
            _restore_files(backup_root, workspace, committed_files, state_existed)
        if output_swapped:
            if output_pack.exists():
                shutil.rmtree(output_pack)
            if previous_output.exists():
                shutil.move(str(previous_output), str(output_pack))
        raise
    finally:
        if tx_root.exists():
            shutil.rmtree(tx_root, ignore_errors=True)
        try:
            if tx_parent.exists() and not any(tx_parent.iterdir()):
                tx_parent.rmdir()
        except OSError:
            pass
