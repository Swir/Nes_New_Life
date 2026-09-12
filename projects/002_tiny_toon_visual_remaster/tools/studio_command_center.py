from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from animation_workbench import write_contact_sheets, write_dashboard as write_animation_dashboard
from bound_art_qa import audit_bound_art_apply
from capture_gap_planner import build_capture_queue, write_outputs as write_capture_gap_outputs
from capture_mission_control import ensure_manifest, mission_status, record_session, write_dashboard as write_capture_dashboard
from final_art_priority import write_priority_board
from hd_readiness import package_hd_pack
from rapid_hd_playtest import build_playtest, default_mesence_hdpacks
from release_candidate import audit_release_candidate, ensure_regression_manifest, write_release_dashboard
from visual_context_audit import write_dashboard as write_visual_context_dashboard


@dataclass(frozen=True)
class EvidencePaths:
    root: Path
    capture_manifest: Path
    regression_manifest: Path
    art_queue: Path
    visual_review: Path
    animation_review: Path
    art_qa: Path
    reports: Path
    release_dir: Path


def evidence_paths(project_root: Path) -> EvidencePaths:
    root = Path(project_root)
    reports = root / "Reports"
    artwork = root / "Artwork"
    return EvidencePaths(
        root=root,
        capture_manifest=root / "CAPTURE_MISSIONS.json",
        regression_manifest=root / "FINAL_REGRESSION.json",
        art_queue=artwork / "ART_QUEUE.csv",
        visual_review=artwork / "VISUAL_CONTEXT_REVIEW.csv",
        animation_review=artwork / "ANIMATION_FAMILY_REVIEW.csv",
        art_qa=reports / "ArtQA" / "ART_QA_RESULT.json",
        reports=reports,
        release_dir=root / "Release",
    )


def initialize_project_evidence(project_root: Path) -> EvidencePaths:
    paths = evidence_paths(project_root)
    paths.reports.mkdir(parents=True, exist_ok=True)
    paths.release_dir.mkdir(parents=True, exist_ok=True)
    paths.art_queue.parent.mkdir(parents=True, exist_ok=True)
    ensure_manifest(paths.capture_manifest)
    ensure_regression_manifest(paths.regression_manifest)
    return paths


def record_capture_progress(project_root: Path, capture_dir: Path, *, completed: list[str] | None = None, notes: str = "") -> dict:
    paths = initialize_project_evidence(project_root)
    session = record_session(paths.capture_manifest, Path(capture_dir), completed or [], notes)
    dashboard = write_capture_dashboard(paths.capture_manifest, paths.reports / "CAPTURE_MISSION_CONTROL.html")
    return {"session": session, "status": mission_status(paths.capture_manifest), "dashboard": str(dashboard)}


def capture_dashboard(project_root: Path) -> dict:
    paths = initialize_project_evidence(project_root)
    dashboard = write_capture_dashboard(paths.capture_manifest, paths.reports / "CAPTURE_MISSION_CONTROL.html")
    return {"status": mission_status(paths.capture_manifest), "dashboard": str(dashboard)}


def capture_gap_dashboard(project_root: Path, current_capture: Path, *, previous_capture: Path | None = None) -> dict:
    paths = initialize_project_evidence(project_root)
    queue = paths.art_queue if paths.art_queue.is_file() else None
    result = build_capture_queue(
        Path(current_capture),
        queue,
        Path(previous_capture) if previous_capture else None,
        queue,
        paths.capture_manifest,
    )
    outputs = write_capture_gap_outputs(result, paths.reports / "CaptureGapPlanner")
    return {**result, "outputs": outputs}


def visual_context_dashboard(project_root: Path, pack_dir: Path) -> dict:
    paths = initialize_project_evidence(project_root)
    if not paths.art_queue.is_file():
        raise ValueError("ART_QUEUE.csv is missing; group/sync the art queue first")
    return write_visual_context_dashboard(
        Path(pack_dir), paths.art_queue, paths.visual_review, paths.reports / "VisualContext"
    )


def animation_family_dashboard(project_root: Path, pack_dir: Path, *, create_contact_sheets: bool = False) -> dict:
    paths = initialize_project_evidence(project_root)
    if not paths.art_queue.is_file():
        raise ValueError("ART_QUEUE.csv is missing; group/sync the art queue first")
    result = write_animation_dashboard(
        Path(pack_dir), paths.art_queue, paths.animation_review, paths.reports / "AnimationWorkbench"
    )
    if create_contact_sheets:
        result["contact_sheets"] = write_contact_sheets(
            Path(pack_dir), paths.art_queue, paths.reports / "AnimationWorkbench" / "LocalContactSheets"
        )
    return result


def final_art_priority_dashboard(project_root: Path, pack_dir: Path, *, top: int = 20) -> dict:
    paths = initialize_project_evidence(project_root)
    if not paths.art_queue.is_file():
        raise ValueError("ART_QUEUE.csv is missing; group/sync the art queue first")
    workspace = paths.root / "Artwork" / "MasterWorkspace"
    return write_priority_board(
        Path(pack_dir),
        paths.reports / "FinalArtPriority",
        queue=paths.art_queue,
        workspace=workspace if (workspace / "ART_STATE.csv").is_file() else None,
        visual_review=paths.visual_review if paths.visual_review.is_file() else None,
        animation_review=paths.animation_review if paths.animation_review.is_file() else None,
        top=top,
    )


def run_playtest_build(project_root: Path, capture_dir: Path, *, rom_name: str | None = None, hdpacks_root: Path | None = None, deploy: bool = False) -> dict:
    initialize_project_evidence(project_root)
    root = Path(project_root)
    target_root = Path(hdpacks_root) if hdpacks_root else default_mesence_hdpacks()
    return build_playtest(
        Path(capture_dir), root,
        rom_name=rom_name if deploy else None,
        hdpacks_root=target_root if deploy else None,
        keep_backup=True,
    )


def run_bound_art_qa(project_root: Path, source_capture: Path, output_pack: Path) -> dict:
    paths = initialize_project_evidence(project_root)
    workspace = paths.root / "Artwork" / "MasterWorkspace"
    if not (workspace / "MASTER_TILES.json").is_file():
        raise ValueError("MasterWorkspace is missing; cannot prove authorized pixel regions")
    report_dir = paths.art_qa.parent
    report_dir.mkdir(parents=True, exist_ok=True)
    return audit_bound_art_apply(Path(source_capture), Path(output_pack), workspace, report_dir)


def release_audit(project_root: Path, pack_dir: Path) -> dict:
    paths = initialize_project_evidence(project_root)
    result = audit_release_candidate(
        Path(pack_dir), paths.capture_manifest, paths.art_queue, paths.art_qa,
        paths.regression_manifest, paths.visual_review,
    )
    dashboard = write_release_dashboard(result, paths.reports / "ReleaseCandidate")
    result["dashboard"] = str(dashboard)
    return result


def gated_release_package(project_root: Path, pack_dir: Path, output_zip: Path | None = None) -> dict:
    paths = initialize_project_evidence(project_root)
    result = release_audit(paths.root, Path(pack_dir))
    if result["release_gate"] != "PASS":
        raise ValueError("Release packaging blocked by Unified Release Candidate Gate:\n- " + "\n- ".join(result["blockers"]))
    output = Path(output_zip) if output_zip else paths.release_dir / "TinyToon_Visual_Remaster_HD_Pack.zip"
    package_hd_pack(Path(pack_dir), output)
    manifest = {
        "release_gate": result["release_gate"],
        "pack_fingerprint": result["pack_fingerprint"],
        "zip": str(output.resolve()),
        "dashboard": result["dashboard"],
    }
    paths.release_dir.mkdir(parents=True, exist_ok=True)
    (paths.release_dir / "RELEASE_PACKAGE.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
