from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from capture_mission_control import default_manifest  # noqa: E402
from release_candidate import (  # noqa: E402
    REGRESSION_CASES,
    audit_release_candidate,
    complete_regression_case,
    ensure_regression_manifest,
    pack_fingerprint,
    regression_status,
    write_release_dashboard,
)
from visual_context_audit import sync_review  # noqa: E402


class ReleaseCandidateTests(unittest.TestCase):
    @staticmethod
    def _write_pack(folder: Path, color=(30, 60, 120, 255)) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        Image.new("RGBA", (32, 32), color).save(folder / "tiles.png")
        (folder / "hires.txt").write_text(
            "<ver>106\n<scale>4\n<img>tiles.png\n[hero_player]<tile>0,2E,FF16360F,0,0,1,N\n",
            encoding="utf-8",
        )

    @staticmethod
    def _complete_capture(path: Path) -> None:
        data = default_manifest()
        for item in data["missions"].values():
            item["done"] = True
            item["notes"] = "verified in local full-game capture"
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    @staticmethod
    def _write_done_queue(path: Path) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow([
                "priority", "tile_id", "palette", "uses", "conditional_uses", "conditions",
                "status", "art_group", "group_confidence", "notes",
            ])
            writer.writerow([1, "2E", "FF16360F", 1, 1, "hero_player", "DONE", "PLAYER", "high", "final"])

    def _complete_regression(self, manifest: Path, pack: Path) -> None:
        ensure_regression_manifest(manifest)
        for key, _ in REGRESSION_CASES:
            complete_regression_case(manifest, key, pack, f"verified {key}")

    def _green_files(self, root: Path, pack: Path) -> tuple[Path, Path, Path, Path, Path]:
        capture = root / "capture.json"
        queue = root / "queue.csv"
        visual = root / "VISUAL_CONTEXT_REVIEW.csv"
        qa = root / "ART_QA_RESULT.json"
        regression = root / "regression.json"
        self._complete_capture(capture)
        self._write_done_queue(queue)
        sync_review(pack, queue, visual)
        qa.write_text(json.dumps({
            "qa_gate": "PASS",
            "output_pack_fingerprint": pack_fingerprint(pack),
        }), encoding="utf-8")
        self._complete_regression(regression, pack)
        return capture, queue, visual, qa, regression

    def test_all_evidence_passes_single_release_gate(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); pack = root / "pack"; report = root / "report"
            self._write_pack(pack)
            capture, queue, visual, qa, regression = self._green_files(root, pack)
            result = audit_release_candidate(pack, capture, queue, qa, regression, visual)
            self.assertEqual(result["release_gate"], "PASS")
            self.assertEqual(result["visual_context"]["gate"], "PASS")
            self.assertEqual(result["blockers"], [])
            dashboard = write_release_dashboard(result, report)
            self.assertTrue(dashboard.is_file())
            self.assertTrue((report / "RELEASE_CANDIDATE.json").is_file())

    def test_missing_visual_context_review_blocks_release(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); pack = root / "pack"
            self._write_pack(pack)
            capture, queue, _, qa, regression = self._green_files(root, pack)
            result = audit_release_candidate(pack, capture, queue, qa, regression)
            self.assertEqual(result["release_gate"], "BLOCKED")
            self.assertTrue(any("Visual Context Review is missing" in item for item in result["blockers"]))

    def test_art_change_invalidates_qa_regression_and_visual_review(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); pack = root / "pack"
            self._write_pack(pack)
            capture, queue, visual, qa, regression = self._green_files(root, pack)
            old_fingerprint = pack_fingerprint(pack)
            self._write_pack(pack, color=(180, 60, 40, 255))
            self.assertNotEqual(pack_fingerprint(pack), old_fingerprint)
            reg = regression_status(regression, pack)
            self.assertEqual(reg["done_current_build"], 0)
            result = audit_release_candidate(pack, capture, queue, qa, regression, visual)
            self.assertEqual(result["release_gate"], "BLOCKED")
            self.assertFalse(result["art_qa"]["fingerprint_matches"])
            self.assertTrue(any("stale" in blocker.lower() for blocker in result["blockers"]))

    def test_unfinished_or_unassigned_art_blocks_release(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); pack = root / "pack"
            capture = root / "capture.json"; queue = root / "queue.csv"; visual = root / "visual.csv"
            qa = root / "qa.json"; regression = root / "regression.json"
            self._write_pack(pack); self._complete_capture(capture)
            with queue.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle); writer.writerow(["status", "art_group"]); writer.writerow(["TODO", "UNASSIGNED"])
            sync_review(pack, queue, visual)
            qa.write_text(json.dumps({"qa_gate": "PASS", "output_pack_fingerprint": pack_fingerprint(pack)}), encoding="utf-8")
            self._complete_regression(regression, pack)
            result = audit_release_candidate(pack, capture, queue, qa, regression, visual)
            self.assertEqual(result["release_gate"], "BLOCKED")
            self.assertTrue(any("unfinished" in blocker.lower() for blocker in result["blockers"]))
            self.assertTrue(any("unassigned" in blocker.lower() for blocker in result["blockers"]))


if __name__ == "__main__":
    unittest.main()
