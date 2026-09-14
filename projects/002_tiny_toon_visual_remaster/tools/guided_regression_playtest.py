from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path

from final_regression_cockpit import FAILURE_CATEGORIES, cockpit_status, record_case_result, write_dashboard
from release_candidate import REGRESSION_CASES, pack_fingerprint

SCHEMA = "swir.project002.guided-regression-playtest.v1"

CASE_GUIDANCE = {
    "boot_title_menu": {
        "route": "Cold boot -> title -> all menu choices -> return/back paths.",
        "cues": [
            "Watch title/logo edges, menu cursor animation, palette swaps and text alignment.",
            "Trigger every selectable menu state at least once.",
            "Check transition frames entering and leaving gameplay."],
    },
    "player_movement": {
        "route": "Reach a safe flat area and deliberately cycle every locomotion state.",
        "cues": [
            "Idle long enough to see the full idle loop.",
            "Walk/run both directions; crouch; jump; apex/fall; land against contrasting backgrounds.",
            "Look for frame-to-frame seams, wrong palettes, alpha halos and unmapped fallback tiles."],
    },
    "player_actions_damage_death": {
        "route": "Use every player action, then intentionally take damage and lose a life.",
        "cues": [
            "Exercise attack/action frames and direction variants.",
            "Observe invulnerability flicker without treating intentional ROM flicker as an HD defect.",
            "Verify hit/death transitions and restart/respawn presentation."],
    },
    "world_route_1": {
        "route": "Traverse the primary route continuously, including camera boundaries and vertical/horizontal scrolling.",
        "cues": [
            "Pause visually at new backgrounds/tilesets and scrolling boundaries.",
            "Look for original-resolution holes, repeated-tile discontinuities and palette-context errors.",
            "Verify doors/exits and level-to-level transitions."],
    },
    "world_route_2": {
        "route": "Take alternate paths, secrets, revisits and uncommon transitions not covered by the primary route.",
        "cues": [
            "Intentionally revisit earlier areas where palette/context may differ.",
            "Trigger optional rooms/routes and uncommon camera transitions.",
            "Treat any uncaptured HD fallback as CAPTURE_GAP, not an art PASS."],
    },
    "enemies": {
        "route": "Encounter common and rare enemies and keep each alive long enough to expose its state cycle.",
        "cues": [
            "Observe movement/idle/attack/projectile states where applicable.",
            "Trigger hit and death states for every enemy family seen.",
            "Check mirrored/directional variants and palettes against multiple backgrounds."],
    },
    "bosses": {
        "route": "Play every boss from intro through defeat, deliberately allowing multiple attack cycles/phases.",
        "cues": [
            "Do not defeat bosses immediately; expose every attack/phase you can legitimately trigger.",
            "Verify hit flashes, death/effect frames, arena background and phase palette changes.",
            "Any unseen phase is a capture blocker, not something to infer from neighboring frames."],
    },
    "hud_text_status": {
        "route": "Exercise HUD changes, counters, dialog/text, pause/status and result screens.",
        "cues": [
            "Change counters/health/score so multiple digit combinations render.",
            "Open pause/status screens and all dialog/result states encountered.",
            "Check font edges, icons, transparency and consistent 4x treatment."],
    },
    "effects_transitions": {
        "route": "Deliberately trigger projectiles, impacts, particles, doors, fades and special transitions.",
        "cues": [
            "Watch short-lived frames; repeat events if necessary.",
            "Check alpha edges and effect palettes over both light and dark backgrounds.",
            "Confirm doors/fades/special transitions do not expose mixed-resolution frames."],
    },
    "ending_credits": {
        "route": "Complete the game path through ending, credits and any post-game state.",
        "cues": [
            "Let every credits/ending screen remain visible long enough for complete inspection.",
            "Verify scrolling text, portraits/backgrounds and transitions.",
            "Check post-game return/restart states if the game exposes them."],
    },
}

FAILURE_ROUTING = {
    "MISSING_HD": "Return to capture/art coverage for the visible missing HD tile(s), then rebuild and re-run this same case.",
    "WRONG_PALETTE": "Open Visual Context / active family review for the affected palette context, repair it, rebuild, then re-run this case.",
    "ANIMATION_SEAM": "Return to the active animation-family sprint and redraw the family as a sequence, then transactional QA + re-test.",
    "TRANSPARENCY": "Repair alpha/canvas edges in the responsible art family and require Pixel QA before re-testing.",
    "MAPPING": "Inspect hires.txt mapping provenance; do not paper over mapping defects with artwork. Restore mapping correctness, then rebuild.",
    "SCALE_OR_FILTER": "Restore the required 4x HD-pack/runtime presentation and verified fullscreen path before recording evidence.",
    "CAPTURE_GAP": "Return to Capture Review Director / Guided Capture Marathon and gather the missing real gameplay evidence before art work.",
    "OTHER": "Record precise notes, isolate the responsible capture/art/runtime component, fix it, then re-run the exact same case.",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_session(manifest: Path, pack: Path) -> dict:
    status = cockpit_status(manifest, pack)
    current_fp = pack_fingerprint(pack)
    if status["pack_fingerprint"] != current_fp:
        raise ValueError("Regression cockpit fingerprint changed during session planning.")
    case = status.get("next_case")
    if case is None:
        return {
            "schema": SCHEMA,
            "generated_utc": _now(),
            "state": "REGRESSION_COMPLETE",
            "pack_fingerprint": current_fp,
            "counts": status["counts"],
            "next_case": None,
            "next_action": "All 10 cases PASS for this exact runtime fingerprint. Continue to Final Release Gate.",
        }
    guide = CASE_GUIDANCE[case["key"]]
    state = "REPAIR_FAILED_CASE" if case["state"] == "FAIL" else "PLAYTEST_CASE_REQUIRED"
    action = FAILURE_ROUTING.get(case.get("failure_category", ""), "") if case["state"] == "FAIL" else "Launch this exact build in verified fullscreen MesenCE and perform only this case before recording PASS/FAIL."
    return {
        "schema": SCHEMA,
        "generated_utc": _now(),
        "state": state,
        "pack_fingerprint": current_fp,
        "counts": status["counts"],
        "next_case": {
            "order": case["order"],
            "key": case["key"],
            "label": case["label"],
            "prior_state": case["state"],
            "failure_category": case.get("failure_category", ""),
            "failure_notes": case.get("failure_notes", ""),
            "route": guide["route"],
            "cues": guide["cues"],
        },
        "next_action": action,
        "policy": "No regression case can auto-PASS. PASS/FAIL must be explicitly recorded after real MesenCE verification on this exact fingerprint.",
    }


def record(manifest: Path, pack: Path, case_key: str, result: str, *, category: str = "OTHER", notes: str = "", failure_notes: str = "") -> dict:
    before = build_session(manifest, pack)
    expected = before.get("next_case")
    if expected is None:
        raise ValueError("All regression cases already PASS for this exact build.")
    if case_key != expected["key"]:
        raise ValueError(f"Fail-closed ordering: next authoritative case is {expected['key']}, not {case_key}.")
    expected_fp = before["pack_fingerprint"]
    actual_fp = pack_fingerprint(pack)
    if actual_fp != expected_fp:
        raise ValueError("Runtime fingerprint changed after the guided case was planned; discard this observation and re-plan.")
    evidence = record_case_result(manifest, case_key, pack, result, notes=notes, failure_category=category, failure_notes=failure_notes)
    after = build_session(manifest, pack)
    return {"recorded": evidence, "session": after}


def write_outputs(session: dict, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "GUIDED_REGRESSION_PLAYTEST.json"
    html_path = output_dir / "GUIDED_REGRESSION_PLAYTEST.html"
    json_path.write_text(json.dumps(session, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    case = session.get("next_case")
    if case:
        cues = "".join(f"<li>{html.escape(c)}</li>" for c in case["cues"])
        case_html = f"<h2>Case {case['order']}/10 — {html.escape(case['label'])}</h2><p><code>{html.escape(case['key'])}</code> · prior {html.escape(case['prior_state'])}</p><p><b>Route:</b> {html.escape(case['route'])}</p><ul>{cues}</ul>"
    else:
        case_html = "<h2>10/10 exact-build regression complete</h2>"
    counts = session["counts"]
    document = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><title>Guided Regression Playtest</title><style>body{{font:15px system-ui;max-width:1100px;margin:28px auto;padding:0 22px;background:#0d1117;color:#e6edf3}}.card{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:18px;margin:14px 0}}code{{color:#79c0ff}}.warn{{color:#f2cc60}}</style></head><body><h1>Project #002 — Guided Exact-Build Regression</h1><div class='card'><p>Fingerprint: <code>{html.escape(session['pack_fingerprint'])}</code></p><p>PASS {counts['PASS']} · FAIL {counts['FAIL']} · STALE {counts['STALE']} · PENDING {counts['PENDING']}</p><p class='warn'>{html.escape(session.get('policy',''))}</p></div><div class='card'>{case_html}</div><div class='card'><h2>DO THIS NEXT</h2><p>{html.escape(session['next_action'])}</p></div></body></html>"""
    html_path.write_text(document, encoding="utf-8")
    return {"json": str(json_path), "dashboard": str(html_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 guided exact-build final regression director")
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan"); plan.add_argument("manifest", type=Path); plan.add_argument("pack", type=Path); plan.add_argument("--output", type=Path, required=True)
    rec = sub.add_parser("record"); rec.add_argument("manifest", type=Path); rec.add_argument("pack", type=Path); rec.add_argument("case"); rec.add_argument("result", choices=("PASS","FAIL")); rec.add_argument("--category", choices=FAILURE_CATEGORIES, default="OTHER"); rec.add_argument("--notes", default=""); rec.add_argument("--failure-notes", default=""); rec.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "plan":
        session = build_session(args.manifest, args.pack)
        outputs = write_outputs(session, args.output)
        result = {"session": session, "outputs": outputs}
    else:
        result = record(args.manifest, args.pack, args.case, args.result, category=args.category, notes=args.notes, failure_notes=args.failure_notes)
        result["outputs"] = write_outputs(result["session"], args.output)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
