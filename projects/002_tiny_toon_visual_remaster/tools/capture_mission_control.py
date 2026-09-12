from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from hdpack_pipeline import analyze

MISSION_ITEMS = [
    ("boot_title_menu", "Boot, title, menus and every menu animation/state", "UI", 100),
    ("player_idle_walk_run", "Player idle/walk/run/crouch/jump/fall/land", "PLAYER", 100),
    ("player_actions_damage_death", "Player attacks/actions, damage, invulnerability and death", "PLAYER", 95),
    ("world_route_1", "World/route pass 1: traverse every visible branch and scrolling boundary", "WORLD", 100),
    ("world_route_2", "World/route pass 2: alternate paths, secrets and revisits", "WORLD", 90),
    ("common_enemies", "Every common enemy with movement/attack/hit/death frames", "ENEMY", 95),
    ("rare_enemies", "Rare/route-specific enemies and uncommon states", "ENEMY", 90),
    ("bosses_all_phases", "Every boss: intro, every phase, attacks, hit/death and effects", "BOSS", 100),
    ("hud_text_status", "HUD, counters, fonts, dialogs, pause/status and result screens", "UI", 95),
    ("effects_transitions", "Projectiles, particles, doors, fades, transitions and special effects", "EFFECTS", 90),
    ("ending_credits", "Ending, credits and post-game states", "UI", 100),
]


def default_manifest() -> dict:
    return {
        "schema": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "warning": "Manual capture mission evidence. Completion is never inferred from tile counts alone.",
        "missions": {
            key: {
                "label": label,
                "group": group,
                "priority": priority,
                "done": False,
                "notes": "",
                "last_session": None,
            }
            for key, label, group, priority in MISSION_ITEMS
        },
        "sessions": [],
    }


def ensure_manifest(path: Path) -> Path:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(default_manifest(), indent=2), encoding="utf-8")
    return path


def load_manifest(path: Path) -> dict:
    ensure_manifest(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    defaults = default_manifest()
    incoming = data.get("missions", {}) if isinstance(data, dict) else {}
    for key, item in defaults["missions"].items():
        if key in incoming and isinstance(incoming[key], dict):
            item["done"] = bool(incoming[key].get("done", False))
            item["notes"] = str(incoming[key].get("notes", ""))
            item["last_session"] = incoming[key].get("last_session")
    defaults["sessions"] = list(data.get("sessions", [])) if isinstance(data, dict) else []
    return defaults


def snapshot_capture(capture_dir: Path) -> dict:
    stats = analyze(capture_dir)
    return {
        "scale": stats.scale,
        "images": len(stats.images),
        "tile_rules": stats.tile_rules,
        "unique_tile_ids": stats.unique_tile_ids,
        "unique_palettes": stats.unique_palettes,
        "missing_images": list(stats.missing_images),
    }


def record_session(
    manifest_path: Path,
    capture_dir: Path,
    completed: list[str] | None = None,
    notes: str = "",
    *,
    capture_fingerprint_sha256: str | None = None,
    attestation: str | None = None,
) -> dict:
    data = load_manifest(manifest_path)
    completed = completed or []
    unknown = [key for key in completed if key not in data["missions"]]
    if unknown:
        raise ValueError("Unknown mission key(s): " + ", ".join(unknown))

    current = snapshot_capture(capture_dir)
    previous = data["sessions"][-1]["capture"] if data["sessions"] else None
    delta = {
        "tile_rules": current["tile_rules"] - previous["tile_rules"] if previous else current["tile_rules"],
        "unique_tile_ids": current["unique_tile_ids"] - previous["unique_tile_ids"] if previous else current["unique_tile_ids"],
        "unique_palettes": current["unique_palettes"] - previous["unique_palettes"] if previous else current["unique_palettes"],
        "images": current["images"] - previous["images"] if previous else current["images"],
    }
    session_id = len(data["sessions"]) + 1
    timestamp = datetime.now(timezone.utc).isoformat()
    for key in completed:
        data["missions"][key]["done"] = True
        data["missions"][key]["last_session"] = session_id
    session = {
        "id": session_id,
        "timestamp_utc": timestamp,
        "capture_path": str(Path(capture_dir).resolve()),
        "capture": current,
        "delta": delta,
        "completed_missions": completed,
        "notes": notes,
    }
    if capture_fingerprint_sha256:
        session["capture_fingerprint_sha256"] = str(capture_fingerprint_sha256)
    if attestation:
        session["attestation"] = str(attestation)
    data["sessions"].append(session)
    manifest_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return session


def mission_status(manifest_path: Path) -> dict:
    data = load_manifest(manifest_path)
    missions = data["missions"]
    done = [key for key, value in missions.items() if value["done"]]
    pending = [
        {"key": key, **value}
        for key, value in missions.items()
        if not value["done"]
    ]
    pending.sort(key=lambda item: (-int(item["priority"]), item["group"], item["key"]))
    last = data["sessions"][-1] if data["sessions"] else None
    stagnating = bool(last and all(int(v) <= 0 for v in last["delta"].values()))
    return {
        "done": len(done),
        "total": len(missions),
        "percent": round((len(done) / len(missions)) * 100, 1) if missions else 0.0,
        "next_missions": pending[:5],
        "last_session": last,
        "stagnating": stagnating,
        "release_capture_gate": "PASS" if len(done) == len(missions) else "BLOCKED",
    }


def write_dashboard(manifest_path: Path, output: Path) -> Path:
    result = mission_status(manifest_path)
    next_rows = "".join(
        f"<tr><td>{item['priority']}</td><td>{item['group']}</td><td><code>{item['key']}</code></td><td>{item['label']}</td></tr>"
        for item in result["next_missions"]
    ) or "<tr><td colspan='4'>All capture missions complete</td></tr>"
    last = result["last_session"]
    last_html = "No capture session recorded yet."
    if last:
        d = last["delta"]
        last_html = (
            f"Session #{last['id']} — Δ rules <b>{d['tile_rules']:+d}</b>, "
            f"tiles <b>{d['unique_tile_ids']:+d}</b>, palettes <b>{d['unique_palettes']:+d}</b>, "
            f"images <b>{d['images']:+d}</b>"
        )
    warning = "<p class='warn'>No new capture data in the latest session — change route/state before continuing.</p>" if result["stagnating"] else ""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        f"""<!doctype html><meta charset='utf-8'><title>Project #002 Capture Mission Control</title>
<style>body{{font:16px system-ui;max-width:1050px;margin:36px auto;padding:0 22px;background:#0d1117;color:#e6edf3}}.card{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:18px;margin:14px 0}}table{{width:100%;border-collapse:collapse}}td,th{{padding:9px;border-bottom:1px solid #30363d;text-align:left}}code{{color:#79c0ff}}.warn{{color:#f2cc60}}</style>
<h1>Tiny Toon Visual Remaster — Capture Mission Control</h1>
<div class='card'><h2>Capture gate: {result['release_capture_gate']}</h2><p><b>{result['done']}/{result['total']}</b> missions complete ({result['percent']}%).</p>{warning}<p>{last_html}</p></div>
<div class='card'><h2>Next highest-impact capture missions</h2><table><tr><th>Priority</th><th>Group</th><th>Key</th><th>What to capture</th></tr>{next_rows}</table></div>
""",
        encoding="utf-8",
    )
    output.with_suffix(".json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 capture mission controller")
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init")
    init.add_argument("manifest", type=Path)
    record = commands.add_parser("record")
    record.add_argument("manifest", type=Path)
    record.add_argument("capture", type=Path)
    record.add_argument("--complete", action="append", default=[])
    record.add_argument("--notes", default="")
    dashboard = commands.add_parser("dashboard")
    dashboard.add_argument("manifest", type=Path)
    dashboard.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.command == "init":
        print(ensure_manifest(args.manifest))
        return 0
    if args.command == "record":
        print(json.dumps(record_session(args.manifest, args.capture, args.complete, args.notes), indent=2))
        return 0
    print(write_dashboard(args.manifest, args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())