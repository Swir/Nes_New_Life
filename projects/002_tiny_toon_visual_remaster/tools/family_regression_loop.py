from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path

from active_family_workbench import WorkbenchError, resolve_active_family_workbench, write_active_state
from final_regression_cockpit import build_and_write as build_regression
from fullscreen_launch import fullscreen_evidence_status
from hd_art_autopilot import run_autopilot

SCHEMA = "swir.project002.family-regression-loop.v1"


class FamilyLoopError(RuntimeError):
    pass


REPAIR_HINTS = {
    "MISSING_HD": "Reopen the affected high-impact family/editable batch and restore missing HD coverage before re-testing this exact case.",
    "WRONG_PALETTE": "Reopen the active family plus Visual Context evidence; correct palette/context handling, then rebuild and re-test this case.",
    "ANIMATION_SEAM": "Reopen the active Animation Family as one unit; repair transition/seam consistency before re-testing.",
    "TRANSPARENCY": "Repair alpha/transparency in the affected family, then rerun transactional Pixel QA before re-testing.",
    "MAPPING": "Stop art iteration and verify hires.txt mapping preservation plus the affected tile/family mapping before re-testing.",
    "SCALE_OR_FILTER": "Keep artwork unchanged; repair the exact-build fullscreen/scale/filter runtime path and re-test.",
    "CAPTURE_GAP": "Return to Capture Review Director and gather the missing real gameplay state before further art claims.",
    "OTHER": "Inspect the recorded failure notes, repair the exact current-build defect, then re-test the same regression case first.",
}


def _safe_family(kit: Path) -> dict | None:
    try:
        result = resolve_active_family_workbench(kit)
        write_active_state(result, kit)
        return {
            "status": result.get("status"),
            "family": result.get("family"),
            "priority": result.get("priority"),
            "members": result.get("members"),
            "board": result.get("board"),
            "editable_dir": result.get("editable_dir"),
            "editable_files": result.get("editable_files", []),
        }
    except WorkbenchError:
        return None


def decide_next(regression: dict, fullscreen: dict, active_family: dict | None) -> dict:
    if fullscreen.get("gate") != "PASS":
        return {
            "state": "FULLSCREEN_EVIDENCE_REQUIRED",
            "action": "Re-run the verified-fullscreen playtest for this exact runtime build before recording regression evidence.",
            "launcher": "Build_HD_Playtest.bat",
        }

    next_case = regression.get("next_case")
    counts = regression.get("counts", {})
    if next_case and next_case.get("state") == "FAIL":
        category = str(next_case.get("failure_category") or "OTHER").upper()
        return {
            "state": "REGRESSION_REPAIR_REQUIRED",
            "action": REPAIR_HINTS.get(category, REPAIR_HINTS["OTHER"]),
            "launcher": "Finish_Family_And_Playtest.bat" if category != "CAPTURE_GAP" else "Capture_Review_Director.bat",
            "regression_case": next_case,
            "active_family": active_family,
        }

    if next_case:
        return {
            "state": "REGRESSION_VERIFICATION_REQUIRED",
            "action": "Verify this exact next FAIL-first/PENDING/STALE case in real MesenCE. Record PASS only after visual confirmation; record FAIL with a defect category otherwise.",
            "launcher": "Final_Regression_Cockpit.bat",
            "regression_case": next_case,
            "active_family": active_family,
        }

    if int(counts.get("PASS", 0) or 0) == int(regression.get("total", 0) or 0) and regression.get("gate") == "PASS":
        return {
            "state": "CURRENT_BUILD_REGRESSION_PASS",
            "action": "The exact current runtime is 10/10 regression-PASS. Prepare/resume the next highest-impact family only if captured art still remains.",
            "launcher": "Evidence_Bound_Art_Handoff.bat",
            "active_family": active_family,
        }

    raise FamilyLoopError("Regression cockpit produced an unsupported state.")


def _write_outputs(result: dict, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "FAMILY_REGRESSION_LOOP.json"
    html_path = output_dir / "FAMILY_REGRESSION_LOOP.html"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    decision = result["decision"]
    case = decision.get("regression_case") or {}
    family = result.get("active_family") or {}
    autopilot = result.get("next_art_autopilot") or {}
    document = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><title>Family Regression Loop</title>
<style>body{{font:15px system-ui;max-width:1250px;margin:28px auto;padding:0 22px;background:#0d1117;color:#e6edf3}}.card{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:18px;margin:14px 0}}code{{color:#79c0ff}}.ok{{color:#3fb950}}.warn{{color:#d29922}}</style></head><body>
<h1>Project #002 — Family → QA → Fullscreen → Regression Loop</h1>
<div class='card'><h2>{html.escape(decision['state'])}</h2><p>Runtime fingerprint: <code>{html.escape(str(result['runtime_fingerprint']))}</code></p><p>Fullscreen: <b>{html.escape(str(result['fullscreen']['gate']))}</b> · Regression PASS {result['regression']['counts']['PASS']}/{result['regression']['total']}</p><p><b>DO THIS NEXT:</b> {html.escape(decision['action'])}</p><p>Recommended launcher: <code>{html.escape(decision['launcher'])}</code></p></div>
<div class='card'><h2>Exact next regression target</h2><p>{html.escape(str(case.get('label', 'No remaining regression case.')))}</p><p>State: {html.escape(str(case.get('state', '—')))} · Category: {html.escape(str(case.get('failure_category', '—')))}</p></div>
<div class='card'><h2>Active / next family</h2><p>{html.escape(str(family.get('family', 'No active PLAYER/ENEMY/BOSS family resolved.')))}</p><p>Priority: {html.escape(str(family.get('priority', '—')))} · members {html.escape(str(family.get('members', '—')))}</p><p>Art autopilot: {html.escape(str(autopilot.get('status', 'NOT_RUN')))}</p></div>
<div class='card'><p>This director never records a regression PASS, never edits Gate A-D and never embeds ROM/capture pixels. Human in-game verification remains authoritative.</p></div>
</body></html>"""
    html_path.write_text(document, encoding="utf-8")
    return {"json": json_path.name, "dashboard": html_path.name}


def run_loop(project_root: Path, capture: Path, runtime_pack: Path, *, prepare_next_family: bool = False, batch_size: int = 30) -> dict:
    root = Path(project_root)
    capture = Path(capture)
    runtime = Path(runtime_pack)
    manifest = root / "FINAL_REGRESSION.json"
    regression = build_regression(manifest, runtime, root / "Reports" / "FinalRegressionCockpit")
    fullscreen = fullscreen_evidence_status(runtime, root / "Reports" / "FullscreenPlaytest" / "FULLSCREEN_PLAYTEST.json")
    kit = root / "Artwork" / "CurrentImpactSprint"
    active = _safe_family(kit) if kit.is_dir() else None
    decision = decide_next(regression, fullscreen, active)

    autopilot = None
    if prepare_next_family and decision["state"] == "CURRENT_BUILD_REGRESSION_PASS":
        autopilot = run_autopilot(root, capture, batch_size=max(1, int(batch_size)))
        if autopilot.get("allowed"):
            active = _safe_family(kit) if kit.is_dir() else None
            if active:
                decision = {
                    "state": "NEXT_FAMILY_READY",
                    "action": "Open the exact active family board/editable folder, redraw the family as one unit, then use Finish Family + Playtest again.",
                    "launcher": "Finish_Family_And_Playtest.bat",
                    "active_family": active,
                }
            elif autopilot.get("status") == "CAPTURED_ART_COMPLETE":
                decision = {
                    "state": "CAPTURED_ART_COMPLETE",
                    "action": "No captured high-impact art remains. Continue missing capture evidence if Gate A is incomplete; otherwise proceed toward final release readiness.",
                    "launcher": "Capture_Review_Director.bat",
                }

    result = {
        "schema": SCHEMA,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "runtime_fingerprint": regression.get("pack_fingerprint"),
        "fullscreen": {
            "gate": fullscreen.get("gate"),
            "verified": fullscreen.get("fullscreen_verified"),
            "fingerprint_matches": fullscreen.get("fingerprint_matches"),
        },
        "regression": {
            "gate": regression.get("gate"),
            "total": regression.get("total"),
            "counts": regression.get("counts", {}),
            "next_case": regression.get("next_case"),
        },
        "active_family": active,
        "next_art_autopilot": None if autopilot is None else {
            "status": autopilot.get("status"),
            "allowed": autopilot.get("allowed"),
            "capture_fingerprint_sha256": autopilot.get("capture_fingerprint_sha256"),
            "visual_completion": autopilot.get("visual_completion", {}),
            "sprint": autopilot.get("sprint"),
        },
        "decision": decision,
        "roadmap_policy": "Tooling never changes Gate A-D. Regression PASS remains explicit human evidence for the exact runtime fingerprint.",
        "privacy_contract": {"metadata_only": True, "rom_bytes": False, "save_states": False, "capture_pixels": False, "emulator_binaries": False, "absolute_local_paths": False},
    }
    result["outputs"] = _write_outputs(result, root / "Reports" / "FamilyRegressionLoop")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 closed family redraw -> QA -> fullscreen -> regression -> next-family loop")
    parser.add_argument("project_root", type=Path)
    parser.add_argument("capture", type=Path)
    parser.add_argument("runtime_pack", type=Path)
    parser.add_argument("--prepare-next-family", action="store_true")
    parser.add_argument("--batch-size", type=int, default=30)
    args = parser.parse_args()
    result = run_loop(args.project_root, args.capture, args.runtime_pack, prepare_next_family=args.prepare_next_family, batch_size=max(1, args.batch_size))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
