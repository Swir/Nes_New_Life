from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from animation_workbench import (  # noqa: E402
    build_animation_families,
    build_condition_candidates,
    mark_reviewed,
    review_status,
    semantic_family,
    sync_review,
    write_contact_sheets,
    write_dashboard,
)


class AnimationWorkbenchTests(unittest.TestCase):
    @staticmethod
    def _write_pack(folder: Path) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        image = Image.new("RGBA", (160, 32), (0, 0, 0, 0))
        colors = [
            (220, 70, 50, 255),
            (210, 100, 40, 255),
            (190, 130, 50, 255),
            (60, 150, 220, 255),
            (90, 180, 230, 255),
        ]
        for index, color in enumerate(colors):
            for y in range(32):
                for x in range(index * 32, index * 32 + 32):
                    image.putpixel((x, y), color)
        image.save(folder / "tiles.png")
        (folder / "hires.txt").write_text(
            "<ver>106\n"
            "<scale>4\n"
            "<img>tiles.png\n"
            "[hero_walk_1]<tile>0,2E,FF16360F,0,0,1,N\n"
            "[hero_walk_2]<tile>0,2F,FF16360F,32,0,1,N\n"
            "[hero_run_1]<tile>0,30,FF16360F,64,0,1,N\n"
            "[hero_jump_1]<tile>0,31,FF303030,96,0,1,N\n"
            "[hero_jump_1]<tile>0,32,FF303030,128,0,1,N\n",
            encoding="utf-8",
        )

    @staticmethod
    def _write_queue(path: Path) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["tile_id", "palette", "art_group"])
            for tile_id, palette in [
                ("2E", "FF16360F"), ("2F", "FF16360F"), ("30", "FF16360F"),
                ("31", "FF303030"), ("32", "FF303030"),
            ]:
                writer.writerow([tile_id, palette, "PLAYER"])

    def test_semantic_family_groups_animation_states(self) -> None:
        self.assertEqual(semantic_family("hero_walk_1"), "HERO")
        self.assertEqual(semantic_family("hero_jump_frame_2"), "HERO")
        self.assertEqual(semantic_family("boss_alpha_phase_2_attack"), "BOSS_ALPHA")

    def test_animation_family_risk_and_review_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = root / "pack"
            queue = root / "queue.csv"
            review = root / "ANIMATION_REVIEW.csv"
            self._write_pack(pack)
            self._write_queue(queue)

            families = build_animation_families(pack, queue)
            hero = next(item for item in families if item["family"] == "HERO")
            self.assertTrue(hero["needs_review"])
            self.assertIn("animation-sequence", hero["risk_reasons"])
            self.assertIn("multi-tile-object", hero["risk_reasons"])

            result = sync_review(pack, queue, review)
            self.assertEqual(result["gate"], "BLOCKED")
            mark_reviewed(review, "HERO", "verified walk/run/jump transitions in MesenCE")
            self.assertEqual(review_status(pack, queue, review)["gate"], "PASS")

            with Image.open(pack / "tiles.png") as image:
                rgba = image.convert("RGBA")
            rgba.putpixel((5, 5), (10, 250, 80, 255))
            rgba.save(pack / "tiles.png")
            stale = review_status(pack, queue, review)
            self.assertEqual(stale["gate"], "BLOCKED")
            self.assertEqual(stale["stale"], 1)

    def test_condition_candidates_do_not_claim_screen_geometry(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = root / "pack"
            queue = root / "queue.csv"
            self._write_pack(pack)
            self._write_queue(queue)
            candidates = build_condition_candidates(pack, queue)
            jump = next(item for item in candidates if item["condition"] == "hero_jump_1")
            self.assertEqual(len(jump["tile_ids"]), 2)
            self.assertTrue(jump["requires_ingame_layout_verification"])
            self.assertEqual(jump["candidate_type"], "condition-cooccurrence")

    def test_dashboard_is_metadata_only_contact_sheets_are_explicit_local_output(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = root / "pack"
            queue = root / "queue.csv"
            review = root / "ANIMATION_REVIEW.csv"
            report = root / "report"
            boards = root / "boards"
            self._write_pack(pack)
            self._write_queue(queue)

            result = write_dashboard(pack, queue, review, report)
            self.assertTrue(Path(result["dashboard"]).is_file())
            self.assertEqual(list(report.glob("*.png")), [])
            contact = write_contact_sheets(pack, queue, boards)
            self.assertGreaterEqual(len(contact["created"]), 1)
            self.assertTrue(all((boards / name).is_file() for name in contact["created"]))


if __name__ == "__main__":
    unittest.main()
