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

from art_sprint_kit import export_sprint_kit, finish_sprint, import_sprint_kit  # noqa: E402
from art_workspace import init_workspace, scan_workspace  # noqa: E402


class ArtSprintKitTests(unittest.TestCase):
    @staticmethod
    def _write_pack(folder: Path) -> None:
        folder.mkdir()
        image = Image.new("RGBA", (96, 32), (0, 0, 0, 0))
        colors = [(190, 50, 60, 255), (40, 120, 220, 255), (210, 150, 30, 255)]
        for index, color in enumerate(colors):
            for y in range(32):
                for x in range(index * 32, (index + 1) * 32):
                    image.putpixel((x, y), color)
        image.save(folder / "tiles.png")
        (folder / "hires.txt").write_text(
            "<ver>106\n<scale>4\n<img>tiles.png\n"
            "[hero_walk_1]<tile>0,2E,FF16360F,0,0,1,N\n"
            "[boss_final_hit]<tile>0,2F,FF27160F,32,0,1,N\n"
            "[enemy_walk_1]<tile>0,30,FF33160F,64,0,1,N\n",
            encoding="utf-8",
        )

    def test_export_creates_top_priority_editable_kit_and_local_board(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack, workspace, kit = root / "pack", root / "workspace", root / "kit"
            self._write_pack(pack)
            init_workspace(pack, workspace)

            result = export_sprint_kit(pack, workspace, kit, top=2)
            self.assertEqual(result["exported"], 2)
            self.assertEqual(len(list((kit / "editable").glob("*.png"))), 2)
            self.assertEqual(len(list((kit / "reference").glob("*.png"))), 2)
            self.assertTrue((kit / "LOCAL_ART_SPRINT_BOARD.png").is_file())
            self.assertTrue((kit / "ART_SPRINT_KIT.json").is_file())
            manifest = json.loads((kit / "ART_SPRINT_KIT.json").read_text(encoding="utf-8"))
            self.assertEqual(len(manifest["items"]), 2)
            self.assertTrue(all(item["dimensions"] == [32, 32] for item in manifest["items"]))

    def test_import_roundtrip_updates_only_changed_sprint_master(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack, workspace, kit = root / "pack", root / "workspace", root / "kit"
            self._write_pack(pack)
            init_workspace(pack, workspace)
            manifest = export_sprint_kit(pack, workspace, kit, top=3)
            target = kit / "editable" / manifest["items"][0]["kit_file"]
            Image.new("RGBA", (32, 32), (10, 240, 120, 255)).save(target)

            result = import_sprint_kit(workspace, kit)
            self.assertEqual(result["imported"], 1)
            self.assertEqual(result["unchanged"], 2)
            self.assertEqual(scan_workspace(workspace)["edited"], 1)

    def test_stale_workspace_conflict_blocks_import(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack, workspace, kit = root / "pack", root / "workspace", root / "kit"
            self._write_pack(pack)
            init_workspace(pack, workspace)
            manifest = export_sprint_kit(pack, workspace, kit, top=1)
            item = manifest["items"][0]
            Image.new("RGBA", (32, 32), (10, 240, 120, 255)).save(kit / "editable" / item["kit_file"])
            Image.new("RGBA", (32, 32), (240, 10, 120, 255)).save(workspace / "editable" / item["master_file"])
            with self.assertRaisesRegex(ValueError, "stale workspace conflicts"):
                import_sprint_kit(workspace, kit)

    def test_resized_sprint_master_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack, workspace, kit = root / "pack", root / "workspace", root / "kit"
            self._write_pack(pack)
            init_workspace(pack, workspace)
            manifest = export_sprint_kit(pack, workspace, kit, top=1)
            item = manifest["items"][0]
            Image.new("RGBA", (64, 64), (255, 0, 255, 255)).save(kit / "editable" / item["kit_file"])
            with self.assertRaisesRegex(ValueError, "invalid files"):
                import_sprint_kit(workspace, kit)

    def test_finish_imports_composes_and_pixel_qa_passes_with_mapping_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack, workspace, kit, output = root / "pack", root / "workspace", root / "kit", root / "final"
            self._write_pack(pack)
            init_workspace(pack, workspace)
            manifest = export_sprint_kit(pack, workspace, kit, top=1)
            item = manifest["items"][0]
            Image.new("RGBA", (32, 32), (20, 230, 100, 255)).save(kit / "editable" / item["kit_file"])

            result = finish_sprint(pack, workspace, kit, output)
            self.assertEqual(result["sprint_import"]["imported"], 1)
            self.assertEqual(result["qa_gate"], "PASS")
            self.assertTrue(result["mapping_preserved"])
            self.assertEqual((output / "hires.txt").read_bytes(), (pack / "hires.txt").read_bytes())
            self.assertTrue((kit / "ART_SPRINT_FINISH.json").is_file())


if __name__ == "__main__":
    unittest.main()
