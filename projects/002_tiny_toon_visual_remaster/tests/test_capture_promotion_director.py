from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from capture_promotion_director import _promotion_acceptance, promote_capture  # noqa: E402


class CapturePromotionDirectorTests(unittest.TestCase):
    @staticmethod
    def _write_pack(folder: Path, *, boss: bool = False) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        for y in range(32):
            for x in range(32):
                image.putpixel((x, y), (80, 180, 230, 255))
        if boss:
            for y in range(32, 64):
                for x in range(32, 64):
                    image.putpixel((x, y), (220, 70, 80, 255))
        image.save(folder / "tiles.png")
        lines = [
            "<ver>106",
            "<scale>4",
            "<img>tiles.png",
            "[hero_player_idle]<tile>0,2E,FF16360F,0,0,1,N",
            "[hero_player_walk_1]<tile>0,2F,FF16360F,32,0,1,N",
            "<condition>hero_player_idle,tileNearby,8,0,2E,FF16360F",
            "<condition>hero_player_walk_1,tileNearby,8,0,2F,FF16360F",
        ]
        if boss:
            lines.extend([
                "[boss_final_idle]<tile>0,30,FF27160F,0,32,1,N",
                "[boss_final_attack_1]<tile>0,31,FF27160F,32,32,1,N",
                "<condition>boss_final_idle,tileNearby,8,0,30,FF27160F",
                "<condition>boss_final_attack_1,tileNearby,8,0,31,FF27160F",
            ])
        (folder / "hires.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_good_candidate_runs_full_safe_promotion_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "project"
            capture = root / "capture"
            project.mkdir()
            self._write_pack(capture, boss=True)

            result = promote_capture(project, capture, top=5, create_sprint=True)

            self.assertEqual(result["promotion_gate"], "PROMOTED")
            self.assertEqual(result["capture_regressions"], 0)
            self.assertEqual(result["coverage_acceptance"]["promotion_admission"]["gate"], "PASS")
            self.assertEqual(result["coverage_acceptance"]["promotion_admission"]["mode"], "INCREMENTAL_CAPTURE_READY")
            self.assertTrue((project / "Reports" / "CaptureCoverageAcceptance" / "CAPTURE_COVERAGE_ACCEPTANCE.json").is_file())
            self.assertTrue((project / "Artwork" / "ART_QUEUE.csv").is_file())
            self.assertTrue((project / "Artwork" / "MasterWorkspace" / "MASTER_TILES.json").is_file())
            self.assertTrue((project / "Artwork" / "VISUAL_CONTEXT_REVIEW.csv").is_file())
            self.assertTrue((project / "Artwork" / "ANIMATION_FAMILY_REVIEW.csv").is_file())
            self.assertTrue((project / "Reports" / "FinalArtPriority" / "FINAL_ART_NEXT.csv").is_file())
            self.assertTrue((project / "Reports" / "ProductionSprint" / "PRODUCTION_SPRINT.html").is_file())
            self.assertTrue((project / "Artwork" / "CurrentArtSprint" / "ART_SPRINT_KIT.json").is_file())
            self.assertTrue((project / "Reports" / "CapturePromotion" / "CAPTURE_PROMOTION.html").is_file())

    def test_regressed_candidate_is_blocked_before_workspace_sync(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "project"
            previous = root / "previous"
            regressed = root / "regressed"
            project.mkdir()
            self._write_pack(previous, boss=True)
            self._write_pack(regressed, boss=False)

            first = promote_capture(project, previous, top=5)
            self.assertEqual(first["promotion_gate"], "PROMOTED")
            queue_before = (project / "Artwork" / "ART_QUEUE.csv").read_bytes()
            manifest_before = (project / "Artwork" / "MasterWorkspace" / "MASTER_TILES.json").read_bytes()

            second = promote_capture(project, regressed, previous_capture=previous, top=5)
            self.assertIn(second["promotion_gate"], {"BLOCKED_REGRESSION", "BLOCKED_ACCEPTANCE"})
            self.assertGreater(second["capture_regressions"], 0)
            self.assertEqual((project / "Artwork" / "ART_QUEUE.csv").read_bytes(), queue_before)
            self.assertEqual((project / "Artwork" / "MasterWorkspace" / "MASTER_TILES.json").read_bytes(), manifest_before)
            self.assertEqual(second["next_actions"][0]["kind"], "CAPTURE_REGRESSION")

    def test_promotion_admission_ignores_only_full_coverage_blockers(self) -> None:
        incremental = _promotion_acceptance({
            "acceptance_gate": "BLOCKED",
            "capture_fingerprint_sha256": "abc",
            "hard_blockers": [
                {"kind": "MISSION_COVERAGE", "detail": "pending"},
                {"kind": "GROUP_SIGNAL", "detail": "not captured yet"},
            ],
        })
        self.assertEqual(incremental["gate"], "PASS")
        self.assertEqual(incremental["mode"], "INCREMENTAL_CAPTURE_READY")

        unsafe = _promotion_acceptance({
            "acceptance_gate": "BLOCKED",
            "capture_fingerprint_sha256": "abc",
            "hard_blockers": [
                {"kind": "MISSION_PROVENANCE", "detail": "untrusted"},
            ],
        })
        self.assertEqual(unsafe["gate"], "BLOCKED")
        self.assertEqual(unsafe["mode"], "UNSAFE_CAPTURE")

    def test_reports_are_metadata_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "project"
            capture = root / "capture"
            project.mkdir()
            self._write_pack(capture, boss=True)
            promote_capture(project, capture, top=5)

            promotion = project / "Reports" / "CapturePromotion"
            acceptance = project / "Reports" / "CaptureCoverageAcceptance"
            self.assertEqual(list(promotion.glob("*.png")), [])
            self.assertEqual(list(acceptance.glob("*.png")), [])
            data = json.loads((promotion / "CAPTURE_PROMOTION.json").read_text(encoding="utf-8"))
            self.assertEqual(data["promotion_gate"], "PROMOTED")
            self.assertIn("coverage_acceptance", data)


if __name__ == "__main__":
    unittest.main()
