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
from release_candidate import REGRESSION_CASES, complete_regression_case, pack_fingerprint  # noqa: E402
from studio_command_center import (  # noqa: E402
    animation_family_dashboard,
    evidence_paths,
    gated_release_package,
    initialize_project_evidence,
    release_audit,
    visual_context_dashboard,
)
from visual_context_audit import sync_review  # noqa: E402


class StudioCommandCenterTests(unittest.TestCase):
    @staticmethod
    def _write_pack(folder: Path) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        image = Image.new("RGBA", (64, 32), (50, 100, 180, 255))
        image.save(folder / "tiles.png")
        (folder / "hires.txt").write_text(
            "<ver>106\n<scale>4\n<img>tiles.png\n"
            "[hero_walk_1]<tile>0,2E,FF16360F,0,0,1,N\n"
            "[hero_walk_2]<tile>0,2F,FF16360F,32,0,1,N\n",
            encoding="utf-8",
        )

    @staticmethod
    def _complete_capture(path: Path) -> None:
        data = default_manifest()
        for item in data["missions"].values():
            item["done"] = True
            item["notes"] = "verified locally"
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    @staticmethod
    def _write_done_queue(path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["tile_id", "palette", "status", "art_group"])
            writer.writerow(["2E", "FF16360F", "DONE", "PLAYER"])
            writer.writerow(["2F", "FF16360F", "DONE", "PLAYER"])

    def _make_green_evidence(self, root: Path, pack: Path) -> None:
        paths = initialize_project_evidence(root)
        self._complete_capture(paths.capture_manifest)
        self._write_done_queue(paths.art_queue)
        sync_review(pack, paths.art_queue, paths.visual_review)
        paths.art_qa.parent.mkdir(parents=True, exist_ok=True)
        paths.art_qa.write_text(
            json.dumps({"qa_gate": "PASS", "output_pack_fingerprint": pack_fingerprint(pack)}),
            encoding="utf-8",
        )
        for key, _ in REGRESSION_CASES:
            complete_regression_case(paths.regression_manifest, key, pack, "verified on exact build")

    def test_initializes_authoritative_evidence_paths(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            paths = initialize_project_evidence(root)
            self.assertTrue(paths.capture_manifest.is_file())
            self.assertTrue(paths.regression_manifest.is_file())
            self.assertTrue(paths.reports.is_dir())
            self.assertEqual(paths.visual_review, root / "Artwork" / "VISUAL_CONTEXT_REVIEW.csv")
            self.assertEqual(paths.animation_review, root / "Artwork" / "ANIMATION_FAMILY_REVIEW.csv")
            self.assertEqual(evidence_paths(root).art_qa, root / "Reports" / "ArtQA" / "ART_QA_RESULT.json")

    def test_studio_audit_exposes_visual_context_as_real_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); pack = root / "pack"
            self._write_pack(pack)
            result = release_audit(root, pack)
            self.assertEqual(result["release_gate"], "BLOCKED")
            self.assertTrue(any("Capture missions incomplete" in item for item in result["blockers"]))
            self.assertTrue(any("Visual Context Review is missing" in item for item in result["blockers"]))
            self.assertTrue(Path(result["dashboard"]).is_file())

    def test_studio_generates_visual_and_animation_dashboards(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); pack = root / "pack"
            self._write_pack(pack)
            paths = initialize_project_evidence(root)
            self._write_done_queue(paths.art_queue)
            visual = visual_context_dashboard(root, pack)
            animation = animation_family_dashboard(root, pack, create_contact_sheets=True)
            self.assertTrue(Path(visual["dashboard"]).is_file())
            self.assertTrue(Path(animation["dashboard"]).is_file())
            self.assertIn("contact_sheets", animation)

    def test_gated_studio_packaging_requires_and_preserves_green_build_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); pack = root / "pack"
            self._write_pack(pack)
            with self.assertRaises(ValueError):
                gated_release_package(root, pack)
            self._make_green_evidence(root, pack)
            result = gated_release_package(root, pack)
            self.assertEqual(result["release_gate"], "PASS")
            self.assertEqual(result["pack_fingerprint"], pack_fingerprint(pack))
            self.assertTrue(Path(result["zip"]).is_file())
            self.assertTrue((root / "Release" / "RELEASE_PACKAGE.json").is_file())


if __name__ == "__main__":
    unittest.main()
