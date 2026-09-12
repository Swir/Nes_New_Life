from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path

from capture_integrity_ledger import assert_capture_admissible, build_ledger
from capture_mission_control import MISSION_ITEMS, ensure_manifest, load_manifest, mission_status, record_session

ATTESTATION = "VERIFIED_IN_GAME"

MISSION_CUES = {
    "boot_title_menu": [
        "Cold boot the ROM and wait through every title/logo animation.",
        "Open every menu/submenu and trigger cursor/selection animation states.",
        "Do not mark complete until all visible boot/title/menu states were actually seen in MesenCE.",
    ],
    "player_idle_walk_run": [
        "Exercise idle, walk/run, crouch, jump, fall and landing states.",
        "Change direction where relevant and visit more than one visual environment.",
        "Watch for palette/context changes while moving.",
    ],
    "player_actions_damage_death": [
        "Trigger every player action/attack available in normal play.",
        "Take damage, observe invulnerability flashing/state changes and trigger death/respawn.",
        "Repeat in contexts that visibly change the player palette/effects when practical.",
    ],
    "world_route_1": [
        "Traverse every known normal route from start to finish.",
        "Push scrolling boundaries in both directions and let new background/metatile states appear.",
        "Do not skip transitions between major areas.",
    ],
    "world_route_2": [
        "Take alternate branches, secrets/bonus paths and revisits that differ from the normal route.",
        "Deliberately expose unusual camera/scroll combinations and return paths.",
    ],
    "common_enemies": [
        "Encounter every common enemy type.",
        "Observe movement/idle/attack/hit/death frames instead of defeating enemies immediately.",
        "Capture projectile/effect states tied to common enemies.",
    ],
    "rare_enemies": [
        "Visit routes/rooms containing uncommon or route-specific enemies.",
        "Wait for rare attack/idle states and record hit/death states where possible.",
    ],
    "bosses_all_phases": [
        "For every boss, observe intro/idle and every reachable phase.",
        "Let every major attack animation play, then capture hit, transition and death/defeat effects.",
        "Do not mark complete if any boss/phase is known to be missing.",
    ],
    "hud_text_status": [
        "Exercise HUD counters at multiple values, dialogs/fonts and status changes.",
        "Open pause/status screens and capture result/summary screens.",
    ],
    "effects_transitions": [
        "Trigger projectiles, particles, doors, fades, flashes, explosions and special effects.",
        "Include level/room transitions and short-lived effects that are easy to miss.",
    ],
    "ending_credits": [
        "Finish the game and let ending sequences play without skipping.",
        "Capture credits and any post-game/result states through their visible variations.",
    ],
}


def _mission_index() -> dict[str, int]:
    return {key: index for index, (key, _, _, _) in enumerate(MISSION_ITEMS)}


def build_plan(manifest_path: Path, capture_dir: Path | None = None) -> dict:
    ensure_manifest(manifest_path)
    data = load_manifest(manifest_path)
    index = _mission_index()
    missions = []
    for key, item in data["missions"].items():
        missions.append({
            "key": key,
            "label": item["label"],
            "group": item["group"],
            "priority": int(item["priority"]),
            "done": bool(item["done"]),
            "last_session": item.get("last_session"),
            "notes": str(item.get("notes", "")),
            "cues": list(MISSION_CUES.get(key, [item["label"]])),
            "order": index.get(key, 999),
        })
    pending = [row for row in missions if not row["done"]]
    pending.sort(key=lambda row: (-row["priority"], row["order"]))
    completed = [row for row in missions if row["done"]]
    status = mission_status(manifest_path)
    ledger = build_ledger(manifest_path, capture_dir) if capture_dir is not None else None
    return {
        "schema": "swir.project002.guided-capture-marathon.v2",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "attestation_required": ATTESTATION,
        "done": status["done"],
        "total": status["total"],
        "percent": status["percent"],
        "release_capture_gate": status["release_capture_gate"],
        "capture_admission_gate": ledger["admission_gate"] if ledger else "NOT_CHECKED",
        "capture_structural_blockers": ledger["structural_blockers"] if ledger else [],
        "capture_fingerprint_sha256": ledger["capture_fingerprint_sha256"] if ledger else None,
        "pending": pending,
        "completed": completed,
        "next": pending[0] if pending else None,
        "important_note": "Missions are completed only by explicit in-game attestation after real MesenCE gameplay, and only when the current capture passes structural integrity admission. Tile-count growth never auto-completes a mission.",
    }


def confirm_mission(
    manifest_path: Path,
    capture_dir: Path,
    mission_key: str,
    *,
    attestation: str,
    notes: str = "",
) -> dict:
    if attestation != ATTESTATION:
        raise ValueError(f"Explicit attestation required: {ATTESTATION}")
    capture = Path(capture_dir)
    if not (capture / "hires.txt").is_file():
        raise ValueError("Capture folder must contain hires.txt")
    data = load_manifest(manifest_path)
    if mission_key not in data["missions"]:
        raise ValueError(f"Unknown mission key: {mission_key}")
    if data["missions"][mission_key]["done"]:
        return {
            "status": "ALREADY_COMPLETE",
            "mission": mission_key,
            "plan": build_plan(manifest_path, capture),
        }

    preflight = assert_capture_admissible(manifest_path, capture)
    audit_note = "Guided Capture Marathon: VERIFIED_IN_GAME; integrity admission PASS; fingerprint=" + preflight["capture_fingerprint_sha256"]
    if notes.strip():
        audit_note += " — " + notes.strip()
    session = record_session(manifest_path, capture, [mission_key], audit_note)
    postflight = build_ledger(manifest_path, capture)
    if postflight["admission_gate"] != "PASS":
        raise RuntimeError("Capture became structurally inadmissible immediately after mission recording")
    plan = build_plan(manifest_path, capture)
    return {
        "status": "RECORDED",
        "mission": mission_key,
        "session": session,
        "capture_integrity": {
            "admission_gate": postflight["admission_gate"],
            "fingerprint_sha256": postflight["capture_fingerprint_sha256"],
            "structural_blockers": postflight["structural_blockers"],
        },
        "stagnating_warning": all(int(value) <= 0 for value in session["delta"].values()),
        "plan": plan,
    }


def write_dashboard(manifest_path: Path, output: Path, capture_dir: Path | None = None) -> Path:
    plan = build_plan(manifest_path, capture_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    cards = []
    for row in plan["pending"]:
        cues = "".join(f"<li>{html.escape(cue)}</li>" for cue in row["cues"])
        cards.append(
            "<section class='mission pending'>"
            f"<h3>{html.escape(row['label'])}</h3>"
            f"<p><b>{row['group']}</b> · priority {row['priority']} · <code>{row['key']}</code></p>"
            f"<ul>{cues}</ul>"
            "</section>"
        )
    for row in plan["completed"]:
        cards.append(
            "<section class='mission done'>"
            f"<h3>✓ {html.escape(row['label'])}</h3>"
            f"<p><b>{row['group']}</b> · verified session {html.escape(str(row.get('last_session') or '—'))}</p>"
            "</section>"
        )
    body = "".join(cards) or "<p>No mission entries.</p>"
    admission = html.escape(plan["capture_admission_gate"])
    structural = ", ".join(plan["capture_structural_blockers"]) or "none"
    fingerprint = plan["capture_fingerprint_sha256"] or "not checked"
    output.write_text(
        f"""<!doctype html><html><head><meta charset='utf-8'><title>Project #002 Guided Capture Marathon</title>
<style>body{{font:15px system-ui;max-width:1100px;margin:30px auto;padding:0 22px;background:#0d1117;color:#e6edf3}}.hero,.mission{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:16px;margin:12px 0}}.pending{{border-left:5px solid #f2cc60}}.done{{border-left:5px solid #3fb950}}code{{color:#79c0ff}}li{{margin:5px 0}}</style></head><body>
<div class='hero'><h1>Guided Capture Marathon</h1><h2>{plan['done']}/{plan['total']} missions · {plan['percent']}% capture missions</h2><p>Mission gate: <b>{plan['release_capture_gate']}</b> · Capture admission: <b>{admission}</b></p><p>Structural blockers: {html.escape(structural)}</p><p>Capture fingerprint: <code>{html.escape(fingerprint)}</code></p><p>{html.escape(plan['important_note'])}</p></div>{body}</body></html>""",
        encoding="utf-8",
    )
    output.with_suffix(".json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 guided full-game MesenCE capture marathon")
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan")
    plan.add_argument("manifest", type=Path)
    plan.add_argument("--capture", type=Path)
    confirm = sub.add_parser("confirm")
    confirm.add_argument("manifest", type=Path)
    confirm.add_argument("capture", type=Path)
    confirm.add_argument("mission")
    confirm.add_argument("--attestation", required=True)
    confirm.add_argument("--notes", default="")
    dashboard = sub.add_parser("dashboard")
    dashboard.add_argument("manifest", type=Path)
    dashboard.add_argument("output", type=Path)
    dashboard.add_argument("--capture", type=Path)
    args = parser.parse_args()

    if args.command == "plan":
        print(json.dumps(build_plan(args.manifest, args.capture), indent=2))
        return 0
    if args.command == "confirm":
        print(json.dumps(confirm_mission(args.manifest, args.capture, args.mission, attestation=args.attestation, notes=args.notes), indent=2))
        return 0
    print(write_dashboard(args.manifest, args.output, args.capture))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
