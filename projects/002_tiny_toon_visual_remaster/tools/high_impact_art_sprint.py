from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from art_sprint_kit import MANIFEST_NAME, _make_board, _read_state, _sha256, finish_sprint
from visual_completion_matrix import build_and_write


def prepare_high_impact_sprint(
    pack_dir: Path,
    workspace: Path,
    kit_dir: Path,
    report_dir: Path,
    *,
    queue: Path | None = None,
    batch_size: int = 30,
    overwrite: bool = False,
) -> dict:
    """Build the completion matrix and export its exact highest-impact batch as an editable sprint kit."""
    pack_dir = Path(pack_dir)
    workspace = Path(workspace)
    kit_dir = Path(kit_dir)
    report_dir = Path(report_dir)

    if not (pack_dir / "hires.txt").is_file():
        raise ValueError("HD pack/capture is missing hires.txt")
    if not (workspace / "MASTER_TILES.json").is_file():
        raise ValueError("MasterWorkspace is missing MASTER_TILES.json")
    if kit_dir.exists() and any(kit_dir.iterdir()):
        if not overwrite:
            raise FileExistsError(f"Sprint kit is not empty: {kit_dir}")
        shutil.rmtree(kit_dir)

    matrix = build_and_write(
        pack_dir,
        report_dir,
        queue=Path(queue) if queue else None,
        workspace=workspace,
        batch_size=batch_size,
    )
    selected = matrix["next_batch"]
    states = _read_state(workspace)

    editable_out = kit_dir / "editable"
    reference_out = kit_dir / "reference"
    editable_out.mkdir(parents=True, exist_ok=True)
    reference_out.mkdir(parents=True, exist_ok=True)

    items: list[dict] = []
    missing: list[dict] = []
    for row in selected:
        key = (row["tile_id"].upper(), row["palette"].upper())
        state = states.get(key)
        if not state:
            missing.append({"tile_id": row["tile_id"], "palette": row["palette"], "reason": "missing-workspace-state"})
            continue
        master_file = state.get("master_file") or ""
        source_editable = workspace / "editable" / master_file
        source_original = workspace / "original" / master_file
        if not master_file or not source_editable.is_file() or not source_original.is_file():
            missing.append({"tile_id": row["tile_id"], "palette": row["palette"], "master_file": master_file, "reason": "missing-master-files"})
            continue
        with Image.open(source_editable) as image:
            dimensions = list(image.size)
        order = int(row["batch_order"])
        kit_file = f"{order:03d}_{master_file}"
        shutil.copy2(source_editable, editable_out / kit_file)
        shutil.copy2(source_original, reference_out / kit_file)
        items.append({
            "priority": order,
            "priority_score": row["impact_score"],
            "impact_score": row["impact_score"],
            "group": row["group"],
            "tile_id": row["tile_id"],
            "palette": row["palette"],
            "status_at_export": row["status"],
            "uses": row["uses"],
            "condition_count": row["condition_count"],
            "visual_variants": row["visual_variants"],
            "reasons": row["reasons"],
            "master_file": master_file,
            "kit_file": kit_file,
            "dimensions": dimensions,
            "workspace_editable_sha256_at_export": _sha256(source_editable),
            "workspace_original_sha256": _sha256(source_original),
        })

    manifest = {
        "schema": 2,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "selection_mode": "visual-completion-high-impact",
        "source_pack": str(pack_dir.resolve()),
        "workspace": str(workspace.resolve()),
        "visual_completion_report": str((report_dir / "VISUAL_COMPLETION_MATRIX.json").resolve()),
        "requested_batch_size": batch_size,
        "matrix_overall_weighted_percent": matrix["overall_weighted_percent"],
        "matrix_captured_unfinished": matrix["captured_unfinished"],
        "matrix_blocking_items": matrix["blocking_items"],
        "exported": len(items),
        "missing_workspace_matches": missing,
        "instructions": [
            "This kit is the exact NEXT_HIGH_IMPACT_ART_BATCH selected by Visual Completion Matrix.",
            "Edit PNG files only in editable/; reference/ is the untouched visual baseline.",
            "Keep dimensions and alpha canvas size unchanged and do not rename kit files.",
            "Finish with high_impact_art_sprint.py finish (or the Windows launcher) to import, compose and Pixel-QA the exact build.",
            "Stale MasterWorkspace conflicts are blocked by SHA-256 checks during import.",
            "All local board/PNG outputs can contain ROM-derived graphics and must never be committed.",
        ],
        "items": items,
    }
    (kit_dir / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    board = _make_board(items, kit_dir)
    manifest["local_board"] = board
    (kit_dir / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    result = {
        "status": "READY" if items and not missing else ("PARTIAL" if items else "BLOCKED"),
        "selection_mode": manifest["selection_mode"],
        "exported": len(items),
        "missing": len(missing),
        "matrix": {
            "overall_weighted_percent": matrix["overall_weighted_percent"],
            "captured_unfinished": matrix["captured_unfinished"],
            "blocking_items": matrix["blocking_items"],
        },
        "kit": str(kit_dir.resolve()),
        "board": str((kit_dir / board).resolve()) if board else None,
        "manifest": str((kit_dir / MANIFEST_NAME).resolve()),
        "dashboard": matrix["outputs"]["dashboard"],
        "batch_csv": matrix["outputs"]["batch_csv"],
    }
    (kit_dir / "HIGH_IMPACT_SPRINT_READY.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 high-impact art sprint director")
    commands = parser.add_subparsers(dest="command", required=True)

    prepare = commands.add_parser("prepare", help="Build matrix and export its exact top batch")
    prepare.add_argument("pack", type=Path)
    prepare.add_argument("workspace", type=Path)
    prepare.add_argument("kit", type=Path)
    prepare.add_argument("reports", type=Path)
    prepare.add_argument("--queue", type=Path)
    prepare.add_argument("--batch-size", type=int, default=30)
    prepare.add_argument("--overwrite", action="store_true")

    finish = commands.add_parser("finish", help="Import edited batch, compose output pack and run Pixel QA")
    finish.add_argument("pack", type=Path)
    finish.add_argument("workspace", type=Path)
    finish.add_argument("kit", type=Path)
    finish.add_argument("output", type=Path)
    finish.add_argument("--overwrite", action="store_true")

    args = parser.parse_args()
    if args.command == "prepare":
        result = prepare_high_impact_sprint(
            args.pack, args.workspace, args.kit, args.reports,
            queue=args.queue, batch_size=max(1, args.batch_size), overwrite=args.overwrite,
        )
    else:
        result = finish_sprint(args.pack, args.workspace, args.kit, args.output, overwrite=args.overwrite)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
