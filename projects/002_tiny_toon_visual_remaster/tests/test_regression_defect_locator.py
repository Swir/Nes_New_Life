from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

PROJECT = Path(__file__).resolve().parents[1]
TOOLS = PROJECT / "tools"
WINDOWS = PROJECT / "windows"
sys.path.insert(0, str(TOOLS))

import regression_defect_locator as locator


class RegressionDefectLocatorTests(unittest.TestCase):
    @staticmethod
    def _write_pack(pack: Path) -> None:
        pack.mkdir(parents=True, exist_ok=True)
        sheet = Image.new("RGBA", (128, 96), (0, 0, 0, 0))
        for y in range(32):
            for x in range(32):
                sheet.putpixel((x, y), (80, 180, 230, 255))
        for y in range(32):
            for x in range(32, 64):
                sheet.putpixel((x, y), (220, 80, 100, 255))
        for y in range(32, 64):
            for x in range(32):
                sheet.putpixel((x, y), (120, 210, 90, 255))
        sheet.save(pack / "tiles.png")
        (pack / "hires.txt").write_text("\n".join([
            "<ver>106",
            "<scale>4",
            "<img>tiles.png",
            "[hero_idle]<tile>0,2E,FF16360F,0,0,1,N",
            "[hero_walk_1]<tile>0,2E,FF16360F,0,0,1,N",
            "[enemy_walk]<tile>0,40,FF27160F,32,0,1,N",
            "[world_grass]<tile>0,50,FF001122,0,32,1,N",
            "<condition>hero_idle,tileNearby,8,0,2E,FF16360F",
            "<condition>hero_walk_1,tileNearby,8,0,2E,FF16360F",
            "<condition>enemy_walk,tileNearby,8,0,40,FF27160F",
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
                {"tile_id": "40", "palette": "FF27160F", "art_group": "ENEMY"},
                {"tile_id": "50", "palette": "FF001122", "art_group": "WORLD"},
            ])

    @staticmethod
    def _write_sprint(root: Path) -> None:
        sprint = root / "Artwork" / "CurrentImpactSprint"
        sprint.mkdir(parents=True, exist_ok=True)
        (sprint / "ART_SPRINT_KIT.json").write_text(json.dumps({
            "schema": 4,
            "items": [{
                "priority": 1,
                "impact_score": 920,
                "group": "PLAYER",
                "tile_id": "2E",
                "palette": "FF16360F",
                "seed_tile_id": "2E",
                "seed_palette": "FF16360F",
            }],
        }), encoding="utf-8")

    def test_player_animation_failure_ranks_player_family_first(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = root / "pack"
            self._write_pack(pack)
            self._write_queue(root)
            self._write_sprint(root)
            plan = locator.build_plan(root, pack, "player_movement", "ANIMATION_SEAM", top=10)
            self.assertEqual("TARGET_CANDIDATES_READY", plan["status"])
            self.assertGreaterEqual(plan["candidate_count"], 3)
            first = plan["candidates"][0]
            self.assertEqual("PLAYER", first["group"])
            self.assertEqual("2E", first["tile_id"])
            self.assertTrue(first["in_current_sprint"])
            self.assertIn("animation-family", first["reasons"])
            self.assertEqual("[SWIR_TARGET tile=2E palette=FF16360F]", first["target_tag"])

    def test_world_case_prefers_world_even_when_player_is_current_sprint(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = root / "pack"
            self._write_pack(pack)
            self._write_queue(root)
            self._write_sprint(root)
            plan = locator.build_plan(root, pack, "world_route_1", "MISSING_HD", top=10)
            self.assertEqual("WORLD", plan["candidates"][0]["group"])
            self.assertEqual("50", plan["candidates"][0]["tile_id"])

    def test_choose_emits_repair_compatible_target_and_context(self) -> None:
        plan = {
            "schema": locator.SCHEMA,
            "pack_fingerprint": "abc",
            "case_key": "bosses",
            "failure_category": "WRONG_PALETTE",
            "candidates": [{
                "rank": 1,
                "group": "BOSS",
                "tile_id": "AA",
                "palette": "BB",
                "family": "BOSS::AA::BB",
                "conditions": ["boss_phase_2"],
                "target_tag": "[SWIR_TARGET tile=AA palette=BB]",
            }],
        }
        selected = locator.choose(plan, 1)
        self.assertEqual(locator.SELECTION_SCHEMA, selected["schema"])
        self.assertEqual("[SWIR_TARGET tile=AA palette=BB]", selected["target_tag"])
        self.assertIn("family=BOSS::AA::BB", selected["context_note"])
        self.assertIn("boss_phase_2", selected["context_note"])

    def test_outputs_are_metadata_only_without_absolute_paths_or_pixels(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = root / "pack"
            self._write_pack(pack)
            self._write_queue(root)
            plan = locator.build_plan(root, pack, "enemies", "WRONG_PALETTE", top=5)
            outputs = locator.write_plan(plan, root / "reports")
            payload = json.loads((root / "reports" / "REGRESSION_DEFECT_TARGETS.json").read_text(encoding="utf-8"))
            text = json.dumps(payload)
            self.assertNotIn(str(root.resolve()), text)
            self.assertTrue(payload["privacy_contract"]["metadata_only"])
            self.assertFalse(payload["privacy_contract"]["capture_pixels"])
            self.assertTrue((root / "reports" / Path(outputs["csv"]).name).is_file())

    def test_non_art_categories_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = root / "pack"
            self._write_pack(pack)
            with self.assertRaisesRegex(locator.DefectLocatorError, "only for art-repair"):
                locator.build_plan(root, pack, "player_movement", "CAPTURE_GAP")

    def test_windows_guided_runner_injects_selected_target_into_fail_notes(self) -> None:
        source = (WINDOWS / "Guided_Regression_Playtest.ps1").read_text(encoding="utf-8")
        self.assertIn("regression_defect_locator.py", source)
        self.assertIn("DEFECT TARGET LOCATOR", source)
        self.assertIn("Select-DefectTarget $case $category", source)
        self.assertIn("$target.target_tag", source)
        self.assertIn("$target.context_note", source)
        self.assertIn("'--failure-notes', $failure", source)
        self.assertLess(source.index("$target = Select-DefectTarget"), source.index("'--failure-notes', $failure"))


if __name__ == "__main__":
    unittest.main()
