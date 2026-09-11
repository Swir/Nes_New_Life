from __future__ import annotations

import argparse
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
TILE_RE = re.compile(r"^(?:\[[^\]]+\])?<tile>(.*)$", re.I)
COND_RE = re.compile(r"^<condition>(.*)$", re.I)


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


def analyze(pack_dir: Path) -> PackStats:
    hires = pack_dir / "hires.txt"
    if not hires.is_file():
        raise FileNotFoundError(f"Missing hires.txt: {hires}")

    version = None
    scale = 1
    images: list[str] = []
    tile_rules = 0
    conditional = 0
    conditions = 0
    tile_ids: set[str] = set()
    palettes: set[str] = set()

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
            continue

        match = TILE_RE.match(line)
        if match:
            tile_rules += 1
            if line.startswith("["):
                conditional += 1
            parts = [part.strip() for part in match.group(1).split(",")]
            if len(parts) >= 3:
                tile_ids.add(parts[1].upper())
                palettes.add(parts[2].upper())

    missing = [name for name in images if not (pack_dir / name).is_file()]
    return PackStats(version, scale, images, tile_rules, conditional, conditions, len(tile_ids), len(palettes), missing)


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

    processed = {}
    for name in stats.images:
        processed[name] = _process_image(source / name, output / name, style)

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

    args = parser.parse_args()
    if args.command == "analyze":
        stats = analyze(args.pack)
        print(json.dumps(asdict(stats), indent=2) if args.json else stats)
        return 0
    if args.command == "preview":
        print(json.dumps(build_preview(args.pack, args.output, args.style, args.overwrite), indent=2))
        return 0

    print(write_report(args.pack, args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
