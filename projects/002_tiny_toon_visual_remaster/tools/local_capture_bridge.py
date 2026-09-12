from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from capture_gap_planner import build_capture_queue
from capture_mission_control import ensure_manifest, mission_status
from validate_hdpack import validate

SCHEMA = "swir.project002.capture-evidence.v1"
GROUP_ORDER = ("PLAYER", "BOSS", "ENEMY", "WORLD", "UI", "EFFECTS", "UNASSIGNED")
GROUP_TOKENS = {
    "PLAYER": ("player", "hero", "buster", "babs", "plucky", "hampton"),
    "BOSS": ("boss",),
    "ENEMY": ("enemy", "foe", "mob"),
    "UI": ("hud", "ui", "menu", "pause", "status", "result", "text", "font"),
    "EFFECTS": ("effect", "fx", "projectile", "shot", "spark", "smoke", "explosion", "transition"),
    "WORLD": ("world", "stage", "level", "bg", "background", "ground", "platform", "tilemap"),
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _group_for(text: str) -> str:
    value = text.lower()
    for group in GROUP_ORDER[:-1]:
        if any(token in value for token in GROUP_TOKENS.get(group, ())):
            return group
    return "UNASSIGNED"


def _parse_hires(pack: Path) -> dict:
    hires = pack / "hires.txt"
    text = hires.read_text(encoding="utf-8", errors="replace")
    images: list[str] = []
    tile_ids: set[str] = set()
    palettes: set[str] = set()
    conditions: list[str] = []
    groups = {group: 0 for group in GROUP_ORDER}
    mappings = 0

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("<img>"):
            value = line[5:].strip()
            if value and value not in images:
                images.append(value)
        if "<condition>" in line:
            conditions.append(line.split("<condition>", 1)[1].split(",", 1)[0].strip())
        if "<tile>" in line:
            mappings += 1
            prefix, payload = line.split("<tile>", 1)
            fields = [field.strip() for field in payload.split(",")]
            if len(fields) >= 2 and fields[1]:
                tile_ids.add(fields[1].upper())
            if len(fields) >= 3 and fields[2]:
                palettes.add(fields[2].upper())
            label = prefix.strip().strip("[]")
            groups[_group_for(label)] += 1

    image_rows: list[dict] = []
    for relative in images:
        candidate = pack / relative
        row = {"name": relative.replace("\\", "/"), "present": candidate.is_file()}
        if candidate.is_file():
            row["bytes"] = candidate.stat().st_size
            row["sha256"] = _sha256(candidate)
            try:
                with Image.open(candidate) as image:
                    row["width"], row["height"] = image.size
                    row["mode"] = image.mode
            except Exception:
                row["width"] = None
                row["height"] = None
                row["mode"] = "UNREADABLE"
        image_rows.append(row)

    fingerprint = hashlib.sha256()
    fingerprint.update(_sha256(hires).encode("ascii"))
    for row in sorted(image_rows, key=lambda item: item["name"].lower()):
        fingerprint.update(row["name"].encode("utf-8"))
        fingerprint.update(str(row.get("sha256", "MISSING")).encode("ascii", errors="ignore"))

    return {
        "hires_sha256": _sha256(hires),
        "capture_fingerprint": fingerprint.hexdigest(),
        "mapping_count": mappings,
        "unique_tile_ids": len(tile_ids),
        "unique_palettes": len(palettes),
        "condition_count": len(conditions),
        "groups": groups,
        "tile_ids": sorted(tile_ids),
        "palettes": sorted(palettes),
        "condition_names": sorted(set(conditions)),
        "images": image_rows,
    }


def build_safe_evidence(project_root: Path, capture: Path, *, previous_capture: Path | None = None) -> dict:
    """Build a metadata-only evidence envelope.

    The returned structure deliberately contains no absolute local path, ROM identity,
    save-state data, image pixels or hires.txt source lines. PNG files are inspected
    locally only to record size/dimensions/hash and are never copied into the handoff.
    """
    root = Path(project_root)
    pack = Path(capture)
    previous = Path(previous_capture) if previous_capture else None
    errors, warnings, scale = validate(pack)
    if errors:
        raise ValueError("Capture failed HD Pack validation: " + "; ".join(errors))

    manifest = root / "CAPTURE_MISSIONS.json"
    ensure_manifest(manifest)
    mission = mission_status(manifest)
    queue = root / "Artwork" / "ART_QUEUE.csv"
    gap = build_capture_queue(
        pack,
        queue if queue.is_file() else None,
        previous,
        queue if queue.is_file() else None,
        manifest,
    )
    regressions = [row for row in gap.get("queue", []) if row.get("kind") == "CAPTURE_REGRESSION"]
    next_rows = []
    for row in gap.get("queue", [])[:20]:
        next_rows.append({
            "priority": int(row.get("priority", 0) or 0),
            "kind": str(row.get("kind", "")),
            "group": str(row.get("group", "")),
            "target": str(row.get("family") or row.get("label") or row.get("state") or row.get("mission") or ""),
        })

    parsed = _parse_hires(pack)
    return {
        "schema": SCHEMA,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "privacy_contract": {
            "contains_rom": False,
            "contains_save_state": False,
            "contains_capture_pixels": False,
            "contains_emulator_binary": False,
            "contains_absolute_local_paths": False,
            "metadata_only": True,
        },
        "hd_pack": {
            "scale": scale,
            "warnings": warnings,
            **parsed,
        },
        "capture_missions": {
            "gate": mission.get("release_capture_gate", "BLOCKED"),
            "done": int(mission.get("done", 0) or 0),
            "total": int(mission.get("total", 0) or 0),
            "percent": mission.get("percent", 0),
        },
        "capture_gap": {
            "regressions": len(regressions),
            "progressed": bool(gap.get("comparison", {}).get("progressed", False)),
            "next": next_rows,
        },
        "release_claim": "NO CLAIM — local evidence must still satisfy authoritative Gate A–D review.",
    }


def _flatten_csv(evidence: dict) -> list[dict]:
    rows: list[dict] = []
    hd = evidence["hd_pack"]
    for group in GROUP_ORDER:
        rows.append({"section": "group", "key": group, "value": hd["groups"].get(group, 0), "detail": "captured mappings"})
    rows.extend([
        {"section": "summary", "key": "mapping_count", "value": hd["mapping_count"], "detail": ""},
        {"section": "summary", "key": "unique_tile_ids", "value": hd["unique_tile_ids"], "detail": ""},
        {"section": "summary", "key": "unique_palettes", "value": hd["unique_palettes"], "detail": ""},
        {"section": "summary", "key": "condition_count", "value": hd["condition_count"], "detail": ""},
        {"section": "capture", "key": "mission_gate", "value": evidence["capture_missions"]["gate"], "detail": f"{evidence['capture_missions']['done']}/{evidence['capture_missions']['total']}"},
        {"section": "capture", "key": "regressions", "value": evidence["capture_gap"]["regressions"], "detail": ""},
    ])
    for image in hd["images"]:
        rows.append({
            "section": "image_metadata",
            "key": image["name"],
            "value": "present" if image.get("present") else "missing",
            "detail": f"{image.get('width', '')}x{image.get('height', '')}; {image.get('bytes', 0)} bytes; sha256={image.get('sha256', '')}",
        })
    return rows


def write_safe_handoff(evidence: dict, output_dir: Path) -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "SAFE_CAPTURE_HANDOFF.json"
    csv_path = out / "SAFE_CAPTURE_HANDOFF.csv"
    html_path = out / "LOCAL_CAPTURE_BRIDGE.html"
    json_path.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["section", "key", "value", "detail"])
        writer.writeheader()
        writer.writerows(_flatten_csv(evidence))

    groups = "".join(
        f"<tr><td>{html.escape(group)}</td><td>{evidence['hd_pack']['groups'].get(group, 0)}</td></tr>"
        for group in GROUP_ORDER
    )
    next_rows = "".join(
        f"<tr><td>{row['priority']}</td><td>{html.escape(row['kind'])}</td><td>{html.escape(row['group'])}</td><td>{html.escape(row['target'])}</td></tr>"
        for row in evidence["capture_gap"]["next"]
    ) or "<tr><td colspan='4'>No queued capture action.</td></tr>"
    doc = f"""<!doctype html><html><head><meta charset='utf-8'><title>Local Capture Bridge</title>
<style>body{{font:15px system-ui;max-width:1150px;margin:30px auto;padding:0 20px;background:#0d1117;color:#e6edf3}}.card{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:16px;margin:12px 0}}table{{width:100%;border-collapse:collapse}}td,th{{padding:8px;border-bottom:1px solid #30363d;text-align:left}}code{{color:#79c0ff}}</style></head><body>
<h1>Project #002 — Local Capture Bridge</h1><div class='card'><b>Privacy-safe metadata handoff</b><p>No ROM, save state, capture pixels, emulator binary or absolute local paths are stored in this handoff.</p><p>Fingerprint: <code>{evidence['hd_pack']['capture_fingerprint']}</code></p><p>Mission gate: {html.escape(str(evidence['capture_missions']['gate']))} · {evidence['capture_missions']['done']}/{evidence['capture_missions']['total']} · regressions {evidence['capture_gap']['regressions']}</p></div>
<div class='card'><h2>Captured mapping groups</h2><table><tr><th>Group</th><th>Mappings</th></tr>{groups}</table></div>
<div class='card'><h2>Capture work next</h2><table><tr><th>Priority</th><th>Type</th><th>Group</th><th>Target</th></tr>{next_rows}</table></div>
</body></html>"""
    html_path.write_text(doc, encoding="utf-8")
    return {"json": str(json_path), "csv": str(csv_path), "dashboard": str(html_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 privacy-safe local MesenCE capture bridge")
    parser.add_argument("project_root", type=Path)
    parser.add_argument("capture", type=Path)
    parser.add_argument("--previous-capture", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or args.project_root / "Reports" / "LocalCaptureBridge"
    evidence = build_safe_evidence(args.project_root, args.capture, previous_capture=args.previous_capture)
    outputs = write_safe_handoff(evidence, output)
    print(json.dumps({"evidence": evidence, "outputs": outputs}, indent=2))
    return 2 if evidence["capture_gap"]["regressions"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
