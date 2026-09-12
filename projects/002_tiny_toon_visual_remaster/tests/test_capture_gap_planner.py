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

from capture_gap_planner import build_capture_queue, capture_profile, compare_profiles, write_outputs  # noqa: E402
from capture_mission_control import default_manifest  # noqa: E402


class CaptureGapPlannerTests(unittest.TestCase):
    @staticmethod
    def _write_pack(folder: Path, include_jump: bool = False, include_boss_hit: bool = True) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        image = Image.new("RGBA", (192, 32), (0, 0, 0, 0))
        colors = [(220, 80, 60, 255), (70, 150, 240, 255), (100, 220, 120, 255), (240, 180, 50, 255), (160, 80, 220, 255), (220, 220, 220, 255)]
        for index, color in enumerate(colors):
            for y in range(32):
                for x in range(index * 32, (index + 1) * 32):
                    image.putpixel((x, y), color)
        image.save(folder / "tiles.png")
        lines = [
            "<ver>106", "<scale>4", "<img>tiles.png",
            "[hero_idle]<tile>0,10,FF000001,0,0,1,N",
            "[hero_walk_f1]<tile>0,11,FF000001,32,0,1,N",
            "[boss_alpha_intro]<tile>0,20,FF000002,64,0,1,N",
            "[boss_alpha_attack_f1]<tile>0,21,FF000002,96,0,1,N",
        ]
        if include_jump:
            lines.append("[hero_jump_f1]<tile>0,12,FF000001,128,0,1,N")
        if include_boss_hit:
            lines.append("[boss_alpha_hit]<tile>0,22,FF000002,160,0,1,N")
        (folder / "hires.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    @staticmethod
    def _write_queue(path: Path) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["tile_id", "palette", "art_group"])
            for tile in ("10", "11", "12"):
                writer.writerow([tile, "FF000001", "PLAYER"])
            for tile in ("20", "21", "22"):
                writer.writerow([tile, "FF000002", "BOSS"])

    def test_profile_surfaces_advisory_player_and_boss_state_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = root / "pack"
            queue = root / "queue.csv"
            self._write_pack(pack, include_jump=False)
            self._write_queue(queue)
            profile = capture_profile(pack, queue)
            self.assertIn("HERO", profile)
            self.assertIn("BOSS_ALPHA", profile)
            self.assertEqual(profile["HERO"]["art_group"], "PLAYER")
            self.assertIn("jump", profile["HERO"]["missing_expected_states"])
            self.assertIn("death", profile["BOSS_ALPHA"]["missing_expected_states"])

    def test_compare_detects_progress_and_coverage_regression(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            first = root / "first"
            second = root / "second"
            queue = root / "queue.csv"
            self._write_queue(queue)
            self._write_pack(first, include_jump=False, include_boss_hit=True)
            self._write_pack(second, include_jump=True, include_boss_hit=False)
            old = capture_profile(first, queue)
            new = capture_profile(second, queue)
            comparison = compare_profiles(old, new)
            self.assertTrue(comparison["progressed"])
            hero = next(item for item in comparison["family_changes"] if item["family"] == "HERO")
            self.assertIn("jump", hero["added_states"])
            boss = next(item for item in comparison["family_changes"] if item["family"] == "BOSS_ALPHA")
            self.assertIn("hit", boss["removed_states"])
            self.assertTrue(any(item["family"] == "BOSS_ALPHA" for item in comparison["regressions"]))

    def test_capture_next_prioritizes_regression_and_pending_missions(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            first = root / "first"
            second = root / "second"
            queue = root / "queue.csv"
            manifest = root / "missions.json"
            self._write_queue(queue)
            self._write_pack(first, include_jump=False, include_boss_hit=True)
            self._write_pack(second, include_jump=True, include_boss_hit=False)
            manifest.write_text(json.dumps(default_manifest(), indent=2), encoding="utf-8")
            result = build_capture_queue(second, queue, first, queue, manifest)
            self.assertGreater(len(result["queue"]), 0)
            self.assertEqual(result["queue"][0]["kind"], "CAPTURE_REGRESSION")
            self.assertTrue(any(row["kind"] == "MISSION" for row in result["queue"]))
            self.assertTrue(any(row["kind"] == "STATE_GAP" and row["art_group"] == "BOSS" for row in result["queue"]))

    def test_outputs_are_metadata_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = root / "pack"
            queue = root / "queue.csv"
            output = root / "out"
            self._write_pack(pack)
            self._write_queue(queue)
            result = build_capture_queue(pack, queue)
            paths = write_outputs(result, output)
            self.assertTrue(Path(paths["json"]).is_file())
            self.assertTrue(Path(paths["csv"]).is_file())
            self.assertTrue(Path(paths["html"]).is_file())
            self.assertEqual(list(output.glob("*.png")), [])


if __name__ == "__main__":
    unittest.main()
