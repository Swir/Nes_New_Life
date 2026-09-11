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

from art_production import (  # noqa: E402
    export_master_tiles,
    find_duplicate_clusters,
    propagate_master,
    write_workboards,
)


class ArtProductionTests(unittest.TestCase):
    @staticmethod
    def _write_pack(folder: Path) -> Path:
        folder.mkdir(parents=True)
        sheet = Image.new("RGBA", (128, 64), (0, 0, 0, 0))
        red = Image.new("RGBA", (32, 32), (220, 40, 40, 255))
        blue = Image.new("RGBA", (32, 32), (40, 80, 220, 255))
        sheet.alpha_composite(red, (0, 0))
        sheet.alpha_composite(red, (32, 0))
        sheet.alpha_composite(blue, (64, 0))
        sheet.alpha_composite(blue, (96, 0))
        sheet.save(folder / "tiles.png")
        (folder / "hires.txt").write_text(
            "\n".join([
                "<ver>106",
                "<scale>4",
                "<img>tiles.png",
                "[hero_player]<tile>0,2E,FF16360F,0,0,1,N",
                "[hero_player]<tile>0,2F,FF16360F,32,0,1,N",
                "[boss_final]<tile>0,30,FF27160F,64,0,1,N",
                "[boss_final]<tile>0,31,FF27160F,96,0,1,N",
            ]) + "\n",
            encoding="utf-8",
        )
        queue = folder / "queue.csv"
        with queue.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["priority", "tile_id", "palette", "uses", "conditional_uses", "conditions", "status", "art_group", "group_confidence", "notes"])
            writer.writerow([1, "2E", "FF16360F", 1, 1, "hero_player", "TODO", "PLAYER", "high", ""])
            writer.writerow([2, "2F", "FF16360F", 1, 1, "hero_player", "TODO", "PLAYER", "high", ""])
            writer.writerow([3, "30", "FF27160F", 1, 1, "boss_final", "TODO", "BOSS", "high", ""])
            writer.writerow([4, "31", "FF27160F", 1, 1, "boss_final", "TODO", "BOSS", "high", ""])
        return queue

    def test_duplicate_clusters_and_group_workboards(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = root / "pack"
            queue = self._write_pack(pack)
            report = find_duplicate_clusters(pack, queue)
            self.assertEqual(report["tiles"], 4)
            self.assertEqual(report["exact_cluster_count"], 2)
            self.assertEqual(report["exact_duplicate_tiles"], 2)

            boards = root / "boards"
            manifest = write_workboards(pack, boards, queue, columns=2)
            self.assertEqual(manifest["tile_count"], 4)
            self.assertEqual(manifest["groups"]["PLAYER"]["tiles"], 2)
            self.assertEqual(manifest["groups"]["BOSS"]["tiles"], 2)
            self.assertTrue((boards / "WORKBOARD_PLAYER.png").is_file())
            self.assertTrue((boards / "WORKBOARD_BOSS.png").is_file())
            self.assertTrue((boards / "WORKBOARDS.json").is_file())

    def test_master_export_and_safe_propagation_preserve_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = root / "pack"
            queue = self._write_pack(pack)
            masters = root / "masters"
            manifest = export_master_tiles(pack, masters, queue)
            self.assertEqual(len(manifest["masters"]), 2)
            red_master = next(item for item in manifest["masters"] if item["group"] == "PLAYER")
            self.assertEqual(red_master["uses"], 2)

            replacement = root / "replacement.png"
            Image.new("RGBA", (32, 32), (20, 230, 90, 255)).save(replacement)
            output = root / "output"
            original_hires = (pack / "hires.txt").read_bytes()
            result = propagate_master(
                pack,
                masters / "MASTER_TILES.json",
                masters / red_master["file"],
                replacement,
                output,
            )
            self.assertEqual(result["targets_updated"], 2)
            self.assertTrue(result["mapping_preserved"])
            self.assertEqual((output / "hires.txt").read_bytes(), original_hires)
            with Image.open(output / "tiles.png") as image:
                rgba = image.convert("RGBA")
                self.assertEqual(rgba.getpixel((5, 5)), (20, 230, 90, 255))
                self.assertEqual(rgba.getpixel((37, 5)), (20, 230, 90, 255))
                self.assertEqual(rgba.getpixel((69, 5)), (40, 80, 220, 255))
            self.assertTrue((output / "PROPAGATION_RESULT.json").is_file())


if __name__ == "__main__":
    unittest.main()
