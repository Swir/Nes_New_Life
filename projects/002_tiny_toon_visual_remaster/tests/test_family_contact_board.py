from pathlib import Path
import json
import tempfile
import unittest

from PIL import Image

from family_contact_board import generate_family_contact_boards


class FamilyContactBoardTests(unittest.TestCase):
    def _png(self, path: Path, offset: int = 0):
        image = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        for x in range(8 + offset, 20 + offset):
            for y in range(6, 26):
                if 0 <= x < 32:
                    image.putpixel((x, y), (240, 180, 80, 255))
        image.save(path)

    def test_generates_one_board_per_character_family_and_skips_world(self):
        with tempfile.TemporaryDirectory() as temp:
            kit = Path(temp)
            (kit / "editable").mkdir(); (kit / "reference").mkdir()
            for name, offset in (("001_a.png", 0), ("002_b.png", 2), ("003_world.png", 0)):
                self._png(kit / "editable" / name, offset)
                self._png(kit / "reference" / name, 0)
            items = [
                {"priority": 1, "group": "PLAYER", "tile_id": "AA", "palette": "P1", "seed_tile_id": "AA", "seed_palette": "P1", "kit_file": "001_a.png"},
                {"priority": 2, "group": "PLAYER", "tile_id": "AB", "palette": "P2", "seed_tile_id": "AA", "seed_palette": "P1", "kit_file": "002_b.png"},
                {"priority": 3, "group": "WORLD", "tile_id": "FF", "palette": "PW", "seed_tile_id": "FF", "seed_palette": "PW", "kit_file": "003_world.png"},
            ]
            result = generate_family_contact_boards(items, kit)
            self.assertEqual(result["family_count"], 1)
            self.assertEqual(result["families"][0]["members"], 2)
            self.assertTrue((kit / result["families"][0]["file"]).is_file())
            saved = json.loads((kit / "FAMILY_CONTACT_BOARDS.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["schema"], 1)
            self.assertEqual(len(saved["families"][0]["metrics"]), 2)
            self.assertIsNotNone(saved["families"][0]["metrics"][0]["bbox"])
            self.assertIsNotNone(saved["families"][0]["metrics"][0]["centroid"])

    def test_empty_character_set_is_valid(self):
        with tempfile.TemporaryDirectory() as temp:
            kit = Path(temp); (kit / "editable").mkdir(); (kit / "reference").mkdir()
            result = generate_family_contact_boards([], kit)
            self.assertEqual(result["family_count"], 0)
            self.assertTrue((kit / "FAMILY_CONTACT_BOARDS.json").is_file())


if __name__ == "__main__":
    unittest.main()
