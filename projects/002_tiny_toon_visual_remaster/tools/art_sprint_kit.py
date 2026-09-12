from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from art_workspace import apply_workspace, scan_workspace
from final_art_priority import build_priority_rows

MANIFEST_NAME = "ART_SPRINT_KIT.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_state(workspace: Path) -> dict[tuple[str, str], dict]:
    scan_workspace(workspace)
    state = workspace / "ART_STATE.csv"
    with state.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {
        ((row.get("tile_id") or "").upper(), (row.get("palette") or "").upper()): row
        for row in rows if row.get("tile_id") and row.get("palette")
    }


def _make_board(items: list[dict], kit_dir: Path) -> str | None:
    if not items:
        return None
    thumbs = []
    for item in items:
        path = kit_dir / "editable" / item["kit_file"]
        with Image.open(path) as image:
            thumb = image.convert("RGBA")
        thumb.thumbnail((128, 128), Image.Resampling.NEAREST)
        thumbs.append((item, thumb))
    columns = 5
    cell_w, cell_h = 190, 205
    rows = (len(thumbs) + columns - 1) // columns
    board = Image.new("RGBA", (columns * cell_w, rows * cell_h), (18, 22, 28, 255))
    draw = ImageDraw.Draw(board)
    font = ImageFont.load_default()
    for index, (item, thumb) in enumerate(thumbs):
        col, row = index % columns, index // columns
        x, y = col * cell_w, row * cell_h
        board.alpha_composite(thumb, (x + (cell_w - thumb.width) // 2, y + 8))
        draw.text((x + 8, y + 142), f"#{item['priority']} score {item['priority_score']}", fill=(245, 245, 245, 255), font=font)
        draw.text((x + 8, y + 158), f"{item['group']} {item['tile_id']} {item['palette'][:8]}", fill=(130, 200, 255, 255), font=font)
        draw.text((x + 8, y + 174), item["master_file"][:25], fill=(180, 185, 195, 255), font=font)
    path = kit_dir / "LOCAL_ART_SPRINT_BOARD.png"
    board.save(path, optimize=True)
    return path.name


def export_sprint_kit(
    pack_dir: Path,
    workspace: Path,
    kit_dir: Path,
    *,
    queue: Path | None = None,
    visual_review: Path | None = None,
    animation_review: Path | None = None,
    top: int = 20,
    overwrite: bool = False,
) -> dict:
    if not (workspace / "MASTER_TILES.json").is_file():
        raise ValueError("MasterWorkspace is missing MASTER_TILES.json")
    if kit_dir.exists() and any(kit_dir.iterdir()):
        if not overwrite:
            raise FileExistsError(f"Sprint kit is not empty: {kit_dir}")
        shutil.rmtree(kit_dir)
    editable_out = kit_dir / "editable"
    reference_out = kit_dir / "reference"
    editable_out.mkdir(parents=True, exist_ok=True)
    reference_out.mkdir(parents=True, exist_ok=True)

    states = _read_state(workspace)
    priority = build_priority_rows(pack_dir, queue, workspace, visual_review, animation_review)
    selected = priority[: max(1, top)]
    items: list[dict] = []
    missing: list[dict] = []
    for row in selected:
        key = (row["tile_id"].upper(), row["palette"].upper())
        state = states.get(key)
        if not state:
            missing.append({"tile_id": row["tile_id"], "palette": row["palette"]})
            continue
        master_file = state["master_file"]
        source_editable = workspace / "editable" / master_file
        source_original = workspace / "original" / master_file
        if not source_editable.is_file() or not source_original.is_file():
            missing.append({"tile_id": row["tile_id"], "palette": row["palette"], "master_file": master_file})
            continue
        with Image.open(source_editable) as image:
            size = list(image.size)
        kit_file = f"{row['priority']:03d}_{master_file}"
        shutil.copy2(source_editable, editable_out / kit_file)
        shutil.copy2(source_original, reference_out / kit_file)
        items.append({
            "priority": row["priority"],
            "priority_score": row["priority_score"],
            "group": row["group"],
            "tile_id": row["tile_id"],
            "palette": row["palette"],
            "uses": row["uses"],
            "reasons": row["reasons"],
            "master_file": master_file,
            "kit_file": kit_file,
            "dimensions": size,
            "workspace_editable_sha256_at_export": _sha256(source_editable),
            "workspace_original_sha256": _sha256(source_original),
        })

    manifest = {
        "schema": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source_pack": str(pack_dir.resolve()),
        "workspace": str(workspace.resolve()),
        "requested_top": top,
        "exported": len(items),
        "missing_workspace_matches": missing,
        "instructions": [
            "Edit PNG files only in editable/; reference/ is the untouched visual baseline.",
            "Keep dimensions and alpha canvas size unchanged.",
            "Do not rename kit files.",
            "Run import before changing the same MasterWorkspace files elsewhere; stale edits are conflict-blocked.",
            "Use finish to import, compose the HD pack and run pixel QA in one step.",
            "LOCAL_ART_SPRINT_BOARD.png and all kit graphics are local ROM-derived production assets and must never be committed.",
        ],
        "items": items,
    }
    (kit_dir / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    board = _make_board(items, kit_dir)
    manifest["local_board"] = board
    (kit_dir / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def import_sprint_kit(workspace: Path, kit_dir: Path) -> dict:
    manifest_path = kit_dir / MANIFEST_NAME
    if not manifest_path.is_file():
        raise ValueError(f"Missing sprint manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    imported: list[str] = []
    unchanged: list[str] = []
    conflicts: list[str] = []
    invalid: list[str] = []

    for item in manifest.get("items", []):
        master_file = item["master_file"]
        kit_file = kit_dir / "editable" / item["kit_file"]
        target = workspace / "editable" / master_file
        if not kit_file.is_file() or not target.is_file():
            invalid.append(f"missing:{master_file}")
            continue
        with Image.open(kit_file) as candidate:
            candidate_size = list(candidate.size)
        if candidate_size != item["dimensions"]:
            invalid.append(f"size:{master_file}:{candidate_size}!={item['dimensions']}")
            continue
        export_sha = item["workspace_editable_sha256_at_export"]
        current_sha = _sha256(target)
        kit_sha = _sha256(kit_file)
        if kit_sha == export_sha:
            unchanged.append(master_file)
            continue
        if current_sha != export_sha:
            conflicts.append(master_file)
            continue
        shutil.copy2(kit_file, target)
        imported.append(master_file)

    if invalid:
        raise ValueError("Sprint import blocked by invalid files: " + "; ".join(invalid))
    if conflicts:
        raise ValueError(
            "Sprint import blocked by stale workspace conflicts: " + ", ".join(conflicts) +
            ". Re-export a fresh sprint kit or manually reconcile those masters."
        )
    scan = scan_workspace(workspace)
    result = {
        "imported": len(imported),
        "imported_files": imported,
        "unchanged": len(unchanged),
        "unchanged_files": unchanged,
        "conflicts": conflicts,
        "workspace_scan": scan,
    }
    (kit_dir / "ART_SPRINT_IMPORT.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def finish_sprint(pack_dir: Path, workspace: Path, kit_dir: Path, output_pack: Path, *, overwrite: bool = False) -> dict:
    imported = import_sprint_kit(workspace, kit_dir)
    applied = apply_workspace(pack_dir, workspace, output_pack, overwrite=overwrite)
    result = {
        "sprint_import": imported,
        "art_apply": applied,
        "qa_gate": applied["pixel_qa"]["qa_gate"],
        "mapping_preserved": applied["mapping_preserved"],
        "output_pack": str(output_pack.resolve()),
    }
    (kit_dir / "ART_SPRINT_FINISH.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 top-priority final-art sprint exporter/importer")
    commands = parser.add_subparsers(dest="command", required=True)

    export = commands.add_parser("export")
    export.add_argument("pack", type=Path)
    export.add_argument("workspace", type=Path)
    export.add_argument("kit", type=Path)
    export.add_argument("--queue", type=Path)
    export.add_argument("--visual-review", type=Path)
    export.add_argument("--animation-review", type=Path)
    export.add_argument("--top", type=int, default=20)
    export.add_argument("--overwrite", action="store_true")

    imp = commands.add_parser("import")
    imp.add_argument("workspace", type=Path)
    imp.add_argument("kit", type=Path)

    finish = commands.add_parser("finish")
    finish.add_argument("pack", type=Path)
    finish.add_argument("workspace", type=Path)
    finish.add_argument("kit", type=Path)
    finish.add_argument("output", type=Path)
    finish.add_argument("--overwrite", action="store_true")

    args = parser.parse_args()
    if args.command == "export":
        result = export_sprint_kit(
            args.pack, args.workspace, args.kit, queue=args.queue,
            visual_review=args.visual_review, animation_review=args.animation_review,
            top=args.top, overwrite=args.overwrite,
        )
    elif args.command == "import":
        result = import_sprint_kit(args.workspace, args.kit)
    else:
        result = finish_sprint(args.pack, args.workspace, args.kit, args.output, overwrite=args.overwrite)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
