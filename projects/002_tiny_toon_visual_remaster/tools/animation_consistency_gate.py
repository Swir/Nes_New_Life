from __future__ import annotations

import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter

from animation_workbench import semantic_family

CHARACTER_GROUPS = {"PLAYER", "ENEMY", "BOSS"}
MIN_FAMILY_SIZE = 2


def _metrics(path: Path) -> dict:
    with Image.open(path) as image:
        rgba = image.convert("RGBA")
    width, height = rgba.size
    alpha = rgba.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        return {
            "width": width,
            "height": height,
            "visible": 0,
            "coverage": 0.0,
            "bbox_w": 0.0,
            "bbox_h": 0.0,
            "center_x": 0.5,
            "center_y": 0.5,
            "colors": 0,
            "detail": 0.0,
        }
    pixels = list(rgba.getdata())
    visible_pixels = [pixel for pixel in pixels if pixel[3] > 0]
    visible = len(visible_pixels)
    left, top, right, bottom = bbox
    bbox_w = (right - left) / max(1, width)
    bbox_h = (bottom - top) / max(1, height)
    center_x = ((left + right) / 2.0) / max(1, width)
    center_y = ((top + bottom) / 2.0) / max(1, height)
    colors = len({pixel[:3] for pixel in visible_pixels})
    gray = rgba.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    detail = sum(edges.getdata()) / max(1, width * height * 255.0)
    return {
        "width": width,
        "height": height,
        "visible": visible,
        "coverage": visible / max(1, width * height),
        "bbox_w": bbox_w,
        "bbox_h": bbox_h,
        "center_x": center_x,
        "center_y": center_y,
        "colors": colors,
        "detail": detail,
    }


def _ratio(value: float, baseline: float) -> float:
    if baseline <= 1e-9:
        return math.inf if value > 0 else 1.0
    return value / baseline


def _median(rows: list[dict], key: str) -> float:
    return float(statistics.median(float(row[key]) for row in rows))


def _families(manifest: dict) -> dict[str, list[str]]:
    grouped: dict[str, set[str]] = {}
    for master in manifest.get("masters", []):
        group = str(master.get("group", "UNASSIGNED")).upper()
        if group not in CHARACTER_GROUPS:
            continue
        name = master.get("file")
        if not name:
            continue
        names = set()
        for target in master.get("targets", []):
            condition = str(target.get("condition", "") or "")
            if condition:
                names.add(semantic_family(condition))
        for family in names:
            if family and family != "UNCONDITIONED":
                grouped.setdefault(family, set()).add(name)
    return {family: sorted(files) for family, files in grouped.items() if len(files) >= MIN_FAMILY_SIZE}


def _palette_siblings(manifest: dict) -> dict[str, list[str]]:
    by_tile: dict[str, set[str]] = {}
    for master in manifest.get("masters", []):
        group = str(master.get("group", "UNASSIGNED")).upper()
        tile_id = str(master.get("tile_id", "") or "").upper()
        name = master.get("file")
        if group in CHARACTER_GROUPS and tile_id and name:
            by_tile.setdefault(tile_id, set()).add(name)
    return {tile_id: sorted(files) for tile_id, files in by_tile.items() if len(files) >= 2}


def _mask_iou(path_a: Path, path_b: Path) -> float:
    with Image.open(path_a) as left_img, Image.open(path_b) as right_img:
        left = left_img.convert("RGBA").getchannel("A").point(lambda p: 255 if p > 0 else 0)
        right = right_img.convert("RGBA").getchannel("A").point(lambda p: 255 if p > 0 else 0)
    if left.size != right.size:
        return 0.0
    intersection = ImageChops.multiply(left, right)
    union = ImageChops.lighter(left, right)
    inter_count = sum(1 for value in intersection.getdata() if value > 0)
    union_count = sum(1 for value in union.getdata() if value > 0)
    return inter_count / union_count if union_count else 1.0


def audit_animation_consistency(workspace: Path, changed_items: list[dict], report_path: Path | None = None) -> dict:
    """Fail closed on catastrophic family/palette inconsistencies in edited character masters.

    This is deliberately a coarse geometry gate, not an aesthetic scorer. It catches a
    frame suddenly becoming much smaller/larger, jumping far across its canvas, or a
    palette sibling losing the shared silhouette. The report is metadata-only.
    """
    workspace = Path(workspace)
    manifest_path = workspace / "MASTER_TILES.json"
    if not manifest_path.is_file():
        raise ValueError("MasterWorkspace is missing MASTER_TILES.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    masters = {item.get("file"): item for item in manifest.get("masters", []) if item.get("file")}
    changed_names = {str(item.get("master_file", "")) for item in changed_items if item.get("master_file")}
    metrics: dict[str, dict] = {}
    blockers: list[dict] = []
    warnings: list[dict] = []
    checked_families = 0
    checked_palette_sets = 0

    def get_metrics(name: str) -> dict:
        if name not in metrics:
            path = workspace / "editable" / name
            if not path.is_file():
                raise ValueError(f"Missing staged animation master: {name}")
            metrics[name] = _metrics(path)
        return metrics[name]

    for family, names in _families(manifest).items():
        changed = [name for name in names if name in changed_names]
        if not changed:
            continue
        checked_families += 1
        peer_names = [name for name in names if name not in changed_names]
        # If the entire family is being redrawn in the same transaction, compare each frame
        # against the family median rather than pretending an old peer is authoritative.
        baseline_names = peer_names if peer_names else names
        baseline = [get_metrics(name) for name in baseline_names]
        median = {key: _median(baseline, key) for key in ("coverage", "bbox_w", "bbox_h", "center_x", "center_y", "colors", "detail")}
        for name in changed:
            row = get_metrics(name)
            issues = []
            if row["visible"] == 0:
                issues.append("FRAME_FULLY_TRANSPARENT")
            width_ratio = _ratio(row["bbox_w"], median["bbox_w"])
            height_ratio = _ratio(row["bbox_h"], median["bbox_h"])
            coverage_ratio = _ratio(row["coverage"], median["coverage"])
            center_delta = math.hypot(row["center_x"] - median["center_x"], row["center_y"] - median["center_y"])
            if width_ratio < 0.45 or width_ratio > 2.20:
                issues.append("FAMILY_BBOX_WIDTH_OUTLIER")
            if height_ratio < 0.45 or height_ratio > 2.20:
                issues.append("FAMILY_BBOX_HEIGHT_OUTLIER")
            if coverage_ratio < 0.30 or coverage_ratio > 3.20:
                issues.append("FAMILY_ALPHA_COVERAGE_OUTLIER")
            if center_delta > 0.34:
                issues.append("FAMILY_CANVAS_CENTER_JUMP")
            detail_ratio = _ratio(row["detail"], median["detail"])
            color_ratio = _ratio(float(row["colors"]), max(1.0, median["colors"]))
            if detail_ratio < 0.22 or detail_ratio > 4.5:
                warnings.append({"family": family, "master_file": name, "code": "FAMILY_DETAIL_DENSITY_OUTLIER", "ratio": round(detail_ratio, 4)})
            if color_ratio < 0.22 or color_ratio > 4.5:
                warnings.append({"family": family, "master_file": name, "code": "FAMILY_COLOR_COUNT_OUTLIER", "ratio": round(color_ratio, 4)})
            for code in issues:
                blockers.append({
                    "family": family,
                    "master_file": name,
                    "code": code,
                    "bbox_width_ratio": round(width_ratio, 4),
                    "bbox_height_ratio": round(height_ratio, 4),
                    "coverage_ratio": round(coverage_ratio, 4),
                    "center_delta": round(center_delta, 4),
                })

    for tile_id, names in _palette_siblings(manifest).items():
        changed = [name for name in names if name in changed_names]
        peers = [name for name in names if name not in changed_names]
        if not changed or not peers:
            continue
        checked_palette_sets += 1
        for name in changed:
            best_iou = max(_mask_iou(workspace / "editable" / name, workspace / "editable" / peer) for peer in peers)
            if best_iou < 0.32:
                blockers.append({
                    "tile_id": tile_id,
                    "master_file": name,
                    "code": "PALETTE_VARIANT_SILHOUETTE_MISMATCH",
                    "best_alpha_mask_iou": round(best_iou, 4),
                })

    result = {
        "schema": "swir.project002.animation-consistency-gate.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "qa_gate": "PASS" if not blockers else "FAIL",
        "changed_character_masters": sum(1 for name in changed_names if str(masters.get(name, {}).get("group", "")).upper() in CHARACTER_GROUPS),
        "checked_animation_families": checked_families,
        "checked_palette_variant_sets": checked_palette_sets,
        "blocker_count": len(blockers),
        "warning_count": len(warnings),
        "blockers": blockers,
        "warnings": warnings,
        "policy": "Geometry/silhouette consistency only. This gate never edits ROADMAP, mappings or image pixels.",
    }
    if report_path is not None:
        Path(report_path).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
