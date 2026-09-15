from __future__ import annotations

import argparse
import hashlib
import html
import json
from datetime import datetime, timezone
from pathlib import Path

from final_release_director import final_release_audit, write_final_dashboard

SCHEMA = "swir.project002.release-finalization-director.v1"

EVIDENCE_CANDIDATES = {
    "capture": ("CAPTURE_MISSIONS.json", "Reports/CaptureMissionControl/CAPTURE_MISSIONS.json"),
    "queue": ("Artwork/ART_QUEUE.csv",),
    "visual_review": ("Artwork/VISUAL_CONTEXT_REVIEW.csv",),
    "art_qa": (
        "Reports/ArtQA/ART_QA_RESULT.json",
        "Reports/TransactionalArtCommit/ART_QA_RESULT.json",
        "ModernizedPack/ART_QA_RESULT.json",
    ),
    "regression": ("FINAL_REGRESSION.json",),
    "fullscreen": ("Reports/FullscreenPlaytest/FULLSCREEN_PLAYTEST.json",),
}

STAGE_ROUTES = {
    "HD PACK STRUCTURE": ("REPAIR_HD_STRUCTURE", "Regression_Mapping_Repair.bat"),
    "CAPTURE COVERAGE": ("COMPLETE_CAPTURE", "Guided_Capture_Marathon.bat"),
    "FINAL ART": ("FINISH_FINAL_ART", "High_Impact_Art_Sprint.bat"),
    "VISUAL CONTEXT": ("REFRESH_VISUAL_CONTEXT", "Continue_HD_Art_Session.bat"),
    "PIXEL QA": ("REFRESH_PIXEL_QA", "Finish_High_Impact_Art_Sprint.bat"),
    "VERIFIED FULLSCREEN": ("REFRESH_FULLSCREEN", "Build_HD_Playtest.bat"),
    "FINAL REGRESSION": ("COMPLETE_FINAL_REGRESSION", "Auto_Continue_Final_Regression.bat"),
}


class ReleaseFinalizationError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_evidence(project_root: Path) -> dict[str, Path]:
    root = Path(project_root)
    resolved: dict[str, Path] = {}
    for key, candidates in EVIDENCE_CANDIDATES.items():
        paths = [root / item for item in candidates]
        resolved[key] = next((item for item in paths if item.is_file()), paths[0])
    return resolved


def build_plan(project_root: Path, pack: Path) -> dict:
    root = Path(project_root)
    pack = Path(pack)
    evidence = resolve_evidence(root)
    audit = final_release_audit(
        pack,
        evidence["capture"],
        evidence["queue"],
        evidence["art_qa"],
        evidence["regression"],
        evidence["visual_review"],
        evidence["fullscreen"],
    )

    evidence_status = {
        key: {
            "exists": value.is_file(),
            "path": value.relative_to(root).as_posix() if value.is_relative_to(root) else value.name,
        }
        for key, value in evidence.items()
    }

    if audit["release_gate"] == "PASS":
        state = "PACKAGE_READY"
        launcher = None
        next_action = "All seven exact-build release stages PASS. Create the ROM-free gated ZIP and release manifest now."
    else:
        stage = audit.get("next_stage") or {}
        name = str(stage.get("name") or "")
        route = STAGE_ROUTES.get(name)
        if not route:
            raise ReleaseFinalizationError(f"No safe finalization route for blocking stage: {name or 'unknown'}")
        state, launcher = route
        next_action = f"Run {launcher} for the first blocking release stage ({name}), then re-run finalization against the resulting exact build."

    return {
        "schema": SCHEMA,
        "generated_utc": _now(),
        "state": state,
        "pack_fingerprint": audit["pack_fingerprint"],
        "release_gate": audit["release_gate"],
        "launcher": launcher,
        "next_stage": audit.get("next_stage"),
        "next_action": next_action,
        "evidence": evidence_status,
        "blockers": audit.get("blockers", []),
        "stages": audit.get("stages", []),
        "policy": (
            "Finalization never weakens an evidence gate. Packaging is allowed only after structure, full capture, final art, "
            "Visual Context, exact-build Pixel QA, verified fullscreen and 10/10 exact-build regression all PASS."
        ),
    }


def write_outputs(plan: dict, output_dir: Path) -> dict:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "RELEASE_FINALIZATION.json"
    html_path = output / "RELEASE_FINALIZATION.html"
    json_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    rows = "".join(
        f"<tr><td>{html.escape(str(stage.get('gate') or ''))}</td><td>{html.escape(str(stage.get('name') or ''))}</td><td>{html.escape(str(stage.get('summary') or ''))}</td></tr>"
        for stage in plan.get("stages", [])
    )
    blockers = "".join(f"<li>{html.escape(str(item))}</li>" for item in plan.get("blockers", [])) or "<li>None</li>"
    html_path.write_text(
        "<!doctype html><html><head><meta charset='utf-8'><title>Release Finalization Director</title>"
        "<style>body{font:15px system-ui;max-width:1100px;margin:30px auto;padding:0 22px;background:#0d1117;color:#e6edf3}.card{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:18px;margin:14px 0}table{width:100%;border-collapse:collapse}td,th{padding:8px;border-bottom:1px solid #30363d;text-align:left}code{color:#79c0ff}.warn{color:#f2cc60}</style></head><body>"
        "<h1>Project #002 — Release Finalization Director</h1>"
        f"<div class='card'><h2>{html.escape(plan['state'])}</h2><p>Exact fingerprint: <code>{html.escape(plan['pack_fingerprint'])}</code></p><p><b>DO THIS NEXT:</b> {html.escape(plan['next_action'])}</p><p class='warn'>{html.escape(plan['policy'])}</p></div>"
        f"<div class='card'><h2>Seven release stages</h2><table><tr><th>Gate</th><th>Stage</th><th>Evidence</th></tr>{rows}</table></div>"
        f"<div class='card'><h2>Blockers</h2><ul>{blockers}</ul></div></body></html>",
        encoding="utf-8",
    )
    return {"json": str(json_path), "dashboard": str(html_path)}


def write_release_manifest(plan_path: Path, zip_path: Path, output_path: Path) -> dict:
    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    if plan.get("state") != "PACKAGE_READY" or plan.get("release_gate") != "PASS":
        raise ReleaseFinalizationError("Release manifest cannot be written unless the saved finalization plan is PACKAGE_READY/PASS.")
    archive = Path(zip_path)
    if not archive.is_file():
        raise ReleaseFinalizationError(f"Release ZIP does not exist: {archive}")
    manifest = {
        "schema": "swir.project002.release-manifest.v1",
        "generated_utc": _now(),
        "release_gate": "PASS",
        "pack_fingerprint": plan["pack_fingerprint"],
        "zip_name": archive.name,
        "zip_sha256": _sha256(archive),
        "zip_bytes": archive.stat().st_size,
        "rom_included": False,
        "save_states_included": False,
        "emulator_binary_included": False,
        "policy": "Public artifact contains only the gated HD Pack payload produced by package_hd_pack; the user's ROM remains local.",
    }
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 exact-build release finalization director")
    sub = parser.add_subparsers(dest="command", required=True)
    plan_cmd = sub.add_parser("plan")
    plan_cmd.add_argument("project_root", type=Path)
    plan_cmd.add_argument("pack", type=Path)
    plan_cmd.add_argument("--output", type=Path, required=True)
    manifest_cmd = sub.add_parser("manifest")
    manifest_cmd.add_argument("plan", type=Path)
    manifest_cmd.add_argument("zip", type=Path)
    manifest_cmd.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "plan":
        result = build_plan(args.project_root, args.pack)
        result["outputs"] = write_outputs(result, args.output)
    else:
        result = write_release_manifest(args.plan, args.zip, args.output)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
