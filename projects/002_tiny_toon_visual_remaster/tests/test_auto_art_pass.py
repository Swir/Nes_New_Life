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

from art_workspace import init_workspace, scan_workspace  # noqa: E402
from auto_art_pass import seed_baseline_art  # noqa: E402
from hd_readiness import write_grouped_art_queue  # noqa: E402


class AutoArtPassTests(unittest.TestCase):
    @staticmethod
    def _write_pack(folder: Path) -> None:
        folder.mkdir()
        image = Image.new("RGBA", (96, 32), (0, 0, 0, 0))
        for x in range(32):
            for y in range(32):
                image.putpixel((x, y), (120, 70, 60, 255))
        for x in range(32, 64):
            for y in range(32):
                image.putpixel((x, y), (60, 130, 75, 220))
        for x in range(64, 96):
            for y in range(32):
                image.putpixel((x, y), (80, 90, 170, 180))
        image.save(folder / "tiles.png")
        (folder / "hires.txt").write_text(
            "\n".join([
                "<ver>106",
                "<scale>4",
                "<img>tiles.png",
                "[hero_player]<tile>0,2E,FF16360F,0,0,1,N",
                "[boss_final]<tile>0,2F,FF16360F,32,0,1,N",
                "[hud_score]<tile>0,30,FF27160F,64,0,1,N",
                "<condition>hero_player,tileNearby,8,0,2E,FF16360F",
                "<condition>boss_final,tileNearby,8,0,2F,FF16360F",
                "<condition>hud_score,tileNearby,8,0,30,FF27160F",
            ]) + "\n",
            encoding="utf-8",
        )

    def test_group_aware_baseline_changes_todo_and_preserves_alpha(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = root / "pack"
            workspace = root / "workspace"
            self._write_pack(pack)
            queue = write_grouped_art_queue(pack, root / "queue.csv")
            init_workspace(pack, workspace, queue)

            manifest = json.loads((workspace / "MASTER_TILES.json").read_text(encoding="utf-8"))
            alpha_before = {}
            for item in manifest["masters"]:
                with Image.open(workspace / "original" / item["file"]) as image:
                    alpha_before[item["file"]] = image.convert("RGBA").getchannel("A").tobytes()

            result = seed_baseline_art(workspace, "group-aware")
            self.assertEqual(result["seeded"], len(manifest["masters"]))
            self.assertEqual(result["preserved_existing_edits"], 0)
            self.assertEqual(result["workspace_scan"]["edited"], len(manifest["masters"]))
            self.assertTrue((workspace / "AUTO_BASELINE.json").is_file())

            for item in manifest["masters"]:
                original = workspace / "original" / item["file"]
                editable = workspace / "editable" / item["file"]
                with Image.open(original) as before, Image.open(editable) as after:
                    self.assertEqual(before.size, after.size)
                    self.assertEqual(after.convert("RGBA").getchannel("A").tobytes(), alpha_before[item["file"]])
                self.assertNotEqual(original.read_bytes(), editable.read_bytes())

    def test_existing_manual_edit_is_preserved_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = root / "pack"
            workspace = root / "workspace"
            self._write_pack(pack)
            queue = write_grouped_art_queue(pack, root / "queue.csv")
            init_workspace(pack, workspace, queue)

            manifest = json.loads((workspace / "MASTER_TILES.json").read_text(encoding="utf-8"))
            manual = workspace / "editable" / manifest["masters"][0]["file"]
            with Image.open(manual) as image:
                changed = image.convert("RGBA")
            changed.putpixel((0, 0), (1, 2, 3, changed.getpixel((0, 0))[3]))
            changed.save(manual)
            manual_bytes = manual.read_bytes()

            result = seed_baseline_art(workspace, "group-aware")
            self.assertEqual(result["preserved_existing_edits"], 1)
            self.assertEqual(manual.read_bytes(), manual_bytes)
            scan = scan_workspace(workspace)
            self.assertEqual(scan["edited"], len(manifest["masters"]))


if __name__ == "__main__":
    unittest.main()
