from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

SCHEMA = "swir.project002.visual-quality-gate.v1"


def _ratio(value: float, baseline: float, *, fallback: float = 1.0) -> float:
    return value / baseline if baseline else fallback


def _bbox_metrics(alpha: Image.Image) -> tuple[tuple[int, int, int, int] | None, int, int, int]:
    bbox = alpha.getbbox()
    if bbox is None:
        return None, 0, 0, 0
    left, top, right, bottom = bbox
    width = max(0, right - left)
    height = max(0, bottom - top)
    return bbox, width, height, width * height


def _detail_energy(image: Image.Image) -> float:
    rgba = image.convert("RGBA")
    gray = rgba.convert("L")
    alpha = rgba.getchannel("A")
    width, height = rgba.size
    if width < 2 or height < 2:
        return 0.0
    gp = gray.load()
    ap = alpha.load()
    total = 0.0
    samples = 0
    for y in range(height):
        for x in range(width):
            if ap[x, y] == 0:
                continue
            if x + 1 < width and ap[x + 1, y] != 0:
                total += abs(int(gp[x, y]) - int(gp[x + 1, y]))
                samples += 1
            if y + 1 < height and ap[x, y + 1] != 0:
                total += abs(int(gp[x, y]) - int(gp[x, y + 1]))
                samples += 1
    return round(total / samples, 4) if samples else 0.0


def _metrics(path: Path) -> dict:
    with Image.open(path) as raw:
        image = raw.convert("RGBA")
    width, height = image.size
    alpha = image.getchannel("A")
    alpha_values = list(alpha.getdata())
    nontransparent = sum(1 for value in alpha_values if value > 0)
    total_pixels = width * height
    bbox, bbox_width, bbox_height, bbox_area = _bbox_metrics(alpha)
    pixels = image.getdata()
    unique_rgb = {
        (r, g, b)
        for r, g, b, a in pixels
        if a > 0
    }
    return {
        "width": width,
        "height": height,
        "total_pixels": total_pixels,
        "nontransparent_pixels": nontransparent,
        "alpha_coverage": round(nontransparent / total_pixels, 6) if total_pixels else 0.0,
        "bbox": list(bbox) if bbox else None,
        "bbox_width": bbox_width,
        "bbox_height": bbox_height,
        "bbox_area": bbox_area,
        "unique_rgb_colors": len(unique_rgb),
        "detail_energy": _detail_energy(image),
    }


def _changed_pixel_ratio(original: Path, edited: Path) -> float:
    with Image.open(original) as a_raw, Image.open(edited) as b_raw:
        a = a_raw.convert("RGBA")
        b = b_raw.convert("RGBA")
    if a.size != b.size:
        return 1.0
    changed = sum(1 for left, right in zip(a.getdata(), b.getdata()) if left != right)
    total = a.width * a.height
    return round(changed / total, 6) if total else 0.0


def audit_master_pair(original: Path, edited: Path, master_file: str | None = None) -> dict:
    original = Path(original)
    edited = Path(edited)
    name = master_file or edited.name
    blockers: list[str] = []
    warnings: list[str] = []

    if not original.is_file():
        blockers.append("MISSING_ORIGINAL")
        return {"master_file": name, "gate": "FAIL", "blockers": blockers, "warnings": warnings}
    if not edited.is_file():
        blockers.append("MISSING_EDITED")
        return {"master_file": name, "gate": "FAIL", "blockers": blockers, "warnings": warnings}

    try:
        base = _metrics(original)
        candidate = _metrics(edited)
    except Exception as exc:
        blockers.append("INVALID_PNG")
        return {
            "master_file": name,
            "gate": "FAIL",
            "blockers": blockers,
            "warnings": warnings,
            "error": type(exc).__name__,
        }

    if (base["width"], base["height"]) != (candidate["width"], candidate["height"]):
        blockers.append("DIMENSION_CHANGE")

    coverage_ratio = _ratio(candidate["alpha_coverage"], base["alpha_coverage"])
    bbox_width_ratio = _ratio(float(candidate["bbox_width"]), float(base["bbox_width"]))
    bbox_height_ratio = _ratio(float(candidate["bbox_height"]), float(base["bbox_height"]))
    color_ratio = _ratio(float(candidate["unique_rgb_colors"]), float(base["unique_rgb_colors"]))
    detail_ratio = _ratio(float(candidate["detail_energy"]), float(base["detail_energy"]))
    changed_ratio = _changed_pixel_ratio(original, edited) if "DIMENSION_CHANGE" not in blockers else 1.0

    if base["nontransparent_pixels"] > 0 and candidate["nontransparent_pixels"] == 0:
        blockers.append("FULLY_TRANSPARENT")
    if base["alpha_coverage"] >= 0.02 and coverage_ratio < 0.25:
        blockers.append("ALPHA_COVERAGE_COLLAPSE")
    if base["bbox_width"] >= 4 and bbox_width_ratio < 0.25:
        blockers.append("BBOX_WIDTH_COLLAPSE")
    if base["bbox_height"] >= 4 and bbox_height_ratio < 0.25:
        blockers.append("BBOX_HEIGHT_COLLAPSE")
    if base["unique_rgb_colors"] >= 4 and candidate["unique_rgb_colors"] <= 1 and candidate["nontransparent_pixels"] >= 4:
        blockers.append("COLOR_COLLAPSE")
    if base["detail_energy"] >= 3.0 and detail_ratio < 0.10 and changed_ratio >= 0.50:
        blockers.append("DETAIL_COLLAPSE")

    # Strong but non-blocking signals: legitimate redraws may intentionally expand silhouettes.
    if base["alpha_coverage"] > 0 and coverage_ratio > 2.5:
        warnings.append("ALPHA_COVERAGE_EXPANSION")
    if base["bbox_area"] > 0 and _ratio(float(candidate["bbox_area"]), float(base["bbox_area"])) > 2.5:
        warnings.append("BBOX_EXPANSION")
    if base["unique_rgb_colors"] >= 8 and color_ratio < 0.25 and "COLOR_COLLAPSE" not in blockers:
        warnings.append("STRONG_COLOR_REDUCTION")
    if base["detail_energy"] >= 3.0 and detail_ratio < 0.35 and "DETAIL_COLLAPSE" not in blockers:
        warnings.append("STRONG_DETAIL_REDUCTION")

    return {
        "master_file": name,
        "gate": "FAIL" if blockers else "PASS",
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "changed_pixel_ratio": changed_ratio,
        "ratios": {
            "alpha_coverage": round(coverage_ratio, 4),
            "bbox_width": round(bbox_width_ratio, 4),
            "bbox_height": round(bbox_height_ratio, 4),
            "unique_colors": round(color_ratio, 4),
            "detail_energy": round(detail_ratio, 4),
        },
        "original": base,
        "edited": candidate,
    }


def audit_workspace_visual_quality(workspace: Path, items: list[dict], report_path: Path | None = None) -> dict:
    workspace = Path(workspace)
    results = [
        audit_master_pair(
            workspace / "original" / item["master_file"],
            workspace / "editable" / item["master_file"],
            item["master_file"],
        )
        for item in items
    ]
    failed = [item for item in results if item["gate"] != "PASS"]
    warnings = sum(len(item.get("warnings", [])) for item in results)
    report = {
        "schema": SCHEMA,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "qa_gate": "FAIL" if failed else "PASS",
        "masters_checked": len(results),
        "masters_failed": len(failed),
        "warnings": warnings,
        "blocker_codes": sorted({code for item in failed for code in item.get("blockers", [])}),
        "results": results,
        "privacy": "Metadata metrics only; no image pixels, ROM bytes, save states, emulator binaries or absolute local paths are serialized.",
    }
    if report_path is not None:
        report_path = Path(report_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report
