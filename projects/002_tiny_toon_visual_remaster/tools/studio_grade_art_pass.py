from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import shutil
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageStat

MANIFEST_NAME = "ART_SPRINT_KIT.json"
REPORT_NAME = "STUDIO_GRADE_ART_PASS.json"

# Fixed, deterministic profiles. They never resize, crop, move or alter alpha.
# The three variants let the scorer choose a useful starting point without
# pretending that generic processing is equivalent to hand-finished final art.
GROUP_BASE = {
    "PLAYER": {"color": 1.20, "contrast": 1.10, "brightness": 1.015, "clarity": 1.24, "curve": 0.12},
    "ENEMY": {"color": 1.17, "contrast": 1.09, "brightness": 1.010, "clarity": 1.20, "curve": 0.10},
    "BOSS": {"color": 1.24, "contrast": 1.15, "brightness": 1.000, "clarity": 1.28, "curve": 0.16},
    "WORLD": {"color": 1.12, "contrast": 1.07, "brightness": 1.010, "clarity": 1.14, "curve": 0.08},
    "UI": {"color": 1.06, "contrast": 1.13, "brightness": 1.010, "clarity": 1.30, "curve": 0.08},
    "EFFECTS": {"color": 1.30, "contrast": 1.12, "brightness": 1.025, "clarity": 1.22, "curve": 0.12},
    "UNASSIGNED": {"color": 1.10, "contrast": 1.06, "brightness": 1.005, "clarity": 1.12, "curve": 0.06},
}

VARIANTS = {
    "refined": {"strength": 0.78, "detail": 0.95},
    "studio": {"strength": 1.00, "detail": 1.00},
    "bold": {"strength": 1.18, "detail": 1.08},
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _clamp(value: float) -> int:
    return max(0, min(255, int(round(value))))


def _tone_lut(curve: float) -> list[int]:
    """Gentle S curve around mid-gray; endpoints stay fixed.

    A fixed LUT is intentionally used instead of per-image autocontrast so exact
    duplicate graphics receive identical treatment and palette relationships do
    not drift based on local histogram differences.
    """
    curve = max(0.0, min(0.35, float(curve)))
    lut: list[int] = []
    for value in range(256):
        x = value / 255.0
        # Smooth contrast curve with no spatial component (safe for tile seams).
        smooth = x * x * (3.0 - 2.0 * x)
        mixed = x * (1.0 - curve) + smooth * curve
        lut.append(_clamp(mixed * 255.0))
    return lut


def _apply_profile(image: Image.Image, group: str, variant: str) -> Image.Image:
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    rgb = rgba.convert("RGB")
    base = GROUP_BASE.get(group.upper(), GROUP_BASE["UNASSIGNED"])
    spec = VARIANTS[variant]
    strength = spec["strength"]

    color = 1.0 + (base["color"] - 1.0) * strength
    contrast = 1.0 + (base["contrast"] - 1.0) * strength
    brightness = 1.0 + (base["brightness"] - 1.0) * strength
    clarity = 1.0 + (base["clarity"] - 1.0) * strength * spec["detail"]
    curve = base["curve"] * strength

    # UI should never be softened. WORLD gets only a tiny median pre-pass to
    # reduce block noise; all operations remain within the same canvas.
    if group.upper() == "WORLD" and variant == "refined":
        rgb = rgb.filter(ImageFilter.MedianFilter(size=3))

    rgb = ImageEnhance.Color(rgb).enhance(color)
    rgb = ImageEnhance.Contrast(rgb).enhance(contrast)
    rgb = ImageEnhance.Brightness(rgb).enhance(brightness)
    rgb = rgb.point(_tone_lut(curve) * 3)

    # PIL UnsharpMask amount is percentage; use a modest radius to avoid halos.
    amount = max(0, int(round((clarity - 1.0) * 460.0)))
    if amount:
        radius = 0.70 if group.upper() == "UI" else 0.85
        rgb = rgb.filter(ImageFilter.UnsharpMask(radius=radius, percent=amount, threshold=2))

    output = rgb.convert("RGBA")
    output.putalpha(alpha)
    return output


def _opaque_pixels(image: Image.Image) -> list[tuple[int, int, int]]:
    rgba = image.convert("RGBA")
    return [(r, g, b) for r, g, b, a in rgba.getdata() if a > 0]


def _edge_energy(image: Image.Image) -> float:
    rgba = image.convert("RGBA")
    gray = rgba.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    stat = ImageStat.Stat(edges)
    return float(stat.mean[0])


def _metrics(image: Image.Image, original: Image.Image | None = None) -> dict:
    pixels = _opaque_pixels(image)
    if not pixels:
        return {
            "opaque_pixels": 0,
            "mean_luma": 0.0,
            "colorfulness": 0.0,
            "clipping_ratio": 0.0,
            "edge_energy": _edge_energy(image),
            "mean_rgb_delta": 0.0,
        }

    n = len(pixels)
    lumas = [(0.2126 * r + 0.7152 * g + 0.0722 * b) for r, g, b in pixels]
    mean_luma = sum(lumas) / n
    rg = [r - g for r, g, _ in pixels]
    yb = [0.5 * (r + g) - b for r, g, b in pixels]
    mean_rg = sum(rg) / n
    mean_yb = sum(yb) / n
    std_rg = math.sqrt(sum((value - mean_rg) ** 2 for value in rg) / n)
    std_yb = math.sqrt(sum((value - mean_yb) ** 2 for value in yb) / n)
    colorfulness = math.sqrt(std_rg * std_rg + std_yb * std_yb) + 0.3 * math.sqrt(mean_rg * mean_rg + mean_yb * mean_yb)
    clipped = sum(1 for r, g, b in pixels if min(r, g, b) <= 2 or max(r, g, b) >= 253)

    mean_rgb_delta = 0.0
    if original is not None:
        before = _opaque_pixels(original)
        if len(before) == n:
            total = 0.0
            for (r0, g0, b0), (r1, g1, b1) in zip(before, pixels):
                total += (abs(r1 - r0) + abs(g1 - g0) + abs(b1 - b0)) / 3.0
            mean_rgb_delta = total / n

    return {
        "opaque_pixels": n,
        "mean_luma": round(mean_luma, 4),
        "colorfulness": round(colorfulness, 4),
        "clipping_ratio": round(clipped / n, 6),
        "edge_energy": round(_edge_energy(image), 4),
        "mean_rgb_delta": round(mean_rgb_delta, 4),
    }


def _score_candidate(original_metrics: dict, candidate_metrics: dict, group: str) -> tuple[float, list[str]]:
    """Rank a useful baseline while penalizing destructive over-processing."""
    reasons: list[str] = []
    clipping = float(candidate_metrics["clipping_ratio"])
    delta = float(candidate_metrics["mean_rgb_delta"])
    edge0 = max(1.0, float(original_metrics["edge_energy"]))
    edge1 = float(candidate_metrics["edge_energy"])
    color0 = max(1.0, float(original_metrics["colorfulness"]))
    color1 = float(candidate_metrics["colorfulness"])
    luma_shift = abs(float(candidate_metrics["mean_luma"]) - float(original_metrics["mean_luma"]))

    edge_gain = max(-0.5, min(0.5, (edge1 - edge0) / edge0))
    color_gain = max(-0.5, min(0.65, (color1 - color0) / color0))

    edge_target = 0.18 if group.upper() in {"PLAYER", "ENEMY", "BOSS", "UI"} else 0.10
    color_target = 0.20 if group.upper() in {"PLAYER", "BOSS", "EFFECTS"} else 0.10
    score = 100.0
    score -= abs(edge_gain - edge_target) * 42.0
    score -= abs(color_gain - color_target) * 26.0
    score -= clipping * 180.0
    score -= max(0.0, delta - 32.0) * 0.8
    score -= max(0.0, luma_shift - 16.0) * 1.2

    if clipping <= 0.025:
        reasons.append("low-channel-clipping")
    else:
        reasons.append("clipping-penalty")
    if abs(edge_gain - edge_target) <= 0.12:
        reasons.append("edge-clarity-near-target")
    if abs(color_gain - color_target) <= 0.18:
        reasons.append("color-lift-near-target")
    if delta <= 32.0:
        reasons.append("controlled-color-drift")
    if luma_shift <= 16.0:
        reasons.append("controlled-luma-shift")
    return round(score, 4), reasons


def _load_manifest(kit_dir: Path) -> dict:
    path = Path(kit_dir) / MANIFEST_NAME
    if not path.is_file():
        raise FileNotFoundError(f"Missing sprint manifest: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data.get("items"), list):
        raise ValueError("Invalid sprint manifest: items list is missing")
    return data


def apply_studio_grade_pass(
    kit_dir: Path,
    *,
    force: bool = False,
    keep_candidates: bool = True,
) -> dict:
    """Polish unchanged High-Impact Sprint masters with deterministic, scored variants.

    Existing artist edits are protected by the sprint-export SHA unless force=True.
    All candidates preserve exact dimensions and alpha bytes. Candidate PNGs stay
    local inside the gitignored art sprint and are never report payloads.
    """
    kit_dir = Path(kit_dir)
    manifest = _load_manifest(kit_dir)
    editable_dir = kit_dir / "editable"
    reference_dir = kit_dir / "reference"
    candidates_dir = kit_dir / "quality_candidates"
    if keep_candidates:
        candidates_dir.mkdir(parents=True, exist_ok=True)
    elif candidates_dir.exists():
        shutil.rmtree(candidates_dir)

    applied = 0
    preserved = 0
    invalid = 0
    records: list[dict] = []

    for item in manifest["items"]:
        kit_file = str(item.get("kit_file", ""))
        group = str(item.get("group") or "UNASSIGNED").upper()
        editable = editable_dir / kit_file
        reference = reference_dir / kit_file
        if not kit_file or not editable.is_file() or not reference.is_file():
            invalid += 1
            records.append({"kit_file": kit_file, "group": group, "result": "missing-input"})
            continue

        current_sha = _sha256(editable)
        export_sha = str(item.get("workspace_editable_sha256_at_export", ""))
        # The sprint copy hash should equal the workspace export hash. Any difference
        # means the artist has already touched it, so do not overwrite by default.
        if not force and export_sha and current_sha != export_sha:
            preserved += 1
            records.append({
                "kit_file": kit_file,
                "group": group,
                "result": "preserved-existing-edit",
                "current_sha256": current_sha,
            })
            continue

        with Image.open(reference) as ref_img:
            original = ref_img.convert("RGBA")
        before_size = original.size
        before_alpha = original.getchannel("A").tobytes()
        original_metrics = _metrics(original)

        candidates: list[dict] = []
        for variant in VARIANTS:
            candidate = _apply_profile(original, group, variant)
            if candidate.size != before_size:
                raise ValueError(f"Studio-grade pass changed dimensions for {kit_file}")
            if candidate.getchannel("A").tobytes() != before_alpha:
                raise ValueError(f"Studio-grade pass changed alpha for {kit_file}")
            metrics = _metrics(candidate, original)
            score, reasons = _score_candidate(original_metrics, metrics, group)
            candidate_path = None
            if keep_candidates:
                variant_dir = candidates_dir / variant
                variant_dir.mkdir(parents=True, exist_ok=True)
                candidate_path = variant_dir / kit_file
                candidate.save(candidate_path, optimize=True)
            candidates.append({
                "variant": variant,
                "score": score,
                "reasons": reasons,
                "metrics": metrics,
                "local_candidate": str(candidate_path.relative_to(kit_dir)) if candidate_path else None,
            })

        candidates.sort(key=lambda row: (-float(row["score"]), row["variant"]))
        selected = candidates[0]
        chosen = _apply_profile(original, group, selected["variant"])
        chosen.save(editable, optimize=True)
        applied += 1
        records.append({
            "kit_file": kit_file,
            "master_file": item.get("master_file"),
            "group": group,
            "tile_id": item.get("tile_id"),
            "palette": item.get("palette"),
            "result": "studio-grade-seeded",
            "selected_variant": selected["variant"],
            "selected_score": selected["score"],
            "selected_reasons": selected["reasons"],
            "original_metrics": original_metrics,
            "selected_metrics": selected["metrics"],
            "output_sha256": _sha256(editable),
            "candidates": candidates,
        })

    result = {
        "schema": "swir.project002.studio-grade-art-pass.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "selection_mode": manifest.get("selection_mode"),
        "force": force,
        "keep_candidates": keep_candidates,
        "items": len(manifest["items"]),
        "applied": applied,
        "preserved_existing_edits": preserved,
        "invalid_or_missing": invalid,
        "important_note": (
            "Studio-Grade Art Pass is an automatic high-quality starting pass, not proof of final hand-finished art. "
            "It preserves dimensions/alpha and protects existing sprint edits unless --force is used. "
            "Final Pixel QA and in-game MesenCE review remain mandatory."
        ),
        "records": records,
    }
    (kit_dir / REPORT_NAME).write_text(json.dumps(result, indent=2), encoding="utf-8")
    _write_dashboard(result, kit_dir / "STUDIO_GRADE_ART_PASS.html")
    return result


def _write_dashboard(result: dict, path: Path) -> None:
    rows = []
    for row in result["records"]:
        variant = row.get("selected_variant", "—")
        score = row.get("selected_score", "—")
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(row.get('kit_file', '')))}</td>"
            f"<td>{html.escape(str(row.get('group', '')))}</td>"
            f"<td>{html.escape(str(row.get('result', '')))}</td>"
            f"<td>{html.escape(str(variant))}</td>"
            f"<td>{html.escape(str(score))}</td>"
            "</tr>"
        )
    document = f"""<!doctype html><html><head><meta charset='utf-8'><title>Project #002 Studio-Grade Art Pass</title>
<style>body{{font:15px system-ui;max-width:1200px;margin:30px auto;padding:0 22px;background:#0d1117;color:#e6edf3}}.card{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:16px;margin:12px 0}}table{{width:100%;border-collapse:collapse}}th,td{{padding:8px;border-bottom:1px solid #30363d;text-align:left}}</style></head><body>
<h1>Studio-Grade Art Pass</h1><div class='card'><b>Applied:</b> {result['applied']} &nbsp; <b>Preserved artist edits:</b> {result['preserved_existing_edits']} &nbsp; <b>Invalid:</b> {result['invalid_or_missing']}<p>{html.escape(result['important_note'])}</p></div><div class='card'><table><tr><th>Asset</th><th>Group</th><th>Result</th><th>Selected</th><th>Score</th></tr>{''.join(rows)}</table></div></body></html>"""
    path.write_text(document, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 studio-grade automatic polish for a High-Impact Art Sprint")
    parser.add_argument("kit", type=Path)
    parser.add_argument("--force", action="store_true", help="Replace sprint files even if they were already edited after export")
    parser.add_argument("--no-candidates", action="store_true", help="Do not keep local A/B/C candidate PNGs")
    args = parser.parse_args()
    result = apply_studio_grade_pass(args.kit, force=args.force, keep_candidates=not args.no_candidates)
    print(json.dumps(result, indent=2))
    return 0 if result["invalid_or_missing"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
