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

from visual_completion_matrix import build_matrix, build_and_write  # noqa: E402


class VisualCompletionMatrixTests(unittest.TestCase):
    @staticmethod
    def _pack(folder: Path) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        image = Image.new("RGBA", (128, 32), (0, 0, 0, 0))
        for idx, color in enumerate([(220, 60, 60, 255), (50, 180, 240, 255), (180, 90, 220, 255), (80, 210, 120, 255)]):
            for y in range(32):
                for x in range(idx * 32, (idx + 1) * 32):
                    image.putpixel((x, y), color)
        image.save(folder / "tiles.png")
        (folder / "hires.txt").write_text(
            "<ver>106\n<scale>4\n<img>tiles.png\n"
            "[hero_walk_1]<tile>0,2E,FF111111,0,0,1,N\n"
            "[hero_walk_2]<tile>0,2E,FF111111,0,0,1,N\n"
            "[boss_attack]<tile>0,3A,FF222222,32,0,1,N\n"
            "[enemy_idle]<tile>0,4B,FF333333,64,0,1,N\n"
            "[world_ground]<tile>0,5C,FF444444,96,0,1,N\n",
            encoding="utf-8",
        )

    @staticmethod
    def _queue(path: Path) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            w = csv.writer(handle)
            w.writerow(["tile_id", "palette", "status", "art_group"])
            w.writerow(["2E", "FF111111", "TODO", "PLAYER"])
            w.writerow(["3A", "FF222222", "TODO", "BOSS"])
            w.writerow(["4B", "FF333333", "TODO", "ENEMY"])
            w.writerow(["5C", "FF444444", "TODO", "WORLD"])

    @staticmethod
    def _workspace(root: Path) -> Path:
        ws = root / "workspace"; ws.mkdir()
        with (ws / "ART_STATE.csv").open("w", encoding="utf-8", newline="") as handle:
            w = csv.writer(handle)
            w.writerow(["master_file", "group", "tile_id", "palette", "uses", "status", "original_sha256", "editable_sha256"])
            w.writerow(["hero.png", "PLAYER", "2E", "FF111111", 2, "EDITED", "a", "b"])
            w.writerow(["boss.png", "BOSS", "3A", "FF222222", 1, "INVALID_SIZE", "a", "a"])
            w.writerow(["enemy.png", "ENEMY", "4B", "FF333333", 1, "TODO", "a", "a"])
            w.writerow(["world.png", "WORLD", "5C", "FF444444", 1, "TODO", "a", "a"])
        return ws

    def test_matrix_measures_group_completion_and_prioritizes_invalid_boss(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); pack = root / "pack"; queue = root / "queue.csv"
            self._pack(pack); self._queue(queue); ws = self._workspace(root)
            result = build_matrix(pack, queue=queue, workspace=ws, batch_size=3)
            groups = {g["group"]: g for g in result["groups"]}
            self.assertEqual(groups["PLAYER"]["master_percent"], 100.0)
            self.assertEqual(groups["BOSS"]["invalid"], 1)
            self.assertEqual(result["next_batch"][0]["group"], "BOSS")
            self.assertIn("invalid-master", result["next_batch"][0]["reasons"])
            self.assertGreater(result["overall_weighted_percent"], 0)
            self.assertLess(result["overall_weighted_percent"], 100)

    def test_outputs_are_metadata_only_and_batch_is_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); pack = root / "pack"; queue = root / "queue.csv"; out = root / "reports"
            self._pack(pack); self._queue(queue); ws = self._workspace(root)
            result = build_and_write(pack, out, queue=queue, workspace=ws, batch_size=2)
            self.assertEqual(len(result["next_batch"]), 2)
            self.assertTrue((out / "VISUAL_COMPLETION_MATRIX.html").is_file())
            self.assertTrue((out / "NEXT_HIGH_IMPACT_ART_BATCH.csv").is_file())
            self.assertEqual(list(out.glob("*.png")), [])
            payload = json.loads((out / "VISUAL_COMPLETION_MATRIX.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["captured_masters"], 4)
            self.assertIn("Uncaptured game states", payload["important_note"])


if __name__ == "__main__":
    unittest.main()
