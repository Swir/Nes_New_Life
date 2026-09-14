from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[1]
TOOLS = PROJECT / "tools"
WINDOWS = PROJECT / "windows"
sys.path.insert(0, str(TOOLS))

import regression_defect_locator as locator
import regression_visual_picker as picker


class RegressionVisualPickerTests(unittest.TestCase):
    @staticmethod
    def _write_pack(pack: Path) -> None:
        pack.mkdir(parents=True, exist_ok=True)
        sheet = Image.new("RGBA", (96, 64), (0, 0, 0, 0))
        for y in range(32):
            for x in range(32):
                sheet.putpixel((x, y), (80, 180, 230, 255))
        for y in range(32):
            for x in range(32, 64):
                alpha = 255 if (x + y) % 3 else 120
                sheet.putpixel((x, y), (225, 90, 120, alpha))
        for y in range(32, 64):
            for x in range(32):
                sheet.putpixel((x, y), (100, 210, 90, 255))
        sheet.save(pack / "tiles.png")
        (pack / "hires.txt").write_text("\n".join([
            "<ver>106",
            "<scale>4",
            "<img>tiles.png",
            "[hero_idle]<tile>0,2E,FF16360F,0,0,1,N",
            "[hero_alt]<tile>0,2E,FF16360F,32,0,1,N",
            "[world_grass]<tile>0,50,FF001122,0,32,1,N",
            "<condition>hero_idle,tileNearby,8,0,2E,FF16360F",
            "<condition>hero_alt,tileNearby,8,0,2E,FF16360F",
            "<condition>world_grass,tileNearby,8,0,50,FF001122",
        ]) + "\n", encoding="utf-8")

    @staticmethod
    def _write_queue(root: Path) -> None:
        artwork = root / "Artwork"
        artwork.mkdir(parents=True, exist_ok=True)
        with (artwork / "ART_QUEUE.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["tile_id", "palette", "art_group"])
            writer.writeheader()
            writer.writerows([
                {"tile_id": "2E", "palette": "FF16360F", "art_group": "PLAYER"},
                {"tile_id": "50", "palette": "FF001122", "art_group": "WORLD"},
            ])

    def _plan(self, root: Path, pack: Path) -> dict:
        self._write_pack(pack)
        self._write_queue(root)
        return locator.build_plan(root, pack, "player_movement", "ANIMATION_SEAM", top=12)

    def test_build_cards_embeds_real_ranked_candidate_previews(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = root / "pack"
            plan = self._plan(root, pack)
            cards = picker.build_cards(plan, pack, max_variants=4)
            self.assertGreaterEqual(len(cards), 2)
            first = cards[0]
            self.assertEqual(1, first["rank"])
            self.assertEqual("PLAYER", first["group"])
            self.assertEqual("2E", first["tile_id"])
            self.assertGreaterEqual(first["variant_count"], 2)
            self.assertTrue(first["variants"][0]["preview"].startswith("data:image/png;base64,"))

    def test_picker_is_fingerprint_bound_and_rejects_stale_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = root / "pack"
            plan = self._plan(root, pack)
            with patch.object(picker, "pack_fingerprint", return_value="different-runtime"):
                with self.assertRaisesRegex(picker.VisualPickerError, "fingerprint changed"):
                    picker.build_cards(plan, pack)

    def test_local_picker_html_declares_rom_pixels_and_clickable_rank(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = root / "pack"
            plan = self._plan(root, pack)
            result = picker.write_picker(plan, pack, root / "Reports" / "RegressionDefectLocator")
            path = Path(result["picker"])
            source = path.read_text(encoding="utf-8")
            self.assertTrue(result["contains_rom_derived_pixels"])
            self.assertEqual("LOCAL_ONLY_GITIGNORED_REPORTS", result["repository_policy"])
            self.assertIn("LOCAL-ONLY", source)
            self.assertIn("data:image/png;base64,", source)
            self.assertIn("onclick='pick(this)'", source)
            self.assertIn("clipboard", source)
            self.assertIn("[SWIR_TARGET", source)

    def test_reports_are_gitignored_for_rom_derived_picker_output(self) -> None:
        gitignore = (REPO / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("projects/**/Reports/", gitignore)

    def test_windows_guided_runner_opens_visual_picker_before_target_choice(self) -> None:
        source = (WINDOWS / "Guided_Regression_Playtest.ps1").read_text(encoding="utf-8")
        self.assertIn("regression_visual_picker.py", source)
        self.assertIn("REGRESSION_VISUAL_PICKER_LOCAL_ONLY.html", source)
        self.assertIn("VISUAL DEFECT PICKER READY", source)
        self.assertIn("contains_rom_derived_pixels", source)
        self.assertIn("Start-Process $VisualPickerHtml", source)
        self.assertLess(source.index("Start-Process $VisualPickerHtml"), source.index("Choose target number shown on the visual board"))


if __name__ == "__main__":
    unittest.main()
