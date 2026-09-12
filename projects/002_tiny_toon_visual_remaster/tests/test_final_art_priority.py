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

from final_art_priority import build_priority_rows, write_priority_board  # noqa: E402


class FinalArtPriorityTests(unittest.TestCase):
    @staticmethod
    def _write_pack(folder: Path) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        image = Image.new("RGBA", (96, 32), (0, 0, 0, 0))
        colors = [(220, 70, 50, 255), (40, 160, 230, 255), (170, 70, 210, 255)]
        for idx, color in enumerate(colors):
            for y in range(32):
                for x in range(idx * 32, (idx + 1) * 32):
                    image.putpixel((x, y), color)
        image.save(folder / "tiles.png")
        (folder / "hires.txt").write_text(
            "<ver>106\n<scale>4\n<img>tiles.png\n"
            "[hero_walk_1]<tile>0,2E,FF111111,0,0,1,N\n"
            "[hero_walk_2]<tile>0,2E,FF222222,0,0,1,N\n"
            "[boss_attack_1]<tile>0,3A,FF333333,32,0,1,N\n"
            "[enemy_idle_1]<tile>0,4B,FF444444,64,0,1,N\n",
            encoding="utf-8",
        )

    @staticmethod
    def _write_queue(path: Path) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["tile_id", "palette", "status", "art_group"])
            writer.writerow(["2E", "FF111111", "TODO", "PLAYER"])
            writer.writerow(["2E", "FF222222", "TODO", "PLAYER"])
            writer.writerow(["3A", "FF333333", "TODO", "BOSS"])
            writer.writerow(["4B", "FF444444", "TODO", "ENEMY"])

    @staticmethod
    def _write_workspace(root: Path) -> Path:
        workspace = root / "workspace"
        workspace.mkdir()
        with (workspace / "ART_STATE.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["master_file", "group", "tile_id", "palette", "uses", "status", "original_sha256", "editable_sha256"])
            writer.writerow(["a.png", "PLAYER", "2E", "FF111111", 1, "TODO", "a", "a"])
            writer.writerow(["b.png", "PLAYER", "2E", "FF222222", 1, "EDITED", "a", "b"])
            writer.writerow(["c.png", "BOSS", "3A", "FF333333", 1, "TODO", "a", "a"])
            writer.writerow(["d.png", "ENEMY", "4B", "FF444444", 1, "TODO", "a", "a"])
        return workspace

    def test_prioritizes_unfinished_player_and_boss_and_skips_edited(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); pack = root / "pack"; queue = root / "queue.csv"
            self._write_pack(pack); self._write_queue(queue); workspace = self._write_workspace(root)
            rows = build_priority_rows(pack, queue, workspace)
            keys = {(row["tile_id"], row["palette"]) for row in rows}
            self.assertNotIn(("2E", "FF222222"), keys)
            self.assertIn(("2E", "FF111111"), keys)
            self.assertIn(("3A", "FF333333"), keys)
            self.assertGreaterEqual(rows[0]["priority_score"], rows[-1]["priority_score"])
            self.assertIn(rows[0]["group"], {"PLAYER", "BOSS"})

    def test_pending_visual_review_boosts_priority(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); pack = root / "pack"; queue = root / "queue.csv"; review = root / "visual.csv"
            self._write_pack(pack); self._write_queue(queue); workspace = self._write_workspace(root)
            with review.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(["tile_id", "status"])
                writer.writerow(["2E", "REVIEW"])
            rows = build_priority_rows(pack, queue, workspace, review)
            hero = next(row for row in rows if row["tile_id"] == "2E")
            self.assertIn("visual-context-pending", hero["reasons"])

    def test_reports_are_metadata_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); pack = root / "pack"; queue = root / "queue.csv"; output = root / "report"
            self._write_pack(pack); self._write_queue(queue); workspace = self._write_workspace(root)
            result = write_priority_board(pack, output, queue=queue, workspace=workspace, top=2)
            self.assertTrue(Path(result["dashboard"]).is_file())
            self.assertTrue(Path(result["csv"]).is_file())
            self.assertTrue((output / "FINAL_ART_PRIORITY.json").is_file())
            self.assertEqual(list(output.glob("*.png")), [])
            data = json.loads((output / "FINAL_ART_PRIORITY.json").read_text(encoding="utf-8"))
            self.assertEqual(data["top_count"], 2)


if __name__ == "__main__":
    unittest.main()
