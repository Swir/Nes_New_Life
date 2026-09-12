from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter

from art_workspace import scan_workspace

GROUP_STYLE = {
    "PLAYER": "cartoon",
    "ENEMY": "cartoon",
    "BOSS": "dramatic",
    "WORLD": "painterly",
    "UI": "crisp",
    "EFFECTS": "vivid",
    "UNASSIGNED": "balanced",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _transform(image: Image.Image, style: str) -> Image.Image:
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    rgb = rgba.convert("RGB")

    if style == "balanced":
        rgb = ImageEnhance.Color(rgb).enhance(1.14)
        rgb = ImageEnhance.Contrast(rgb).enhance(1.08)
        rgb = ImageEnhance.Brightness(rgb).enhance(1.02)
        rgb = rgb.filter(ImageFilter.UnsharpMask(radius=0.9, percent=120, threshold=1))
    elif style == "cartoon":
        rgb = rgb.filter(ImageFilter.SMOOTH)
        rgb = ImageEnhance.Color(rgb).enhance(1.24)
        rgb = ImageEnhance.Contrast(rgb).enhance(1.10)
        rgb = ImageEnhance.Brightness(rgb).enhance(1.02)
        rgb = rgb.filter(ImageFilter.UnsharpMask(radius=1.1, percent=145, threshold=1))
    elif style == "dramatic":
        rgb = ImageEnhance.Color(rgb).enhance(1.28)
        rgb = ImageEnhance.Contrast(rgb).enhance(1.16)
        rgb = ImageEnhance.Brightness(rgb).enhance(1.01)
        rgb = rgb.filter(ImageFilter.UnsharpMask(radius=1.2, percent=155, threshold=1))
    elif style == "painterly":
        rgb = rgb.filter(ImageFilter.SMOOTH_MORE)
        rgb = ImageEnhance.Color(rgb).enhance(1.16)
        rgb = ImageEnhance.Contrast(rgb).enhance(1.07)
        rgb = ImageEnhance.Brightness(rgb).enhance(1.02)
        rgb = rgb.filter(ImageFilter.UnsharpMask(radius=1.3, percent=125, threshold=1))
    elif style == "crisp":
        rgb = ImageEnhance.Contrast(rgb).enhance(1.12)
        rgb = ImageEnhance.Color(rgb).enhance(1.08)
        rgb = ImageEnhance.Brightness(rgb).enhance(1.02)
        rgb = rgb.filter(ImageFilter.UnsharpMask(radius=0.8, percent=165, threshold=1))
    elif style == "vivid":
        rgb = ImageEnhance.Color(rgb).enhance(1.34)
        rgb = ImageEnhance.Contrast(rgb).enhance(1.12)
        rgb = ImageEnhance.Brightness(rgb).enhance(1.04)
        rgb = rgb.filter(ImageFilter.UnsharpMask(radius=1.0, percent=150, threshold=1))
    else:
        raise ValueError(f"Unknown auto-art style: {style}")

    output = rgb.convert("RGBA")
    output.putalpha(alpha)
    return output


def seed_baseline_art(
    workspace: Path,
    profile: str = "group-aware",
    force: bool = False,
) -> dict:
    """Seed untouched master PNGs with a safe automatic baseline art pass.

    Manually edited masters are preserved by default. Dimensions and alpha are retained.
    The result is intentionally a baseline, not a claim of final hand-drawn artwork.
    """
    manifest_path = workspace / "MASTER_TILES.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Missing master manifest: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    original_dir = workspace / "original"
    editable_dir = workspace / "editable"
    editable_dir.mkdir(parents=True, exist_ok=True)

    seeded = 0
    preserved_manual = 0
    skipped_missing = 0
    changed_by_group: dict[str, int] = {}
    records: list[dict] = []

    for master in manifest.get("masters", []):
        name = master["file"]
        group = (master.get("group") or "UNASSIGNED").upper()
        original = original_dir / name
        editable = editable_dir / name
        if not original.is_file() or not editable.is_file():
            skipped_missing += 1
            records.append({"file": name, "group": group, "result": "missing"})
            continue

        original_sha = _sha256(original)
        editable_sha = _sha256(editable)
        if not force and original_sha != editable_sha:
            preserved_manual += 1
            records.append({"file": name, "group": group, "result": "preserved-existing-edit"})
            continue

        style = GROUP_STYLE.get(group, "balanced") if profile == "group-aware" else profile
        with Image.open(original) as source:
            before_size = source.size
            before_alpha = source.convert("RGBA").getchannel("A").tobytes()
            transformed = _transform(source, style)

        if transformed.size != before_size:
            raise ValueError(f"Auto art changed dimensions for {name}: {before_size} -> {transformed.size}")
        if transformed.getchannel("A").tobytes() != before_alpha:
            raise ValueError(f"Auto art changed alpha/transparency for {name}")

        transformed.save(editable, optimize=True)
        seeded += 1
        changed_by_group[group] = changed_by_group.get(group, 0) + 1
        records.append({
            "file": name,
            "group": group,
            "style": style,
            "result": "seeded",
            "original_sha256": original_sha,
            "editable_sha256": _sha256(editable),
        })

    scan = scan_workspace(workspace)
    result = {
        "profile": profile,
        "force": force,
        "masters": len(manifest.get("masters", [])),
        "seeded": seeded,
        "preserved_existing_edits": preserved_manual,
        "skipped_missing": skipped_missing,
        "changed_by_group": dict(sorted(changed_by_group.items())),
        "workspace_scan": scan,
        "important": (
            "AUTO_BASELINE is a fast coherent starting pass. It does not replace manual final art review. "
            "Existing manual edits are preserved unless --force is used."
        ),
        "records": records,
    }
    (workspace / "AUTO_BASELINE.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 automatic baseline master-art pass")
    parser.add_argument("workspace", type=Path)
    parser.add_argument(
        "--profile",
        choices=["group-aware", "balanced", "cartoon", "dramatic", "painterly", "crisp", "vivid"],
        default="group-aware",
    )
    parser.add_argument("--force", action="store_true", help="Also replace already-edited masters")
    args = parser.parse_args()
    print(json.dumps(seed_baseline_art(args.workspace, args.profile, args.force), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
