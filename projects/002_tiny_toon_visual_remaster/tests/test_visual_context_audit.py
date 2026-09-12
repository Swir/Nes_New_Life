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

from visual_context_audit import (  # noqa: E402
    build_context_families,
    mark_reviewed,
    review_status,
    sync_review,
    write_dashboard,
)


class VisualContextAuditTests(unittest.TestCase):
    @staticmethod
    def _write_pack(folder: Path) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        image = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
        for y in range(32):
            for x in range(32):
                image.putpixel((x, y), (220, 70, 50, 255))
            for x in range(32, 64):
                image.putpixel((x, y), (50, 120, 220, 255))
        image.save(folder / "tiles.png")
        (folder / "hires.txt").write_text(
            "<ver>106\n"
            "<scale>4\n"
            "<img>tiles.png\n"
            "[hero_idle]<tile>0,2E,FF16360F,0,0,1,N\n"
            "[hero_hit]<tile>0,2E,FF303030,32,0,1,N\n",
            encoding="utf-8",
        )

    @staticmethod
    def _write_queue(path: Path) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["tile_id", "palette", "art_group"])
            writer.writerow(["2E", "FF16360F", "PLAYER"])
            writer.writerow(["2E", "FF303030", "PLAYER"])

    def test_high_risk_family_requires_explicit_review(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = root / "pack"
            queue = root / "queue.csv"
            review = root / "VISUAL_CONTEXT_REVIEW.csv"
            self._write_pack(pack)
            self._write_queue(queue)

            families = build_context_families(pack, queue)
            self.assertEqual(len(families), 1)
            self.assertGreaterEqual(families[0]["risk_score"], 4)
            self.assertIn("multi-palette", families[0]["risk_reasons"])
            self.assertIn("multi-condition", families[0]["risk_reasons"])
            self.assertIn("visual-variants", families[0]["risk_reasons"])

            sync = sync_review(pack, queue, review)
            self.assertEqual(sync["gate"], "BLOCKED")
            self.assertEqual(sync["pending"], 1)

            mark_reviewed(review, "2E", "checked both hero contexts in MesenCE")
            status = review_status(pack, queue, review)
            self.assertEqual(status["gate"], "PASS")
            self.assertEqual(status["reviewed"], 1)

    def test_art_change_makes_old_review_stale(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = root / "pack"
            queue = root / "queue.csv"
            review = root / "VISUAL_CONTEXT_REVIEW.csv"
            self._write_pack(pack)
            self._write_queue(queue)
            sync_review(pack, queue, review)
            mark_reviewed(review, "2E", "reviewed")
            self.assertEqual(review_status(pack, queue, review)["gate"], "PASS")

            with Image.open(pack / "tiles.png") as image:
                rgba = image.convert("RGBA")
            rgba.putpixel((5, 5), (20, 250, 80, 255))
            rgba.save(pack / "tiles.png")

            status = review_status(pack, queue, review)
            self.assertEqual(status["gate"], "BLOCKED")
            self.assertEqual(status["stale"], 1)

    def test_dashboard_contains_metadata_only_and_no_png_payload(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = root / "pack"
            queue = root / "queue.csv"
            review = root / "VISUAL_CONTEXT_REVIEW.csv"
            output = root / "report"
            self._write_pack(pack)
            self._write_queue(queue)

            result = write_dashboard(pack, queue, review, output)
            self.assertTrue(Path(result["dashboard"]).is_file())
            self.assertTrue((output / "VISUAL_CONTEXT_AUDIT.json").is_file())
            self.assertEqual(list(output.glob("*.png")), [])


if __name__ == "__main__":
    unittest.main()
