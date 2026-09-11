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

from art_workspace import apply_workspace, init_workspace, scan_workspace  # noqa: E402


class ArtWorkspaceTests(unittest.TestCase):
    @staticmethod
    def _write_pack(folder: Path) -> None:
        folder.mkdir()
        image = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
        for y in range(32):
            for x in range(32):
                image.putpixel((x, y), (180, 40, 50, 255))
        for y in range(32):
            for x in range(32, 64):
                image.putpixel((x, y), (30, 120, 210, 255))
        image.save(folder / "tiles.png")
        (folder / "hires.txt").write_text(
            "\n".join([
                "<ver>106",
                "<scale>4",
                "<img>tiles.png",
                "[hero_player]<tile>0,2E,FF16360F,0,0,1,N",
                "[boss_final]<tile>0,2F,FF27160F,32,0,1,N",
            ]) + "\n",
            encoding="utf-8",
        )

    def test_workspace_detects_multiple_edits_and_applies_them_together(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = root / "pack"
            workspace = root / "art"
            output = root / "output"
            self._write_pack(pack)

            info = init_workspace(pack, workspace)
            self.assertEqual(info["master_count"], 2)

            editable = sorted((workspace / "editable").glob("*.png"))
            self.assertEqual(len(editable), 2)
            Image.new("RGBA", (32, 32), (0, 255, 0, 255)).save(editable[0])
            Image.new("RGBA", (32, 32), (255, 255, 0, 255)).save(editable[1])

            scan = scan_workspace(workspace)
            self.assertEqual(scan["edited"], 2)
            self.assertEqual(scan["invalid"], 0)
            self.assertEqual(scan["percent_edited"], 100.0)

            result = apply_workspace(pack, workspace, output)
            self.assertEqual(result["changed_masters"], 2)
            self.assertEqual(result["targets_updated"], 2)
            self.assertTrue(result["mapping_preserved"])
            self.assertEqual((output / "hires.txt").read_bytes(), (pack / "hires.txt").read_bytes())
            self.assertTrue((output / "ART_APPLY_RESULT.json").is_file())

            with (workspace / "ART_STATE.csv").open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertTrue(all(row["status"] == "EDITED" for row in rows))

    def test_workspace_rejects_resized_master(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = root / "pack"
            workspace = root / "art"
            self._write_pack(pack)
            init_workspace(pack, workspace)
            target = next((workspace / "editable").glob("*.png"))
            Image.new("RGBA", (64, 64), (255, 0, 255, 255)).save(target)
            scan = scan_workspace(workspace)
            self.assertEqual(scan["invalid"], 1)
            with self.assertRaises(ValueError):
                apply_workspace(pack, workspace, root / "output")


if __name__ == "__main__":
    unittest.main()
