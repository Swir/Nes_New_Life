from __future__ import annotations

import argparse
import csv
import json
import re
import zipfile
from dataclasses import asdict
from pathlib import Path

from hdpack_pipeline import analyze, parse_tile_rules, write_art_queue
from validate_hdpack import validate

GROUP_KEYWORDS = {
    "PLAYER": ("hero", "player", "buster", "babs", "plucky", "furball"),
    "BOSS": ("boss",),
    "ENEMY": ("enemy", "foe", "mob"),
    "UI": ("hud", "ui", "menu", "font", "text", "title", "score", "life", "lives"),
    "EFFECTS": ("effect", "fx", "projectile", "shot", "spark", "explosion", "smoke"),
    "WORLD": ("world", "level", "stage", "background", "bg", "scenery", "terrain", "tilemap"),
}

CHECKLIST_ITEMS = [
    ("boot_title_menu", "Boot, title screen and every menu/state"),
    ("player_all_moves", "Player: every movement/action/hit/death animation"),
    ("all_level_routes", "Every playable level/route and scrolling section captured"),
    ("all_enemies", "Every common enemy and enemy animation captured"),
    ("all_bosses", "Every boss phase/animation/effect captured"),
    ("hud_and_text", "HUD, counters, fonts, dialogs and status screens captured"),
    ("effects_and_transitions", "Projectiles, particles, transitions and special effects captured"),
    ("ending_credits", "Ending/credits/game-complete states captured"),
    ("art_pass_complete", "Final 4x art pass completed for the intended release scope"),
    ("full_game_regression", "Full-game visual regression pass completed in MesenCE"),
]

FORBIDDEN_SUFFIXES = {
    ".nes", ".fds", ".unf", ".unif", ".sav", ".srm", ".state", ".mss", ".ips", ".bps"
}
FORBIDDEN_NAMES = {"rom_info.json"}
GENERATED_NAMES = {
    "NES_NEW_LIFE_REPORT.html",
    "NES_NEW_LIFE_ART_QUEUE.csv",
    "NES_NEW_LIFE_READINESS.html",
    "NES_NEW_LIFE_READINESS.json",
}


def _tokenize(value: str) -> set[str]:
    return {token for token in re.split(r"[^a-z0-9]+", value.lower()) if token}


def infer_art_group(condition_names: set[str]) -> tuple[str, str]:
    tokens: set[str] = set()
    for name in condition_names:
        tokens.update(_tokenize(name))
    matches: list[tuple[int, str]] = []
    for group, keywords in GROUP_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in tokens)
        if score:
            matches.append((score, group))
    if not matches:
        return "UNASSIGNED", "none"
    matches.sort(key=lambda item: (-item[0], item[1]))
    top_score, top_group = matches[0]
    confidence = "high" if top_score >= 2 else "medium"
    return top_group, confidence


def write_grouped_art_queue(pack_dir: Path, output: Path | None = None) -> Path:
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
        writer.writerow([
            "priority", "tile_id", "palette", "uses", "conditional_uses", "conditions",
            "status", "art_group", "group_confidence", "notes"
        ])
        for index, item in enumerate(ranked, 1):
            group, confidence = infer_art_group(item["conditions"])
            writer.writerow([
                index,
                item["tile_id"],
                item["palette"],
                item["uses"],
                item["conditional_uses"],
                " | ".join(sorted(item["conditions"])),
                "TODO",
                group,
                confidence,
                "",
            ])
    return output


def default_checklist() -> dict:
    return {
        "schema": 1,
        "warning": "Manual evidence checklist. It is not an automatic whole-game coverage percentage.",
        "items": {key: {"label": label, "done": False, "notes": ""} for key, label in CHECKLIST_ITEMS},
    }


def ensure_checklist(path: Path) -> Path:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(default_checklist(), indent=2), encoding="utf-8")
    return path


def _load_checklist(path: Path | None) -> dict:
    if path is None or not path.is_file():
        return default_checklist()
    data = json.loads(path.read_text(encoding="utf-8"))
    defaults = default_checklist()
    incoming = data.get("items", {}) if isinstance(data, dict) else {}
    for key in defaults["items"]:
        if key in incoming and isinstance(incoming[key], dict):
            defaults["items"][key]["done"] = bool(incoming[key].get("done", False))
            defaults["items"][key]["notes"] = str(incoming[key].get("notes", ""))
    return defaults


def _queue_status(queue: Path | None) -> dict:
    result = {"rows": 0, "done": 0, "todo": 0, "unassigned": 0, "groups": {}}
    if queue is None or not queue.is_file():
        return result
    with queue.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            result["rows"] += 1
            status = (row.get("status") or "TODO").strip().upper()
            group = (row.get("art_group") or "UNASSIGNED").strip().upper()
            if status in {"DONE", "COMPLETE", "COMPLETED", "FINAL"}:
                result["done"] += 1
            else:
                result["todo"] += 1
            if group == "UNASSIGNED":
                result["unassigned"] += 1
            result["groups"][group] = result["groups"].get(group, 0) + 1
    return result


def readiness(pack_dir: Path, checklist: Path | None = None, queue: Path | None = None) -> dict:
    stats = analyze(pack_dir)
    errors, warnings, validation_stats = validate(pack_dir)
    checklist_data = _load_checklist(checklist)
    queue_data = _queue_status(queue)
    items = checklist_data["items"]
    checklist_done = sum(1 for item in items.values() if item["done"])
    checklist_total = len(items)

    blockers: list[str] = []
    if errors:
        blockers.append("HD Pack validation has structural errors")
    if stats.missing_images:
        blockers.append("Referenced PNG files are missing")
    if stats.scale < 4:
        blockers.append("HD Pack scale is below the Project #002 4x target")
    if checklist_done < checklist_total:
        blockers.append(f"Manual full-game evidence checklist incomplete ({checklist_done}/{checklist_total})")
    if queue_data["rows"] and queue_data["todo"]:
        blockers.append(f"Art queue still contains {queue_data['todo']} unfinished entries")
    if queue_data["rows"] and queue_data["unassigned"]:
        blockers.append(f"Art queue still contains {queue_data['unassigned']} unassigned entries")

    release_ready = not blockers
    return {
        "release_ready": release_ready,
        "release_gate": "PASS" if release_ready else "BLOCKED",
        "important_note": "This gate combines structural checks and explicit manual evidence; it does not infer unseen game content.",
        "pack_stats": asdict(stats),
        "validator": {"errors": errors, "warnings": warnings, "stats": validation_stats},
        "checklist": {
            "done": checklist_done,
            "total": checklist_total,
            "items": items,
        },
        "art_queue": queue_data,
        "blockers": blockers,
    }


def write_readiness_dashboard(
    pack_dir: Path,
    checklist: Path | None = None,
    queue: Path | None = None,
    output: Path | None = None,
) -> Path:
    result = readiness(pack_dir, checklist, queue)
    output = output or (pack_dir / "NES_NEW_LIFE_READINESS.html")
    json_output = output.with_suffix(".json")
    json_output.write_text(json.dumps(result, indent=2), encoding="utf-8")

    gate = result["release_gate"]
    blockers = "".join(f"<li>{item}</li>" for item in result["blockers"]) or "<li>None</li>"
    checklist_rows = "".join(
        f"<tr><td>{'✅' if item['done'] else '⬜'}</td><td>{item['label']}</td><td>{item['notes']}</td></tr>"
        for item in result["checklist"]["items"].values()
    )
    group_rows = "".join(
        f"<tr><td>{group}</td><td>{count}</td></tr>"
        for group, count in sorted(result["art_queue"]["groups"].items())
    ) or "<tr><td>No queue loaded</td><td>0</td></tr>"
    stats = result["pack_stats"]
    queue_stats = result["art_queue"]
    html = f"""<!doctype html><meta charset='utf-8'><title>Project #002 HD Readiness</title>
<style>body{{font:16px system-ui;max-width:1050px;margin:36px auto;padding:0 22px;background:#0d1117;color:#e6edf3}}.card{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:18px;margin:14px 0}}.pass{{color:#3fb950}}.blocked{{color:#f85149}}table{{width:100%;border-collapse:collapse}}td,th{{padding:9px;border-bottom:1px solid #30363d;text-align:left}}code{{color:#79c0ff}}</style>
<h1>NES New Life — Project #002 HD Readiness</h1>
<div class='card'><h2 class='{'pass' if gate == 'PASS' else 'blocked'}'>Release gate: {gate}</h2>
<p>{result['important_note']}</p><ul>{blockers}</ul></div>
<div class='card'><h2>Pack structure</h2><p>Scale: <b>{stats['scale']}×</b> · Images: <b>{len(stats['images'])}</b> · Tile rules: <b>{stats['tile_rules']}</b> · Unique tiles: <b>{stats['unique_tile_ids']}</b> · Palettes: <b>{stats['unique_palettes']}</b></p></div>
<div class='card'><h2>Art queue</h2><p>Total: <b>{queue_stats['rows']}</b> · Done: <b>{queue_stats['done']}</b> · TODO: <b>{queue_stats['todo']}</b> · Unassigned: <b>{queue_stats['unassigned']}</b></p><table><tr><th>Group</th><th>Entries</th></tr>{group_rows}</table></div>
<div class='card'><h2>Manual full-game evidence ({result['checklist']['done']}/{result['checklist']['total']})</h2><table><tr><th></th><th>Evidence item</th><th>Notes</th></tr>{checklist_rows}</table></div>
"""
    output.write_text(html, encoding="utf-8")
    return output


def package_hd_pack(pack_dir: Path, output_zip: Path) -> Path:
    errors, _, _ = validate(pack_dir)
    if errors:
        raise ValueError("Cannot package invalid HD Pack: " + "; ".join(errors))
    stats = analyze(pack_dir)
    if stats.missing_images:
        raise ValueError("Cannot package HD Pack with missing images: " + ", ".join(stats.missing_images))
    if not (pack_dir / "hires.txt").is_file():
        raise ValueError("Cannot package without hires.txt")

    output_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(pack_dir.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(pack_dir)
            if path.suffix.lower() in FORBIDDEN_SUFFIXES:
                raise ValueError(f"Forbidden ROM/save/patch file in pack: {rel}")
            if path.name.lower() in FORBIDDEN_NAMES:
                continue
            if path.name in GENERATED_NAMES or path.name.startswith("NES_NEW_LIFE_PREVIEW"):
                continue
            archive.write(path, rel.as_posix())
    return output_zip


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 HD release-readiness and packaging tools")
    commands = parser.add_subparsers(dest="command", required=True)

    classify = commands.add_parser("classify")
    classify.add_argument("pack", type=Path)
    classify.add_argument("--output", type=Path)

    checklist_cmd = commands.add_parser("init-checklist")
    checklist_cmd.add_argument("output", type=Path)

    dash = commands.add_parser("dashboard")
    dash.add_argument("pack", type=Path)
    dash.add_argument("--checklist", type=Path)
    dash.add_argument("--queue", type=Path)
    dash.add_argument("--output", type=Path)

    package = commands.add_parser("package")
    package.add_argument("pack", type=Path)
    package.add_argument("output", type=Path)

    args = parser.parse_args()
    if args.command == "classify":
        print(write_grouped_art_queue(args.pack, args.output))
        return 0
    if args.command == "init-checklist":
        print(ensure_checklist(args.output))
        return 0
    if args.command == "dashboard":
        print(write_readiness_dashboard(args.pack, args.checklist, args.queue, args.output))
        return 0
    print(package_hd_pack(args.pack, args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
