from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter

IMG_RE = re.compile(r"^<img>(.+?)\s*$", re.I)
SCALE_RE = re.compile(r"^<scale>(\d+)\s*$", re.I)
VER_RE = re.compile(r"^<ver>(\d+)\s*$", re.I)
TILE_RE = re.compile(r"^(?:\[([^\]]+)\])?<tile>(.*)$", re.I)
COND_RE = re.compile(r"^<condition>(.*)$", re.I)


@dataclass(frozen=True)
class TileRule:
    condition: str | None
    image_index: str
    tile_id: str
    palette: str
    x: int | None
    y: int | None

    @property
    def key(self) -> str:
        return f"{self.tile_id}:{self.palette}:{self.condition or '-'}"


@dataclass
class PackStats:
    version: int | None
    scale: int
    images: list[str]
    tile_rules: int
    conditional_tile_rules: int
    conditions: int
    unique_tile_ids: int
    unique_palettes: int
    missing_images: list[str]


def _clean_lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines()]


def parse_tile_rules(pack_dir: Path) -> list[TileRule]:
    hires = pack_dir / "hires.txt"
    if not hires.is_file():
        raise FileNotFoundError(f"Missing hires.txt: {hires}")

    rules: list[TileRule] = []
    for line in _clean_lines(hires):
        if not line or line.startswith("#"):
            continue
        match = TILE_RE.match(line)
        if not match:
            continue
        parts = [part.strip() for part in match.group(2).split(",")]
        if len(parts) < 3:
            continue
        x = int(parts[3]) if len(parts) > 4 and parts[3].lstrip("-").isdigit() else None
        y = int(parts[4]) if len(parts) > 4 and parts[4].lstrip("-").isdigit() else None
        rules.append(
            TileRule(
                condition=match.group(1) or None,
                image_index=parts[0],
                tile_id=parts[1].upper(),
                palette=parts[2].upper(),
                x=x,
                y=y,
            )
        )
    return rules


def analyze(pack_dir: Path) -> PackStats:
    hires = pack_dir / "hires.txt"
    if not hires.is_file():
        raise FileNotFoundError(f"Missing hires.txt: {hires}")

    version = None
    scale = 1
    images: list[str] = []
    conditions = 0

    for line in _clean_lines(hires):
        if not line or line.startswith("#"):
            continue
        match = VER_RE.match(line)
        if match:
            version = int(match.group(1))
            continue
        match = SCALE_RE.match(line)
        if match:
            scale = max(1, int(match.group(1)))
            continue
        match = IMG_RE.match(line)
        if match:
            images.append(match.group(1).strip())
            continue
        if COND_RE.match(line):
            conditions += 1

    rules = parse_tile_rules(pack_dir)
    missing = [name for name in images if not (pack_dir / name).is_file()]
    return PackStats(
        version=version,
        scale=scale,
        images=images,
        tile_rules=len(rules),
        conditional_tile_rules=sum(1 for rule in rules if rule.condition),
        conditions=conditions,
        unique_tile_ids=len({rule.tile_id for rule in rules}),
        unique_palettes=len({rule.palette for rule in rules}),
        missing_images=missing,
    )


def capture_snapshot(pack_dir: Path) -> dict:
    stats = analyze(pack_dir)
    rules = parse_tile_rules(pack_dir)
    return {
        "stats": asdict(stats),
        "rule_keys": sorted({rule.key for rule in rules}),
        "tile_ids": sorted({rule.tile_id for rule in rules}),
        "palettes": sorted({rule.palette for rule in rules}),
        "conditional_contexts": sorted({rule.condition for rule in rules if rule.condition}),
    }


def compare_captures(baseline: Path, current: Path) -> dict:
    old = capture_snapshot(baseline)
    new = capture_snapshot(current)
    old_rules = set(old["rule_keys"])
    new_rules = set(new["rule_keys"])
    old_tiles = set(old["tile_ids"])
    new_tiles = set(new["tile_ids"])
    old_palettes = set(old["palettes"])
    new_palettes = set(new["palettes"])

    added_rules = sorted(new_rules - old_rules)
    removed_rules = sorted(old_rules - new_rules)
    baseline_count = max(1, len(old_rules))
    growth_percent = round((len(new_rules) - len(old_rules)) * 100.0 / baseline_count, 2)

    return {
        "baseline": str(baseline.resolve()),
        "current": str(current.resolve()),
        "baseline_rule_count": len(old_rules),
        "current_rule_count": len(new_rules),
        "rule_growth_percent": growth_percent,
        "added_rule_count": len(added_rules),
        "removed_rule_count": len(removed_rules),
        "new_tile_ids": sorted(new_tiles - old_tiles),
        "new_palettes": sorted(new_palettes - old_palettes),
        "added_rules": added_rules,
        "removed_rules": removed_rules,
        "capture_progressed": len(added_rules) > 0,
    }


def write_art_queue(pack_dir: Path, output: Path | None = None) -> Path:
    output = output or (pack_dir / "NES_NEW_LIFE_ART_QUEUE.csv")
    rules = parse_tile_rules(pack_dir)
    grouped: dict[tuple[str, str], dict] = {}

    for rule in rules:
        key = (rule.tile_id, rule.palette)
        item = grouped.setdefault(
            key,
            {
                "tile_id": rule.tile_id,
                "palette": rule.palette,
                "uses": 0,
                "conditional_uses": 0,
                "conditions": set(),
            },
        )
        item["uses"] += 1
        if rule.condition:
            item["conditional_uses"] += 1
            item["conditions"].add(rule.condition)

    ranked = sorted(
        grouped.values(),
        key=lambda item: (-item["uses"], -item["conditional_uses"], item["tile_id"], item["palette"]),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["priority", "tile_id", "palette", "uses", "conditional_uses", "conditions", "status", "art_group", "notes"])
        for index, item in enumerate(ranked, 1):
            writer.writerow(
                [
                    index,
                    item["tile_id"],
                    item["palette"],
                    item["uses"],
                    item["conditional_uses"],
                    " | ".join(sorted(item["conditions"])),
                    "TODO",
                    "UNASSIGNED",
                    "",
                ]
            )
    return output


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _process_image(source: Path, target: Path, style: str) -> dict:
    with Image.open(source) as image:
        rgba = image.convert("RGBA")
        alpha = rgba.getchannel("A")
        rgb = rgba.convert("RGB")

        if style == "clean":
            rgb = ImageEnhance.Contrast(rgb).enhance(1.08)
            rgb = ImageEnhance.Color(rgb).enhance(1.10)
            rgb = rgb.filter(ImageFilter.UnsharpMask(radius=1.0, percent=120, threshold=2))
        elif style == "vibrant":
            rgb = ImageEnhance.Color(rgb).enhance(1.28)
            rgb = ImageEnhance.Contrast(rgb).enhance(1.12)
            rgb = ImageEnhance.Brightness(rgb).enhance(1.03)
            rgb = rgb.filter(ImageFilter.UnsharpMask(radius=1.1, percent=135, threshold=2))
        elif style == "smooth":
            rgb = rgb.filter(ImageFilter.SMOOTH_MORE)
            rgb = ImageEnhance.Color(rgb).enhance(1.16)
            rgb = ImageEnhance.Contrast(rgb).enhance(1.08)
            rgb = rgb.filter(ImageFilter.UnsharpMask(radius=1.35, percent=145, threshold=1))
        elif style == "illustrated":
            rgb = rgb.filter(ImageFilter.SMOOTH_MORE)
            rgb = ImageEnhance.Color(rgb).enhance(1.22)
            rgb = ImageEnhance.Contrast(rgb).enhance(1.10)
            rgb = rgb.filter(ImageFilter.UnsharpMask(radius=1.5, percent=160, threshold=1))
        else:
            raise ValueError(f"Unknown style: {style}")

        output = rgb.convert("RGBA")
        output.putalpha(alpha)
        target.parent.mkdir(parents=True, exist_ok=True)
        output.save(target, optimize=True)
        return {
            "width": output.width,
            "height": output.height,
            "source_sha256": _sha256(source),
            "output_sha256": _sha256(target),
        }


def build_preview(source: Path, output: Path, style: str = "vibrant", overwrite: bool = False) -> dict:
    source = source.resolve()
    output = output.resolve()
    if source == output:
        raise ValueError("Output must be different from source pack")

    stats = analyze(source)
    if stats.missing_images:
        raise ValueError("Missing referenced PNG files: " + ", ".join(stats.missing_images))

    if output.exists():
        if not overwrite:
            raise FileExistsError(f"Output exists: {output}")
        shutil.rmtree(output)
    output.mkdir(parents=True)

    referenced = set(stats.images)
    for item in source.iterdir():
        if item.name in referenced:
            continue
        target = output / item.name
        if item.is_file():
            shutil.copy2(item, target)
        elif item.is_dir():
            shutil.copytree(item, target)

    processed = {name: _process_image(source / name, output / name, style) for name in stats.images}
    manifest = {
        "generator": "NES New Life Project #002 Instant HD Preview",
        "style": style,
        "mapping_preserved": True,
        "source_pack": str(source),
        "stats": asdict(stats),
        "images": processed,
    }
    (output / "NES_NEW_LIFE_PREVIEW.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def write_report(pack_dir: Path, output: Path | None = None) -> Path:
    stats = analyze(pack_dir)
    output = output or (pack_dir / "NES_NEW_LIFE_REPORT.html")
    rows = "".join(f"<li><code>{name}</code></li>" for name in stats.images)
    missing = "<br>".join(stats.missing_images) or "None"
    html = f"""<!doctype html><meta charset='utf-8'><title>NES New Life HD Pack Report</title>
<style>body{{font:16px system-ui;max-width:900px;margin:40px auto;padding:0 20px;background:#101318;color:#eef}}code{{color:#7ee7ff}}.card{{background:#191e27;padding:18px;border-radius:14px;margin:14px 0}}</style>
<h1>NES New Life — HD Pack Report</h1>
<div class='card'><b>Format:</b> {stats.version or 'unknown'} &nbsp; <b>Scale:</b> {stats.scale}×<br>
<b>Images:</b> {len(stats.images)} &nbsp; <b>Tile rules:</b> {stats.tile_rules} &nbsp; <b>Conditional:</b> {stats.conditional_tile_rules}<br>
<b>Unique tile IDs:</b> {stats.unique_tile_ids} &nbsp; <b>Unique palettes:</b> {stats.unique_palettes} &nbsp; <b>Conditions:</b> {stats.conditions}<br><b>Missing files:</b> {missing}</div>
<h2>Referenced sheets</h2><ul>{rows}</ul>"""
    output.write_text(html, encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze and non-destructively modernize a local Mesen HD Pack")
    commands = parser.add_subparsers(dest="command", required=True)

    analyze_cmd = commands.add_parser("analyze")
    analyze_cmd.add_argument("pack", type=Path)
    analyze_cmd.add_argument("--json", action="store_true")

    preview_cmd = commands.add_parser("preview")
    preview_cmd.add_argument("pack", type=Path)
    preview_cmd.add_argument("output", type=Path)
    preview_cmd.add_argument("--style", choices=["clean", "vibrant", "smooth", "illustrated"], default="vibrant")
    preview_cmd.add_argument("--overwrite", action="store_true")

    report_cmd = commands.add_parser("report")
    report_cmd.add_argument("pack", type=Path)
    report_cmd.add_argument("--output", type=Path)

    queue_cmd = commands.add_parser("art-queue")
    queue_cmd.add_argument("pack", type=Path)
    queue_cmd.add_argument("--output", type=Path)

    compare_cmd = commands.add_parser("compare")
    compare_cmd.add_argument("baseline", type=Path)
    compare_cmd.add_argument("current", type=Path)
    compare_cmd.add_argument("--output", type=Path)

    args = parser.parse_args()
    if args.command == "analyze":
        stats = analyze(args.pack)
        print(json.dumps(asdict(stats), indent=2) if args.json else stats)
        return 0
    if args.command == "preview":
        print(json.dumps(build_preview(args.pack, args.output, args.style, args.overwrite), indent=2))
        return 0
    if args.command == "report":
        print(write_report(args.pack, args.output))
        return 0
    if args.command == "art-queue":
        print(write_art_queue(args.pack, args.output))
        return 0

    result = compare_captures(args.baseline, args.current)
    if args.output:
        args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(args.output)
    else:
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
