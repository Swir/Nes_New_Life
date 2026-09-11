from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from collections import defaultdict
from pathlib import Path

from PIL import Image

from art_production import export_master_tiles
from validate_hdpack import validate

STATE_FIELDS = ("master_file", "group", "tile_id", "palette", "uses", "status", "original_sha256", "editable_sha256")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _image_index_map(pack_dir: Path) -> dict[str, Path]:
    images: list[Path] = []
    for raw in (pack_dir / "hires.txt").read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = raw.strip()
        if line.lower().startswith("<img>"):
            images.append(pack_dir / line[5:].strip())
    return {str(index): path for index, path in enumerate(images)}


def init_workspace(pack_dir: Path, output_dir: Path, queue: Path | None = None, overwrite: bool = False) -> dict:
    errors, _, _ = validate(pack_dir)
    if errors:
        raise ValueError("Source HD pack is invalid: " + "; ".join(errors))
    if output_dir.exists() and any(output_dir.iterdir()) and not overwrite:
        raise FileExistsError(f"Workspace is not empty: {output_dir}")
    if overwrite and output_dir.exists():
        shutil.rmtree(output_dir)

    originals = output_dir / "original"
    editable = output_dir / "editable"
    originals.mkdir(parents=True, exist_ok=True)
    editable.mkdir(parents=True, exist_ok=True)

    manifest = export_master_tiles(pack_dir, originals, queue)
    rows: list[dict[str, str]] = []
    for master in manifest.get("masters", []):
        source = originals / master["file"]
        target = editable / master["file"]
        shutil.copy2(source, target)
        sha = _sha256(source)
        rows.append({
            "master_file": master["file"],
            "group": master.get("group", "UNASSIGNED"),
            "tile_id": master.get("tile_id", ""),
            "palette": master.get("palette", ""),
            "uses": str(master.get("uses", 0)),
            "status": "TODO",
            "original_sha256": sha,
            "editable_sha256": sha,
        })

    shutil.copy2(originals / "MASTER_TILES.json", output_dir / "MASTER_TILES.json")
    with (output_dir / "ART_STATE.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=STATE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    info = {
        "source_pack": str(pack_dir.resolve()),
        "master_count": len(rows),
        "instructions": [
            "Edit PNG files only inside editable/.",
            "Keep every master PNG at exactly the same pixel dimensions.",
            "Run scan to update TODO/EDITED state, then apply to build one combined HD pack.",
            "Never edit original/; it is the pixel-accurate baseline used for change detection.",
        ],
    }
    (output_dir / "WORKSPACE.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    return info


def scan_workspace(workspace: Path) -> dict:
    manifest = json.loads((workspace / "MASTER_TILES.json").read_text(encoding="utf-8"))
    by_name = {item["file"]: item for item in manifest.get("masters", [])}
    rows: list[dict[str, str]] = []
    edited = 0
    invalid = 0

    for name, master in sorted(by_name.items()):
        original = workspace / "original" / name
        editable = workspace / "editable" / name
        status = "TODO"
        original_sha = _sha256(original) if original.is_file() else "MISSING"
        editable_sha = _sha256(editable) if editable.is_file() else "MISSING"
        if not original.is_file() or not editable.is_file():
            status = "INVALID"
            invalid += 1
        else:
            with Image.open(original) as base, Image.open(editable) as changed:
                if base.size != changed.size:
                    status = "INVALID_SIZE"
                    invalid += 1
                elif original_sha != editable_sha:
                    status = "EDITED"
                    edited += 1
        rows.append({
            "master_file": name,
            "group": master.get("group", "UNASSIGNED"),
            "tile_id": master.get("tile_id", ""),
            "palette": master.get("palette", ""),
            "uses": str(master.get("uses", 0)),
            "status": status,
            "original_sha256": original_sha,
            "editable_sha256": editable_sha,
        })

    with (workspace / "ART_STATE.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=STATE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    total = len(rows)
    return {
        "masters": total,
        "edited": edited,
        "todo": total - edited - invalid,
        "invalid": invalid,
        "percent_edited": round((edited / total * 100.0), 2) if total else 0.0,
    }


def apply_workspace(pack_dir: Path, workspace: Path, output_dir: Path, overwrite: bool = False) -> dict:
    scan = scan_workspace(workspace)
    if scan["invalid"]:
        raise ValueError(f"Art workspace has {scan['invalid']} invalid/missing master file(s). Fix them before apply.")

    errors, _, _ = validate(pack_dir)
    if errors:
        raise ValueError("Source HD pack is invalid: " + "; ".join(errors))
    if output_dir.exists() and any(output_dir.iterdir()) and not overwrite:
        raise FileExistsError(f"Output is not empty: {output_dir}")
    if overwrite and output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    image_map = _image_index_map(pack_dir)
    sheets: dict[str, Image.Image] = {}
    sheet_paths: dict[str, Path] = {}
    for index, source in image_map.items():
        if not source.is_file():
            raise FileNotFoundError(f"Missing source sheet: {source}")
        with Image.open(source) as image:
            sheets[index] = image.convert("RGBA")
        sheet_paths[index] = source

    manifest = json.loads((workspace / "MASTER_TILES.json").read_text(encoding="utf-8"))
    changed_masters = 0
    targets_updated = 0
    changed_by_group: dict[str, int] = defaultdict(int)

    for master in manifest.get("masters", []):
        original = workspace / "original" / master["file"]
        editable = workspace / "editable" / master["file"]
        if _sha256(original) == _sha256(editable):
            continue
        with Image.open(original) as source_image, Image.open(editable) as replacement_image:
            source_size = source_image.size
            replacement = replacement_image.convert("RGBA")
        if replacement.size != source_size:
            raise ValueError(f"Edited master changed size: {master['file']} {source_size} -> {replacement.size}")
        changed_masters += 1
        changed_by_group[master.get("group", "UNASSIGNED")] += 1
        for target in master.get("targets", []):
            image_index = str(target["image_index"])
            sheet = sheets.get(image_index)
            if sheet is None:
                raise ValueError(f"Unknown image index {image_index} for {master['file']}")
            x, y = int(target["x"]), int(target["y"])
            w, h = replacement.size
            if x < 0 or y < 0 or x + w > sheet.width or y + h > sheet.height:
                raise ValueError(f"Replacement does not fit {master['file']} at {x},{y}")
            sheet.alpha_composite(replacement, (x, y))
            targets_updated += 1

    for index, sheet in sheets.items():
        source = sheet_paths[index]
        destination = output_dir / source.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(destination, optimize=True)

    (output_dir / "hires.txt").write_bytes((pack_dir / "hires.txt").read_bytes())
    errors, warnings, stats = validate(output_dir)
    if errors:
        raise ValueError("Generated HD pack failed validation: " + "; ".join(errors))

    result = {
        "changed_masters": changed_masters,
        "targets_updated": targets_updated,
        "changed_by_group": dict(sorted(changed_by_group.items())),
        "mapping_preserved": (output_dir / "hires.txt").read_bytes() == (pack_dir / "hires.txt").read_bytes(),
        "validation_warnings": warnings,
        "validation_stats": stats,
        "workspace_scan": scan,
    }
    (output_dir / "ART_APPLY_RESULT.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 batch art workspace")
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init")
    init.add_argument("pack", type=Path)
    init.add_argument("workspace", type=Path)
    init.add_argument("--queue", type=Path)
    init.add_argument("--overwrite", action="store_true")

    scan = commands.add_parser("scan")
    scan.add_argument("workspace", type=Path)

    apply = commands.add_parser("apply")
    apply.add_argument("pack", type=Path)
    apply.add_argument("workspace", type=Path)
    apply.add_argument("output", type=Path)
    apply.add_argument("--overwrite", action="store_true")

    args = parser.parse_args()
    if args.command == "init":
        result = init_workspace(args.pack, args.workspace, args.queue, args.overwrite)
    elif args.command == "scan":
        result = scan_workspace(args.workspace)
    else:
        result = apply_workspace(args.pack, args.workspace, args.output, args.overwrite)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
