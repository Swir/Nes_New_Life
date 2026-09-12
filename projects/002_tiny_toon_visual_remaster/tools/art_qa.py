from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

from validate_hdpack import validate


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _image_index_map(pack_dir: Path) -> dict[str, Path]:
    images: list[Path] = []
    hires = pack_dir / "hires.txt"
    if not hires.is_file():
        raise FileNotFoundError(f"Missing hires.txt: {hires}")
    for raw in hires.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = raw.strip()
        if line.lower().startswith("<img>"):
            images.append(pack_dir / line[5:].strip())
    return {str(index): path for index, path in enumerate(images)}


def _changed_masters(workspace: Path) -> list[dict]:
    manifest_path = workspace / "MASTER_TILES.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Missing MASTER_TILES.json: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    changed: list[dict] = []
    for master in manifest.get("masters", []):
        name = master["file"]
        original = workspace / "original" / name
        editable = workspace / "editable" / name
        if not original.is_file() or not editable.is_file():
            raise FileNotFoundError(f"Missing master pair for {name}")
        with Image.open(original) as before, Image.open(editable) as after:
            if before.size != after.size:
                raise ValueError(f"Master size changed: {name} {before.size} -> {after.size}")
        if _sha256(original) != _sha256(editable):
            changed.append(master)
    return changed


def _allowed_rectangles(changed: list[dict]) -> dict[str, list[tuple[int, int, int, int, str]]]:
    result: dict[str, list[tuple[int, int, int, int, str]]] = {}
    for master in changed:
        for target in master.get("targets", []):
            image_index = str(target["image_index"])
            w = int(target.get("width", master.get("width", 0)))
            h = int(target.get("height", master.get("height", 0)))
            if not w or not h:
                # Current master tiles are one HD tile (8 NES pixels * scale 4 = 32px)
                # unless the manifest explicitly records another size.
                w = int(master.get("pixel_width", 32))
                h = int(master.get("pixel_height", 32))
            x, y = int(target["x"]), int(target["y"])
            result.setdefault(image_index, []).append((x, y, x + w, y + h, master["file"]))
    return result


def audit_art_apply(source_pack: Path, output_pack: Path, workspace: Path, report_dir: Path) -> dict:
    source_errors, _, _ = validate(source_pack)
    output_errors, output_warnings, output_stats = validate(output_pack)
    if source_errors:
        raise ValueError("Source HD pack is invalid: " + "; ".join(source_errors))
    if output_errors:
        raise ValueError("Output HD pack is invalid: " + "; ".join(output_errors))

    report_dir.mkdir(parents=True, exist_ok=True)
    changed = _changed_masters(workspace)
    allowed = _allowed_rectangles(changed)
    source_map = _image_index_map(source_pack)
    output_map = _image_index_map(output_pack)

    mapping_preserved = (source_pack / "hires.txt").read_bytes() == (output_pack / "hires.txt").read_bytes()
    sheets: list[dict] = []
    total_changed = 0
    total_authorized = 0
    total_unauthorized = 0
    touched_targets: set[str] = set()

    if set(source_map) != set(output_map):
        raise ValueError("Source/output <img> index sets differ")

    for index in sorted(source_map, key=int):
        source_path = source_map[index]
        output_path = output_map[index]
        if source_path.name != output_path.name:
            raise ValueError(f"Image mapping changed at index {index}: {source_path.name} -> {output_path.name}")
        with Image.open(source_path) as src_raw, Image.open(output_path) as out_raw:
            src = src_raw.convert("RGBA")
            out = out_raw.convert("RGBA")
        if src.size != out.size:
            raise ValueError(f"Sheet dimensions changed for {source_path.name}: {src.size} -> {out.size}")

        allow_mask = Image.new("L", src.size, 0)
        draw = ImageDraw.Draw(allow_mask)
        for x0, y0, x1, y1, master_name in allowed.get(index, []):
            if x0 < 0 or y0 < 0 or x1 > src.width or y1 > src.height:
                raise ValueError(f"Authorized target outside sheet {source_path.name}: {master_name} @ {x0},{y0},{x1},{y1}")
            draw.rectangle((x0, y0, x1 - 1, y1 - 1), fill=255)

        difference = ImageChops.difference(src, out)
        difference_mask = difference.convert("RGB").convert("L").point(lambda value: 255 if value else 0)
        changed_pixels = 0
        authorized_pixels = 0
        unauthorized_pixels = 0
        diff_overlay = Image.new("RGBA", src.size, (0, 0, 0, 0))
        overlay_pixels = diff_overlay.load()
        diff_pixels = difference_mask.load()
        allow_pixels = allow_mask.load()

        for y in range(src.height):
            for x in range(src.width):
                if not diff_pixels[x, y]:
                    continue
                changed_pixels += 1
                if allow_pixels[x, y]:
                    authorized_pixels += 1
                    overlay_pixels[x, y] = (0, 255, 80, 210)
                else:
                    unauthorized_pixels += 1
                    overlay_pixels[x, y] = (255, 0, 180, 255)

        for x0, y0, x1, y1, master_name in allowed.get(index, []):
            if difference_mask.crop((x0, y0, x1, y1)).getbbox() is not None:
                touched_targets.add(master_name)

        total_changed += changed_pixels
        total_authorized += authorized_pixels
        total_unauthorized += unauthorized_pixels
        overlay_name = f"diff_{int(index):03d}_{source_path.stem}.png"
        if changed_pixels:
            diff_overlay.save(report_dir / overlay_name, optimize=True)
        else:
            overlay_name = ""
        sheets.append({
            "image_index": int(index),
            "image": source_path.name,
            "changed_pixels": changed_pixels,
            "authorized_changed_pixels": authorized_pixels,
            "unauthorized_changed_pixels": unauthorized_pixels,
            "authorized_regions": len(allowed.get(index, [])),
            "diff_overlay": overlay_name,
        })

    changed_names = {master["file"] for master in changed}
    untouched_changed_masters = sorted(changed_names - touched_targets)
    qa_pass = mapping_preserved and total_unauthorized == 0 and not untouched_changed_masters
    result = {
        "qa_gate": "PASS" if qa_pass else "BLOCKED",
        "mapping_preserved": mapping_preserved,
        "changed_master_count": len(changed),
        "changed_pixels": total_changed,
        "authorized_changed_pixels": total_authorized,
        "unauthorized_changed_pixels": total_unauthorized,
        "edited_masters_with_no_output_difference": untouched_changed_masters,
        "validation_warnings": output_warnings,
        "validation_stats": output_stats,
        "sheets": sheets,
    }
    (report_dir / "ART_QA_RESULT.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    _write_html(result, report_dir / "ART_QA_REPORT.html")
    return result


def _write_html(result: dict, output: Path) -> None:
    rows = []
    for sheet in result["sheets"]:
        overlay = sheet["diff_overlay"]
        link = f'<a href="{html.escape(overlay)}">diff</a>' if overlay else "—"
        rows.append(
            "<tr>"
            f"<td>{sheet['image_index']}</td><td>{html.escape(sheet['image'])}</td>"
            f"<td>{sheet['changed_pixels']}</td><td>{sheet['authorized_changed_pixels']}</td>"
            f"<td>{sheet['unauthorized_changed_pixels']}</td><td>{sheet['authorized_regions']}</td><td>{link}</td>"
            "</tr>"
        )
    blockers = []
    if not result["mapping_preserved"]:
        blockers.append("hires.txt changed")
    if result["unauthorized_changed_pixels"]:
        blockers.append(f"{result['unauthorized_changed_pixels']} changed pixels outside authorized master targets")
    if result["edited_masters_with_no_output_difference"]:
        blockers.append("edited masters produced no output difference: " + ", ".join(result["edited_masters_with_no_output_difference"]))
    blocker_html = "<br>".join(html.escape(item) for item in blockers) or "None"
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Project #002 Art QA</title>
<style>body{{font-family:Segoe UI,Arial,sans-serif;max-width:1200px;margin:32px auto;padding:0 20px;background:#111;color:#eee}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #444;padding:8px;text-align:left}}th{{background:#222}}.pass{{color:#55e07a}}.blocked{{color:#ff5c8a}}code{{background:#222;padding:2px 5px}}</style></head>
<body><h1>Project #002 — Batch Art Pixel QA</h1>
<h2 class="{'pass' if result['qa_gate'] == 'PASS' else 'blocked'}">QA gate: {result['qa_gate']}</h2>
<p><b>Mapping preserved:</b> {result['mapping_preserved']}<br>
<b>Changed masters:</b> {result['changed_master_count']}<br>
<b>Changed pixels:</b> {result['changed_pixels']}<br>
<b>Authorized changed pixels:</b> {result['authorized_changed_pixels']}<br>
<b>Unauthorized changed pixels:</b> {result['unauthorized_changed_pixels']}</p>
<p><b>Blockers:</b><br>{blocker_html}</p>
<p>Diff overlays contain only change markers: green = authorized master region change, magenta = unauthorized change. They do not reproduce the source artwork.</p>
<table><thead><tr><th>#</th><th>Sheet</th><th>Changed</th><th>Authorized</th><th>Unauthorized</th><th>Allowed regions</th><th>Overlay</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
</body></html>"""
    output.write_text(document, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 pixel-safe batch art QA gate")
    parser.add_argument("source_pack", type=Path)
    parser.add_argument("output_pack", type=Path)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("report_dir", type=Path)
    args = parser.parse_args()
    result = audit_art_apply(args.source_pack, args.output_pack, args.workspace, args.report_dir)
    print(json.dumps(result, indent=2))
    return 0 if result["qa_gate"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
