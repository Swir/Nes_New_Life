from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path


REPORTS = {
    "capture_to_hd": ("CaptureToHDSession", "CAPTURE_TO_HD_SESSION.json"),
    "hd_art_autopilot": ("HDArtAutopilot", "HD_ART_AUTOPILOT.json"),
    "art_session": ("ArtSessionController", "ART_SESSION_CONTROLLER.json"),
    "final_release": ("FinalReleaseReadiness", "FINAL_RELEASE_READINESS.json"),
}


def _load(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def read_production_state(project_root: Path) -> dict:
    root = Path(project_root)
    reports_root = root / "Reports"
    loaded: dict[str, dict | None] = {}
    for key, (folder, name) in REPORTS.items():
        loaded[key] = _load(reports_root / folder / name)
    return loaded


def decide_next(state: dict) -> dict:
    release = state.get("final_release") or {}
    release_gate = str(release.get("release_gate", ""))
    if release_gate == "PASS":
        return {
            "stage": "RELEASE_READY",
            "severity": "ok",
            "launcher": "Final_Release_Gate.bat",
            "next_action": "All exact-build release gates are green. Build the gated ROM-free release ZIP through Final Release Gate.",
        }

    art = state.get("art_session") or {}
    art_status = str(art.get("status", ""))
    if art_status in {"BLOCKED_QA", "BLOCKED_MATRIX"}:
        return {
            "stage": art_status,
            "severity": "block",
            "launcher": "Continue_HD_Art_Session.bat",
            "next_action": str(art.get("next_action") or "Resolve Pixel QA / matrix blockers before another art batch."),
        }
    if art_status in {"NEXT_BATCH_READY", "NEXT_BATCH_PARTIAL"}:
        return {
            "stage": "ART_BATCH_ACTIVE",
            "severity": "work",
            "launcher": "Continue_HD_Art_Session.bat",
            "next_action": "Continue editing CurrentImpactSprint/editable, then finish through the QA-gated art-session controller.",
        }
    if art_status == "CAPTURED_ART_COMPLETE":
        return {
            "stage": "CAPTURED_ART_COMPLETE",
            "severity": "work",
            "launcher": "Full_Capture_To_HD_Autopilot.bat",
            "next_action": str(art.get("next_action") or "Continue missing gameplay capture or proceed to exact-build regression when Gate A is complete."),
        }

    autopilot = state.get("hd_art_autopilot") or {}
    auto_status = str(autopilot.get("status", ""))
    if auto_status.startswith("BLOCKED_"):
        return {
            "stage": auto_status,
            "severity": "block",
            "launcher": "Full_Capture_To_HD_Autopilot.bat",
            "next_action": str(autopilot.get("next_action") or "Repair the blocked capture/art handoff and rerun HD Autopilot."),
        }
    if auto_status in {"HIGH_IMPACT_SPRINT_READY", "HIGH_IMPACT_SPRINT_PARTIAL", "RESUME_EXISTING_SPRINT"}:
        return {
            "stage": "ART_BATCH_ACTIVE",
            "severity": "work",
            "launcher": "Continue_HD_Art_Session.bat",
            "next_action": str(autopilot.get("next_action") or "Complete the current exact High-Impact Art Sprint and run Pixel QA."),
        }
    if auto_status == "CAPTURED_ART_COMPLETE":
        return {
            "stage": "CAPTURED_ART_COMPLETE",
            "severity": "work",
            "launcher": "Full_Capture_To_HD_Autopilot.bat",
            "next_action": str(autopilot.get("next_action") or "Return to missing gameplay capture or exact-build regression."),
        }

    session = state.get("capture_to_hd") or {}
    production = str(session.get("production_decision", ""))
    capture = str(session.get("capture_decision", ""))
    if production == "BLOCK_PRODUCTION":
        return {
            "stage": capture or "CAPTURE_BLOCKED",
            "severity": "block",
            "launcher": "Full_Capture_To_HD_Autopilot.bat",
            "next_action": str(session.get("next_action") or "Fix capture integrity/regression/provenance before production."),
        }
    if production in {"SAFE_INCREMENTAL_ART", "FULL_CAPTURE_READY"}:
        return {
            "stage": "SAFE_CAPTURE_NEEDS_ART_ROUTING",
            "severity": "work",
            "launcher": "Full_Capture_To_HD_Autopilot.bat",
            "next_action": "Capture is admitted to production. Run Full Capture -> HD Autopilot to rebuild the exact matrix and prepare/resume the highest-impact 4x batch.",
        }
    if capture:
        return {
            "stage": capture,
            "severity": "work",
            "launcher": "Full_Capture_To_HD_Autopilot.bat",
            "next_action": str(session.get("next_action") or "Continue the guided capture path."),
        }

    return {
        "stage": "START_CAPTURE_TO_HD_AUTOPILOT",
        "severity": "work",
        "launcher": "Full_Capture_To_HD_Autopilot.bat",
        "next_action": "Run the full guided Capture -> evidence -> acceptance -> promotion -> exact-art autopilot with the legally supplied local ROM.",
    }


def build_cockpit(project_root: Path) -> dict:
    state = read_production_state(project_root)
    decision = decide_next(state)
    result = {
        "schema": "swir.project002.production-cockpit.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "stage": decision["stage"],
        "severity": decision["severity"],
        "launcher": decision["launcher"],
        "next_action": decision["next_action"],
        "capture_to_hd": state.get("capture_to_hd"),
        "hd_art_autopilot": state.get("hd_art_autopilot"),
        "art_session": state.get("art_session"),
        "final_release": state.get("final_release"),
        "roadmap_policy": "Cockpit state never edits Gate A-D; only real local gameplay/art/QA evidence may change release progress.",
        "privacy_contract": {
            "metadata_only": True,
            "rom_bytes": False,
            "save_states": False,
            "capture_pixels": False,
            "emulator_binaries": False,
            "absolute_local_paths": False,
        },
    }
    return result


def write_outputs(result: dict, output_dir: Path) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "PRODUCTION_COCKPIT.json"
    html_path = output_dir / "PRODUCTION_COCKPIT.html"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    stage = html.escape(str(result.get("stage", "UNKNOWN")))
    action = html.escape(str(result.get("next_action", "")))
    launcher = html.escape(str(result.get("launcher", "")))
    doc = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><title>Project #002 Production Cockpit</title>
<style>body{{font:15px system-ui;max-width:1050px;margin:30px auto;padding:0 22px;background:#0d1117;color:#e6edf3}}.card{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:16px;margin:12px 0}}code{{color:#79c0ff}}.ok{{color:#3fb950}}</style></head><body>
<h1>Project #002 — Authoritative Production Cockpit</h1><div class='card'><h2>{stage}</h2><p><b>DO THIS NEXT:</b> {action}</p><p>Recommended launcher: <code>{launcher}</code></p></div>
<div class='card'><p>Metadata-only decision surface. It does not contain ROM bytes, save states, capture pixels, emulator binaries or absolute local paths and it never edits ROADMAP Gate A-D.</p></div></body></html>"""
    html_path.write_text(doc, encoding="utf-8")
    return {"json": str(json_path), "dashboard": str(html_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 authoritative production-state cockpit")
    parser.add_argument("project_root", type=Path)
    args = parser.parse_args()
    result = build_cockpit(args.project_root)
    result["outputs"] = write_outputs(result, args.project_root / "Reports" / "ProductionCockpit")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
