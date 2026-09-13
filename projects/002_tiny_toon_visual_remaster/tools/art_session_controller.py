from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from art_sprint_kit import finish_sprint
from high_impact_art_sprint import prepare_high_impact_sprint
from visual_completion_matrix import build_and_write as build_visual_completion


def decide_next(*, qa_gate: str, mapping_preserved: bool, captured_unfinished: int, blocking_items: int) -> dict:
    if qa_gate != "PASS" or not mapping_preserved:
        return {
            "status": "BLOCKED_QA",
            "continue_art": False,
            "next_action": "Fix Pixel QA or hires.txt mapping preservation before preparing another art batch.",
        }
    if blocking_items > 0:
        return {
            "status": "BLOCKED_MATRIX",
            "continue_art": False,
            "next_action": "Resolve invalid/classification blockers reported by Visual Completion Matrix before continuing.",
        }
    if captured_unfinished <= 0:
        return {
            "status": "CAPTURED_ART_COMPLETE",
            "continue_art": False,
            "next_action": "Captured art backlog is clear. Continue missing gameplay capture or proceed to exact-build regression if Gate A is complete.",
        }
    return {
        "status": "NEXT_BATCH_READY",
        "continue_art": True,
        "next_action": "A fresh exact high-impact batch was prepared from the post-QA workspace state.",
    }


def run_cycle(project_root: Path, source_pack: Path, *, batch_size: int = 30, overwrite_output: bool = True) -> dict:
    root = Path(project_root)
    source_pack = Path(source_pack)
    artwork = root / "Artwork"
    workspace = artwork / "MasterWorkspace"
    kit = artwork / "CurrentImpactSprint"
    queue = artwork / "ART_QUEUE.csv"
    reports = root / "Reports" / "VisualCompletion"
    output_pack = root / "Build" / "HighImpactCandidate"

    if not (kit / "ART_SPRINT_KIT.json").is_file():
        raise FileNotFoundError("CurrentImpactSprint manifest is missing; prepare a sprint before finishing an art session.")

    finish = finish_sprint(source_pack, workspace, kit, output_pack, overwrite=overwrite_output)
    qa_gate = str(finish.get("qa_gate", "FAIL"))
    mapping_preserved = bool(finish.get("mapping_preserved", False))

    matrix = build_visual_completion(
        output_pack,
        reports,
        queue=queue if queue.is_file() else None,
        workspace=workspace,
        batch_size=max(1, int(batch_size)),
    )
    captured_unfinished = int(matrix.get("captured_unfinished", 0))
    blocking_items = int(matrix.get("blocking_items", 0))
    decision = decide_next(
        qa_gate=qa_gate,
        mapping_preserved=mapping_preserved,
        captured_unfinished=captured_unfinished,
        blocking_items=blocking_items,
    )

    sprint = None
    if decision["continue_art"]:
        # The finished kit is archived locally before the next exact batch is generated.
        archive_root = artwork / "SprintArchive"
        archive_root.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        archived = archive_root / f"ImpactSprint_{stamp}"
        if archived.exists():
            shutil.rmtree(archived)
        shutil.move(str(kit), str(archived))
        sprint = prepare_high_impact_sprint(
            output_pack,
            workspace,
            kit,
            reports,
            queue=queue if queue.is_file() else None,
            batch_size=max(1, int(batch_size)),
            overwrite=False,
        )
        decision["status"] = "NEXT_BATCH_READY" if sprint.get("status") == "READY" else "NEXT_BATCH_PARTIAL"
        decision["archive"] = archived.name

    result = {
        "schema": "swir.project002.art-session-controller.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": decision["status"],
        "qa_gate": qa_gate,
        "mapping_preserved": mapping_preserved,
        "captured_unfinished": captured_unfinished,
        "blocking_items": blocking_items,
        "matrix_weighted_percent": matrix.get("overall_weighted_percent", 0),
        "next_batch_count": len(matrix.get("next_batch", [])),
        "sprint": None if sprint is None else {
            "status": sprint.get("status"),
            "exported": sprint.get("exported", 0),
            "missing": sprint.get("missing", 0),
        },
        "next_action": decision["next_action"],
        "roadmap_policy": "This controller never edits Gate A-D; only real gameplay/art/QA evidence may change release progress.",
    }
    out = root / "Reports" / "ArtSessionController"
    out.mkdir(parents=True, exist_ok=True)
    (out / "ART_SESSION_CONTROLLER.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 finish-QA-refresh-next-batch art session controller")
    parser.add_argument("project_root", type=Path)
    parser.add_argument("source_pack", type=Path)
    parser.add_argument("--batch-size", type=int, default=30)
    args = parser.parse_args()
    result = run_cycle(args.project_root, args.source_pack, batch_size=max(1, args.batch_size))
    print(json.dumps(result, indent=2))
    return 0 if result["status"] not in {"BLOCKED_QA", "BLOCKED_MATRIX"} else 3


if __name__ == "__main__":
    raise SystemExit(main())
