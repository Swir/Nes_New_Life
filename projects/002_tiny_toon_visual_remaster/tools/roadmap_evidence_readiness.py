from __future__ import annotations

import argparse
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path


GATES = ("A", "B", "C", "D")
REPORTS = {
    "capture_acceptance": ("CaptureCoverageAcceptance", "CAPTURE_COVERAGE_ACCEPTANCE.json"),
    "capture_to_hd": ("CaptureToHDSession", "CAPTURE_TO_HD_SESSION.json"),
    "hd_art_autopilot": ("HDArtAutopilot", "HD_ART_AUTOPILOT.json"),
    "art_session": ("ArtSessionController", "ART_SESSION_CONTROLLER.json"),
    "visual_matrix": ("VisualCompletion", "VISUAL_COMPLETION_MATRIX.json"),
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


def _release_stage(release: dict, name: str) -> dict:
    for stage in release.get("stages", []):
        if isinstance(stage, dict) and str(stage.get("name", "")) == name:
            return stage
    return {}


def parse_roadmap(roadmap: Path) -> list[dict]:
    text = Path(roadmap).read_text(encoding="utf-8")
    current_gate = ""
    rows: list[dict] = []
    for raw in text.splitlines():
        heading = re.match(r"^## Gate ([A-D])\b", raw)
        if heading:
            current_gate = heading.group(1)
            continue
        if current_gate not in GATES:
            continue
        item = re.match(r"^- \[([ xX])\] (.+)$", raw)
        if not item:
            continue
        rows.append({
            "gate": current_gate,
            "index": 1 + sum(1 for row in rows if row["gate"] == current_gate),
            "checked": item.group(1).lower() == "x",
            "text": item.group(2).strip(),
        })
    return rows


def load_evidence(project_root: Path) -> dict:
    reports = Path(project_root) / "Reports"
    result: dict[str, dict | None] = {}
    for key, (folder, filename) in REPORTS.items():
        result[key] = _load(reports / folder / filename)
    return result


def _status(status: str, reason: str, source: str = "") -> dict:
    return {"status": status, "reason": reason, "source": source}


def _capture_item(item: dict, evidence: dict) -> dict:
    acceptance = evidence.get("capture_acceptance") or {}
    summary = acceptance.get("mission_summary", {})
    integrity = acceptance.get("capture_integrity", {})
    verified = int(summary.get("verified", 0) or 0)
    total = int(summary.get("total", 0) or 0)
    hard = list(acceptance.get("hard_blockers", []))
    full = acceptance.get("acceptance_gate") == "READY_FOR_GATE_A_REVIEW"
    clean_integrity = (
        integrity.get("admission_gate") == "PASS"
        and int(integrity.get("regression_count", 0) or 0) == 0
        and not integrity.get("structural_blockers")
        and not integrity.get("at_risk_missions")
    )
    text = item["text"].lower()
    if "capture_regression" in text or "repeated captures" in text:
        if clean_integrity and acceptance:
            return _status(
                "READY_FOR_HUMAN_REVIEW",
                "Capture Integrity evidence reports PASS admission with zero structural regressions/at-risk missions. Confirm the real repeated gameplay captures before checking this item.",
                "CaptureCoverageAcceptance",
            )
        if acceptance:
            return _status("BLOCKED", "Capture integrity/regression evidence is not clean yet.", "CaptureCoverageAcceptance")
        return _status("WAITING_LOCAL_EVIDENCE", "Run the real Guided Capture Marathon and acceptance pass first.")
    if full and verified == total and total > 0:
        return _status(
            "READY_FOR_HUMAN_REVIEW",
            f"All {verified}/{total} fingerprint-bound capture missions are VERIFIED_IN_GAME and hard acceptance blockers are clear. This item still needs visual human confirmation in real gameplay.",
            "CaptureCoverageAcceptance",
        )
    if acceptance:
        blocker = hard[0].get("detail") if hard and isinstance(hard[0], dict) else "Capture coverage is incomplete."
        return _status("BLOCKED" if hard else "WAITING_LOCAL_EVIDENCE", f"Capture evidence: {verified}/{total} verified. {blocker}", "CaptureCoverageAcceptance")
    return _status("WAITING_LOCAL_EVIDENCE", "No fingerprint-bound Capture Coverage Acceptance report exists yet.")


def _gate_b_item(item: dict, evidence: dict) -> dict:
    release = evidence.get("final_release") or {}
    capture = evidence.get("capture_to_hd") or {}
    autopilot = evidence.get("hd_art_autopilot") or {}
    art = evidence.get("art_session") or {}
    final_art = _release_stage(release, "FINAL ART")
    visual = _release_stage(release, "VISUAL CONTEXT")
    pixel = _release_stage(release, "PIXEL QA")
    text = item["text"].lower()

    if "promote only" in text:
        if capture.get("production_decision") in {"SAFE_INCREMENTAL_ART", "FULL_CAPTURE_READY"}:
            return _status("READY_FOR_HUMAN_REVIEW", "Capture Production Director admitted the fingerprint-bound capture to production; verify it is the intended latest baseline.", "CaptureToHDSession")
        return _status("WAITING_LOCAL_EVIDENCE", "No safe current capture promotion evidence is available.", "CaptureToHDSession")
    if "resume-safe sync" in text:
        if autopilot.get("status") in {"HIGH_IMPACT_SPRINT_READY", "HIGH_IMPACT_SPRINT_PARTIAL", "RESUME_EXISTING_SPRINT", "CAPTURED_ART_COMPLETE"}:
            return _status("READY_FOR_HUMAN_REVIEW", "HD Art Autopilot reached the art stage without replacing an active sprint. Confirm existing edited masters were preserved.", "HDArtAutopilot")
        return _status("WAITING_LOCAL_EVIDENCE", "Run safe capture promotion and HD Art Autopilot first.", "HDArtAutopilot")
    if "visual_context_review" in text or "visual-context" in text:
        if visual.get("gate") == "PASS":
            return _status("READY_FOR_HUMAN_REVIEW", "Final Release Readiness reports Visual Context PASS for the current build.", "FinalReleaseReadiness")
        return _status("BLOCKED" if visual else "WAITING_LOCAL_EVIDENCE", visual.get("summary", "Visual Context evidence is missing."), "FinalReleaseReadiness")
    if "pixel qa" in text or "preserves `hires.txt`" in text:
        if pixel.get("gate") == "PASS":
            return _status("READY_FOR_HUMAN_REVIEW", "Current-build Pixel QA is PASS. Confirm the exact local candidate and preserved mapping before checking this item.", "FinalReleaseReadiness")
        return _status("BLOCKED" if pixel else "WAITING_LOCAL_EVIDENCE", pixel.get("summary", "Current-build Pixel QA evidence is missing."), "FinalReleaseReadiness")
    if "zero todo" in text or "world/ui/effects" in text or "backlog is exhausted" in text:
        if final_art.get("gate") == "PASS":
            return _status("READY_FOR_HUMAN_REVIEW", "Final Art gate is PASS with the current queue complete/classified.", "FinalReleaseReadiness")
        return _status("BLOCKED" if final_art else "WAITING_LOCAL_EVIDENCE", final_art.get("summary", "Final Art completion evidence is missing."), "FinalReleaseReadiness")
    if "finish through" in text or "work only" in text or "high_impact_art_sprint" in text:
        if art.get("status") in {"NEXT_BATCH_READY", "NEXT_BATCH_PARTIAL", "CAPTURED_ART_COMPLETE"}:
            return _status("READY_FOR_HUMAN_REVIEW", "QA-gated art-session controller has processed the current sprint state. Inspect the local sprint/candidate before approval.", "ArtSessionController")
        return _status("WAITING_LOCAL_EVIDENCE", "A real local High-Impact Art Sprint has not yet produced reviewable completion evidence.", "ArtSessionController")
    return _status("WAITING_LOCAL_EVIDENCE", "This art-production checkbox requires local art/review evidence not safely inferable from metadata alone.")


def _gate_c_item(item: dict, evidence: dict) -> dict:
    release = evidence.get("final_release") or {}
    text = item["text"].lower()
    stage_map = {
        "pixel qa": "PIXEL QA",
        "hires.txt": "HD PACK STRUCTURE",
        "missing referenced": "HD PACK STRUCTURE",
        "4x target": "HD PACK STRUCTURE",
        "fullscreen": "VERIFIED FULLSCREEN",
        "10/10": "FINAL REGRESSION",
        "ten cases": "FINAL REGRESSION",
        "final regression": "FINAL REGRESSION",
        "animation seams": "FINAL REGRESSION",
        "playtest": "VERIFIED FULLSCREEN",
        "mesence automatically": "VERIFIED FULLSCREEN",
    }
    stage_name = next((value for key, value in stage_map.items() if key in text), "")
    if not stage_name:
        return _status("WAITING_LOCAL_EVIDENCE", "This QA checkbox needs explicit local gameplay/build evidence.")
    stage = _release_stage(release, stage_name)
    if stage.get("gate") == "PASS":
        return _status("READY_FOR_HUMAN_REVIEW", f"Exact-build release evidence reports {stage_name} PASS. Confirm the real local run before checking this item.", "FinalReleaseReadiness")
    if stage:
        return _status("BLOCKED", stage.get("summary", f"{stage_name} is not PASS."), "FinalReleaseReadiness")
    return _status("WAITING_LOCAL_EVIDENCE", f"No {stage_name} release evidence exists yet.", "FinalReleaseReadiness")


def _gate_d_item(item: dict, evidence: dict) -> dict:
    release = evidence.get("final_release") or {}
    text = item["text"].lower()
    if not release:
        return _status("WAITING_LOCAL_EVIDENCE", "Final Release Readiness has not been generated for the real candidate build.")
    if "final release readiness director" in text or "final_release_gate" in text:
        if release.get("release_gate") == "PASS":
            return _status("READY_FOR_HUMAN_REVIEW", "Authoritative Final Release Readiness reports PASS for the exact build.", "FinalReleaseReadiness")
        return _status("BLOCKED", "Final Release Readiness is still BLOCKED.", "FinalReleaseReadiness")
    mapping = {
        "capture missions": "CAPTURE COVERAGE",
        "art queue": "FINAL ART",
        "visual completion matrix": "FINAL ART",
        "visual context": "VISUAL CONTEXT",
        "pixel qa": "PIXEL QA",
        "10/10": "FINAL REGRESSION",
        "fullscreen": "VERIFIED FULLSCREEN",
        "runtime pack": "HD PACK STRUCTURE",
        "release zip": None,
        "screenshots/video": None,
    }
    found = next(((key, value) for key, value in mapping.items() if key in text), None)
    if not found:
        return _status("WAITING_LOCAL_EVIDENCE", "Release checkbox needs explicit local release evidence.")
    _, stage_name = found
    if stage_name is None:
        if "release zip" in text and release.get("release_gate") == "PASS":
            return _status("READY_FOR_HUMAN_REVIEW", "Packaging is authorized by the exact-build release gate; confirm the generated ROM-free ZIP before checking.", "FinalReleaseReadiness")
        return _status("WAITING_LOCAL_EVIDENCE", "This item requires a local packaging/media action that metadata cannot perform or infer.")
    stage = _release_stage(release, stage_name)
    if stage.get("gate") == "PASS":
        return _status("READY_FOR_HUMAN_REVIEW", f"Final Release Readiness reports {stage_name} PASS for the exact candidate.", "FinalReleaseReadiness")
    return _status("BLOCKED", stage.get("summary", f"{stage_name} is not PASS."), "FinalReleaseReadiness")


def assess(project_root: Path) -> dict:
    root = Path(project_root)
    items = parse_roadmap(root / "ROADMAP.md")
    evidence = load_evidence(root)
    assessed: list[dict] = []
    for item in items:
        if item["checked"]:
            readiness = _status("ALREADY_CHECKED", "ROADMAP already records this item as complete.")
        elif item["gate"] == "A":
            readiness = _capture_item(item, evidence)
        elif item["gate"] == "B":
            readiness = _gate_b_item(item, evidence)
        elif item["gate"] == "C":
            readiness = _gate_c_item(item, evidence)
        else:
            readiness = _gate_d_item(item, evidence)
        assessed.append({**item, **readiness})

    counts: dict[str, int] = {}
    for row in assessed:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    review = [row for row in assessed if row["status"] == "READY_FOR_HUMAN_REVIEW"]
    blocked = [row for row in assessed if row["status"] == "BLOCKED"]
    waiting = [row for row in assessed if row["status"] == "WAITING_LOCAL_EVIDENCE"]
    if review:
        next_action = f"Review Gate {review[0]['gate']} #{review[0]['index']}: {review[0]['text']} against the real local evidence. Check it manually only if the evidence truly proves it."
    elif blocked:
        next_action = f"Resolve Gate {blocked[0]['gate']} #{blocked[0]['index']} blocker: {blocked[0]['reason']}"
    elif waiting:
        next_action = f"Generate real local evidence for Gate {waiting[0]['gate']} #{waiting[0]['index']}: {waiting[0]['text']}"
    else:
        next_action = "All ROADMAP items are already checked; run Final Release Gate and verify the release artifact."

    return {
        "schema": "swir.project002.roadmap-evidence-readiness.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "roadmap_items": len(assessed),
        "counts": counts,
        "items": assessed,
        "next_action": next_action,
        "roadmap_policy": "READ-ONLY. This director never edits ROADMAP.md and never converts metadata into completion. READY_FOR_HUMAN_REVIEW means only that supporting evidence is present and must still be manually verified against real local gameplay/art/QA.",
        "privacy_contract": {
            "metadata_only": True,
            "rom_bytes": False,
            "save_states": False,
            "capture_pixels": False,
            "emulator_binaries": False,
            "absolute_local_paths": False,
        },
    }


def write_outputs(result: dict, output_dir: Path) -> dict:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "ROADMAP_EVIDENCE_READINESS.json"
    html_path = output / "ROADMAP_EVIDENCE_READINESS.html"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    rows = []
    for item in result["items"]:
        cls = item["status"].lower()
        rows.append(
            "<tr>"
            f"<td>Gate {html.escape(item['gate'])} #{item['index']}</td>"
            f"<td>{html.escape(item['text'])}</td>"
            f"<td class='{cls}'>{html.escape(item['status'])}</td>"
            f"<td>{html.escape(item['reason'])}</td>"
            f"<td><code>{html.escape(item.get('source') or '—')}</code></td>"
            "</tr>"
        )
    counts = " · ".join(f"{html.escape(k)}={v}" for k, v in sorted(result["counts"].items()))
    document = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><title>Project #002 ROADMAP Evidence Readiness</title>
<style>body{{font:15px system-ui;max-width:1500px;margin:28px auto;padding:0 20px;background:#0d1117;color:#e6edf3}}.card{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:16px;margin:12px 0}}table{{width:100%;border-collapse:collapse}}th,td{{padding:9px;border-bottom:1px solid #30363d;text-align:left;vertical-align:top}}.ready_for_human_review{{color:#3fb950;font-weight:700}}.blocked{{color:#f85149;font-weight:700}}.waiting_local_evidence{{color:#d29922}}.already_checked{{color:#79c0ff}}code{{color:#79c0ff}}</style></head><body>
<h1>Project #002 — ROADMAP Evidence Readiness</h1><div class='card'><b>{html.escape(counts)}</b><h3>DO THIS NEXT</h3><p>{html.escape(result['next_action'])}</p><p>{html.escape(result['roadmap_policy'])}</p></div>
<div class='card'><table><tr><th>Item</th><th>ROADMAP requirement</th><th>Evidence state</th><th>Why</th><th>Source</th></tr>{''.join(rows)}</table></div></body></html>"""
    html_path.write_text(document, encoding="utf-8")
    return {"json": str(json_path), "dashboard": str(html_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 read-only Gate A-D evidence readiness director")
    parser.add_argument("project_root", type=Path)
    args = parser.parse_args()
    result = assess(args.project_root)
    result["outputs"] = write_outputs(result, args.project_root / "Reports" / "RoadmapEvidenceReadiness")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
