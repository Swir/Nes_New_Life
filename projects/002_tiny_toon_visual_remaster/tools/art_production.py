from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

from hdpack_pipeline import parse_tile_rules

GROUP_ORDER = ("PLAYER", "ENEMY", "BOSS", "WORLD", "UI", "EFFECTS", "UNASSIGNED")


def _image_index_map(pack_dir: Path) -> dict[str, Path]:
    images: list[Path] = []
    for raw in (pack_dir / "hires.txt").read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = raw.strip()
        if line.lower().startswith("<img>"):
            images.append(pack_dir / line[5:].strip())
    return {str(index): path for index, path in enumerate(images)}


def _load_groups(queue: Path | None) -> dict[tuple[str, str], str]:
    groups: dict[tuple[str, str], str] = {}
    if queue is None or not queue.is_file():
        return groups
    with queue.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            key = ((row.get("tile_id") or "").strip().upper(), (row.get("palette") or "").strip().upper())
            if all(key):
                groups[key] = (row.get("art_group") or "UNASSIGNED").strip().upper() or "UNASSIGNED"
    return groups


def _crop_rule(pack_dir: Path, rule, scale: int) -> Image.Image | None:
    image_map = _image_index_map(pack_dir)
    source = image_map.get(rule.image_index)
    if source is None or not source.is_file() or rule.x is None or rule.y is None:
        return None
    size = 8 * max(1, scale)
    with Image.open(source) as image:
        rgba = image.convert("RGBA")
        if rule.x < 0 or rule.y < 0 or rule.x + size > rgba.width or rule.y + size > rgba.height:
            return None
        return rgba.crop((rule.x, rule.y, rule.x + size, rule.y + size))


def _alpha_hash(image: Image.Image) -> str:
    return hashlib.sha256(image.convert("RGBA").tobytes()).hexdigest()


def _phash_bits(image: Image.Image) -> int:
    gray = image.convert("L").resize((8, 8), Image.Resampling.LANCZOS)
    values = list(gray.getdata())
    mean = sum(values) / len(values)
    bits = 0
    for value in values:
        bits = (bits << 1) | int(value >= mean)
    return bits


def _hamming(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def build_tile_catalog(pack_dir: Path, queue: Path | None = None) -> list[dict]:
    groups = _load_groups(queue)
    scale = 4
    for raw in (pack_dir / "hires.txt").read_text(encoding="utf-8-sig", errors="replace").splitlines():
        if raw.strip().lower().startswith("<scale>"):
            try:
                scale = max(1, int(raw.strip()[7:]))
            except ValueError:
                pass
    catalog: list[dict] = []
    for index, rule in enumerate(parse_tile_rules(pack_dir), 1):
        crop = _crop_rule(pack_dir, rule, scale)
        if crop is None:
            continue
        catalog.append({
            "index": index,
            "tile_id": rule.tile_id,
            "palette": rule.palette,
            "condition": rule.condition or "",
            "image_index": rule.image_index,
            "x": rule.x,
            "y": rule.y,
            "group": groups.get((rule.tile_id, rule.palette), "UNASSIGNED"),
            "exact_hash": _alpha_hash(crop),
            "phash": _phash_bits(crop),
            "image": crop,
        })
    return catalog


def find_duplicate_clusters(pack_dir: Path, queue: Path | None = None, near_distance: int = 5) -> dict:
    catalog = build_tile_catalog(pack_dir, queue)
    exact: dict[str, list[dict]] = defaultdict(list)
    for item in catalog:
        exact[item["exact_hash"]].append(item)
    exact_clusters = [items for items in exact.values() if len(items) > 1]

    representatives = [items[0] for items in exact.values()]
    near_clusters: list[list[dict]] = []
    used: set[int] = set()
    for i, base in enumerate(representatives):
        if i in used:
            continue
        cluster = [base]
        for j in range(i + 1, len(representatives)):
            if j in used:
                continue
            other = representatives[j]
            if _hamming(base["phash"], other["phash"]) <= near_distance:
                cluster.append(other)
                used.add(j)
        if len(cluster) > 1:
            near_clusters.append(cluster)

    def compact(item: dict) -> dict:
        return {key: item[key] for key in ("index", "tile_id", "palette", "condition", "image_index", "x", "y", "group")}

    return {
        "tiles": len(catalog),
        "exact_cluster_count": len(exact_clusters),
        "exact_duplicate_tiles": sum(len(cluster) - 1 for cluster in exact_clusters),
        "near_cluster_count": len(near_clusters),
        "near_distance": near_distance,
        "exact_clusters": [[compact(item) for item in cluster] for cluster in exact_clusters],
        "near_clusters": [[compact(item) for item in cluster] for cluster in near_clusters],
    }


def write_workboards(pack_dir: Path, output_dir: Path, queue: Path | None = None, columns: int = 10) -> dict:
    catalog = build_tile_catalog(pack_dir, queue)
    output_dir.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in catalog:
        grouped[item["group"] if item["group"] in GROUP_ORDER else "UNASSIGNED"].append(item)

    manifest = {"groups": {}, "tile_count": len(catalog)}
    for group in GROUP_ORDER:
        items = grouped.get(group, [])
        if not items:
            continue
        thumb = 96
        label_h = 34
        rows = (len(items) + columns - 1) // columns
        board = Image.new("RGBA", (columns * thumb, rows * (thumb + label_h)), (20, 24, 30, 255))
        draw = ImageDraw.Draw(board)
        for idx, item in enumerate(items):
            col = idx % columns
            row = idx // columns
            x = col * thumb
            y = row * (thumb + label_h)
            tile = item["image"].copy()
            tile.thumbnail((80, 80), Image.Resampling.NEAREST)
            tx = x + (thumb - tile.width) // 2
            ty = y + (thumb - tile.height) // 2
            board.alpha_composite(tile, (tx, ty))
            label = f"{item['tile_id']} {item['palette'][:6]}"
            draw.text((x + 4, y + thumb + 2), label, fill=(235, 240, 245, 255), font=ImageFont.load_default())
            draw.text((x + 4, y + thumb + 16), f"#{item['index']} {item['condition'][:12]}", fill=(150, 190, 220, 255), font=ImageFont.load_default())
        path = output_dir / f"WORKBOARD_{group}.png"
        board.save(path, optimize=True)
        manifest["groups"][group] = {"tiles": len(items), "file": path.name}

    manifest_path = output_dir / "WORKBOARDS.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def export_master_tiles(pack_dir: Path, output_dir: Path, queue: Path | None = None) -> dict:
    catalog = build_tile_catalog(pack_dir, queue)
    output_dir.mkdir(parents=True, exist_ok=True)
    by_hash: dict[str, dict] = {}
    usage: dict[str, list[dict]] = defaultdict(list)
    for item in catalog:
        key = item["exact_hash"]
        by_hash.setdefault(key, item)
        usage[key].append(item)

    manifest = {"masters": []}
    for number, (key, item) in enumerate(sorted(by_hash.items()), 1):
        name = f"MASTER_{number:04d}_{item['group']}_{item['tile_id']}_{item['palette'][:8]}.png"
        item["image"].save(output_dir / name, optimize=True)
        manifest["masters"].append({
            "file": name,
            "exact_hash": key,
            "group": item["group"],
            "tile_id": item["tile_id"],
            "palette": item["palette"],
            "uses": len(usage[key]),
            "targets": [
                {k: target[k] for k in ("image_index", "x", "y", "tile_id", "palette", "condition")}
                for target in usage[key]
            ],
        })
    (output_dir / "MASTER_TILES.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def propagate_master(pack_dir: Path, master_manifest: Path, master_file: Path, replacement: Path, output_dir: Path) -> dict:
    data = json.loads(master_manifest.read_text(encoding="utf-8"))
    entry = next((item for item in data.get("masters", []) if item.get("file") == master_file.name), None)
    if entry is None:
        raise ValueError(f"Master not found in manifest: {master_file.name}")
    output_dir.mkdir(parents=True, exist_ok=True)
    image_map = _image_index_map(pack_dir)
    targets_by_image: dict[str, list[dict]] = defaultdict(list)
    for target in entry["targets"]:
        targets_by_image[target["image_index"]].append(target)

    with Image.open(replacement) as img:
        replacement_rgba = img.convert("RGBA")
    changed = 0
    for image_index, targets in targets_by_image.items():
        source = image_map.get(image_index)
        if source is None or not source.is_file():
            raise FileNotFoundError(f"Missing source sheet for image index {image_index}")
        with Image.open(source) as img:
            sheet = img.convert("RGBA")
        for target in targets:
            x, y = int(target["x"]), int(target["y"])
            size = replacement_rgba.size
            if x < 0 or y < 0 or x + size[0] > sheet.width or y + size[1] > sheet.height:
                raise ValueError(f"Replacement does not fit target at {x},{y} in {source.name}")
            sheet.alpha_composite(replacement_rgba, (x, y))
            changed += 1
        sheet.save(output_dir / source.name, optimize=True)

    for source in image_map.values():
        target = output_dir / source.name
        if source.is_file() and not target.exists():
            target.write_bytes(source.read_bytes())
    (output_dir / "hires.txt").write_bytes((pack_dir / "hires.txt").read_bytes())
    result = {"master": master_file.name, "targets_updated": changed, "mapping_preserved": True}
    (output_dir / "PROPAGATION_RESULT.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 art-production accelerator")
    commands = parser.add_subparsers(dest="command", required=True)

    dup = commands.add_parser("duplicates")
    dup.add_argument("pack", type=Path)
    dup.add_argument("--queue", type=Path)
    dup.add_argument("--near-distance", type=int, default=5)
    dup.add_argument("--output", type=Path)

    boards = commands.add_parser("workboards")
    boards.add_argument("pack", type=Path)
    boards.add_argument("output", type=Path)
    boards.add_argument("--queue", type=Path)

    masters = commands.add_parser("masters")
    masters.add_argument("pack", type=Path)
    masters.add_argument("output", type=Path)
    masters.add_argument("--queue", type=Path)

    prop = commands.add_parser("propagate")
    prop.add_argument("pack", type=Path)
    prop.add_argument("master_manifest", type=Path)
    prop.add_argument("master_file", type=Path)
    prop.add_argument("replacement", type=Path)
    prop.add_argument("output", type=Path)

    args = parser.parse_args()
    if args.command == "duplicates":
        result = find_duplicate_clusters(args.pack, args.queue, args.near_distance)
        text = json.dumps(result, indent=2)
        if args.output:
            args.output.write_text(text, encoding="utf-8")
            print(args.output)
        else:
            print(text)
        return 0
    if args.command == "workboards":
        print(json.dumps(write_workboards(args.pack, args.output, args.queue), indent=2))
        return 0
    if args.command == "masters":
        print(json.dumps(export_master_tiles(args.pack, args.output, args.queue), indent=2))
        return 0
    print(json.dumps(propagate_master(args.pack, args.master_manifest, args.master_file, args.replacement, args.output), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
