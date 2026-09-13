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

from art_sprint_kit import finish_sprint  # noqa: E402
from art_workspace import init_workspace  # noqa: E402
from high_impact_art_sprint import prepare_high_impact_sprint  # noqa: E402


class HighImpactArtSprintTests(unittest.TestCase):
    @staticmethod
    def _write_pack(folder: Path) -> None:
        folder.mkdir()
        image = Image.new("RGBA", (128, 32), (0, 0, 0, 0))
        colors = [(190, 50, 60, 255), (40, 120, 220, 255), (210, 150, 30, 255), (100, 210, 90, 255)]
        for index, color in enumerate(colors):
            for y in range(32):
                for x in range(index * 32, (index + 1) * 32):
                    image.putpixel((x, y), color)
        image.save(folder / "tiles.png")
        (folder / "hires.txt").write_text(
            "<ver>106\n<scale>4\n<img>tiles.png\n"
            "[hero_walk_1]<tile>0,2E,FF16360F,0,0,1,N\n"
            "[hero_walk_2]<tile>0,2E,FF16360F,0,0,1,N\n"
            "[boss_final_hit]<tile>0,2F,FF27160F,32,0,1,N\n"
            "[enemy_walk_1]<tile>0,30,FF33160F,64,0,1,N\n"
            "[world_grass]<tile>0,31,FF44160F,96,0,1,N\n",
            encoding="utf-8",
        )

    def test_prepare_exports_family_aware_matrix_seed_batch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack, workspace = root / "pack", root / "workspace"
            kit, reports = root / "kit", root / "reports"
            self._write_pack(pack)
            init_workspace(pack, workspace)

            result = prepare_high_impact_sprint(pack, workspace, kit, reports, batch_size=2)
            self.assertEqual(result["status"], "READY")
            self.assertGreaterEqual(result["exported"], 1)
            self.assertTrue((reports / "NEXT_HIGH_IMPACT_ART_BATCH.csv").is_file())
            self.assertTrue((reports / "FAMILY_AWARE_ART_BATCH.json").is_file())
            self.assertTrue((kit / "LOCAL_ART_SPRINT_BOARD.png").is_file())
            self.assertTrue((kit / "FAMILY_CONTACT_BOARDS.json").is_file())

            manifest = json.loads((kit / "ART_SPRINT_KIT.json").read_text(encoding="utf-8"))
            matrix = json.loads((reports / "VISUAL_COMPLETION_MATRIX.json").read_text(encoding="utf-8"))
            family_plan = json.loads((reports / "FAMILY_AWARE_ART_BATCH.json").read_text(encoding="utf-8"))
            family_boards = json.loads((kit / "FAMILY_CONTACT_BOARDS.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["selection_mode"], "visual-completion-family-aware-high-impact")
            self.assertEqual(manifest["schema"], 4)
            self.assertEqual(manifest["matrix_seed_count"], len(matrix["next_batch"]))
            self.assertEqual(manifest["family_contact_board_count"], family_boards["family_count"])
            expected = [(row["tile_id"], row["palette"]) for row in family_plan["selection"]]
            actual = [(row["tile_id"], row["palette"]) for row in manifest["items"]]
            self.assertEqual(actual, expected)

    def test_prepared_batch_uses_existing_safe_finish_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack, workspace = root / "pack", root / "workspace"
            kit, reports, output = root / "kit", root / "reports", root / "output"
            self._write_pack(pack)
            init_workspace(pack, workspace)
            prepare_high_impact_sprint(pack, workspace, kit, reports, batch_size=1)
            manifest = json.loads((kit / "ART_SPRINT_KIT.json").read_text(encoding="utf-8"))
            item = manifest["items"][0]
            Image.new("RGBA", tuple(item["dimensions"]), (20, 230, 100, 255)).save(kit / "editable" / item["kit_file"])

            finished = finish_sprint(pack, workspace, kit, output)
            self.assertEqual(finished["sprint_import"]["imported"], 1)
            self.assertEqual(finished["qa_gate"], "PASS")
            self.assertTrue(finished["mapping_preserved"])
            self.assertEqual((output / "hires.txt").read_bytes(), (pack / "hires.txt").read_bytes())

    def test_nonempty_kit_is_never_overwritten_implicitly(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack, workspace = root / "pack", root / "workspace"
            kit, reports = root / "kit", root / "reports"
            self._write_pack(pack)
            init_workspace(pack, workspace)
            kit.mkdir()
            (kit / "artist-note.txt").write_text("keep me", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                prepare_high_impact_sprint(pack, workspace, kit, reports, batch_size=1)


if __name__ == "__main__":
    unittest.main()
