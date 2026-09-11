from __future__ import annotations

import argparse
import re
from pathlib import Path

TAG_RE = re.compile(r"<(\w+)>(.*)$")


def validate(folder: Path) -> tuple[list[str], list[str], dict[str, int]]:
    errors: list[str] = []
    warnings: list[str] = []
    stats = {"images": 0, "tiles": 0, "conditions": 0}
    hires = folder / "hires.txt"
    if not hires.is_file():
        return [f"Missing {hires}"], warnings, stats

    images: list[Path] = []
    image_sizes: list[tuple[int, int] | None] = []
    version = scale = None
    seen_rules: set[str] = set()
    try:
        from PIL import Image
    except ImportError:
        Image = None
        warnings.append("Pillow not installed; PNG dimensions will not be checked.")

    for line_no, raw in enumerate(hires.read_text(encoding="utf-8-sig").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("["):
            close = line.find("]")
            if close > 0:
                stats["conditions"] += 1
                line = line[close + 1:].strip()
        m = TAG_RE.search(line)
        if not m:
            warnings.append(f"Line {line_no}: unrecognized syntax")
            continue
        tag, payload = m.group(1).lower(), m.group(2).strip()
        if tag == "ver":
            try: version = int(payload)
            except ValueError: errors.append(f"Line {line_no}: invalid <ver> value")
        elif tag == "scale":
            try:
                scale = int(payload)
                if scale < 1 or scale > 10: warnings.append(f"Line {line_no}: unusual HD scale {scale}")
            except ValueError: errors.append(f"Line {line_no}: invalid <scale> value")
        elif tag == "img":
            img = folder / payload
            images.append(img)
            stats["images"] += 1
            if not img.is_file():
                errors.append(f"Line {line_no}: missing image {payload}")
                image_sizes.append(None)
            elif Image:
                try:
                    with Image.open(img) as im: image_sizes.append(im.size)
                except Exception as exc:
                    errors.append(f"Line {line_no}: cannot read {payload}: {exc}")
                    image_sizes.append(None)
            else:
                image_sizes.append(None)
        elif tag == "tile":
            stats["tiles"] += 1
            parts = [p.strip() for p in payload.split(",")]
            if len(parts) < 5:
                errors.append(f"Line {line_no}: <tile> requires at least 5 fields")
                continue
            try: img_index, x, y = int(parts[0]), int(parts[3]), int(parts[4])
            except ValueError:
                errors.append(f"Line {line_no}: invalid image index/x/y in <tile>")
                continue
            if img_index < 0 or img_index >= len(images):
                errors.append(f"Line {line_no}: image index {img_index} does not exist yet")
            elif image_sizes[img_index] is not None:
                w, h = image_sizes[img_index]
                if x < 0 or y < 0 or x >= w or y >= h:
                    errors.append(f"Line {line_no}: tile coordinate ({x},{y}) is outside image {img_index} ({w}x{h})")
            if payload in seen_rules: warnings.append(f"Line {line_no}: exact duplicate tile rule")
            seen_rules.add(payload)

    if version is None: errors.append("Missing <ver> tag")
    elif version < 100: warnings.append(f"Old HD pack format version: {version}")
    if scale is None: errors.append("Missing <scale> tag")
    if stats["images"] == 0: warnings.append("No <img> entries found yet")
    if stats["tiles"] == 0: warnings.append("No <tile> mappings found yet; run Mesen HD Pack Builder capture first")
    return errors, warnings, stats


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Mesen NES HD Pack folder.")
    parser.add_argument("folder", type=Path, help="Folder containing hires.txt and PNG sheets")
    args = parser.parse_args()
    errors, warnings, stats = validate(args.folder.resolve())
    print(f"Images: {stats['images']} | Tile rules: {stats['tiles']} | Conditional rules: {stats['conditions']}")
    for item in warnings: print(f"WARNING: {item}")
    for item in errors: print(f"ERROR: {item}")
    if errors: return 2
    print("HD pack validation: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
