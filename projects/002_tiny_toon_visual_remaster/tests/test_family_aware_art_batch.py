from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from family_aware_art_batch import build_family_aware_batch  # noqa: E402


class FamilyAwareArtBatchTests(unittest.TestCase):
    def _workspace(self, root: Path, masters: list[dict], states: list[dict]) -> Path:
        workspace = root / "workspace"
        workspace.mkdir()
        (workspace / "MASTER_TILES.json").write_text(json.dumps({"masters": masters}), encoding="utf-8")
        fields = ["tile_id", "palette", "status", "master_file"]
        with (workspace / "ART_STATE.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(states)
        return workspace

    @staticmethod
    def _master(name: str, tile: str, palette: str, group: str, condition: str) -> dict:
        return {
            "file": name,
            "tile_id": tile,
            "palette": palette,
            "group": group,
            "targets": [{"condition": condition}],
        }

    @staticmethod
    def _seed(tile: str, palette: str, group: str, score: int = 900) -> dict:
        return {
            "tile_id": tile,
            "palette": palette,
            "group": group,
            "status": "TODO",
            "uses": 5,
            "condition_count": 1,
            "visual_variants": 1,
            "impact_score": score,
            "reasons": [f"group:{group.lower()}", "high-reuse"],
        }

    def test_first_character_family_overflows_nominal_batch_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            masters = [
                self._master("hero_a.png", "2E", "AA", "PLAYER", "hero_walk_1"),
                self._master("hero_b.png", "2F", "AA", "PLAYER", "hero_walk_2"),
                self._master("hero_c.png", "30", "AA", "PLAYER", "hero_jump_1"),
            ]
            states = [
                {"tile_id": "2E", "palette": "AA", "status": "TODO", "master_file": "hero_a.png"},
                {"tile_id": "2F", "palette": "AA", "status": "TODO", "master_file": "hero_b.png"},
                {"tile_id": "30", "palette": "AA", "status": "TODO", "master_file": "hero_c.png"},
            ]
            workspace = self._workspace(root, masters, states)
            plan = build_family_aware_batch([self._seed("2E", "AA", "PLAYER")], workspace, 1)
            self.assertEqual(plan["selected_count"], 3)
            self.assertEqual(plan["family_bundle_count"], 1)
            self.assertTrue(plan["bundles"][0]["overflowed_nominal_batch"])
            self.assertEqual({row["tile_id"] for row in plan["selection"]}, {"2E", "2F", "30"})

    def test_already_final_family_peer_is_not_reopened(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            masters = [
                self._master("hero_a.png", "2E", "AA", "PLAYER", "hero_walk_1"),
                self._master("hero_b.png", "2F", "AA", "PLAYER", "hero_walk_2"),
            ]
            states = [
                {"tile_id": "2E", "palette": "AA", "status": "TODO", "master_file": "hero_a.png"},
                {"tile_id": "2F", "palette": "AA", "status": "EDITED", "master_file": "hero_b.png"},
            ]
            workspace = self._workspace(root, masters, states)
            plan = build_family_aware_batch([self._seed("2E", "AA", "PLAYER")], workspace, 5)
            self.assertEqual([row["tile_id"] for row in plan["selection"]], ["2E"])

    def test_palette_sibling_is_bundled_even_without_shared_condition_family(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            masters = [
                self._master("enemy_a.png", "40", "AA", "ENEMY", "rat_walk_1"),
                self._master("enemy_b.png", "40", "BB", "ENEMY", "rat_hurt_1"),
            ]
            states = [
                {"tile_id": "40", "palette": "AA", "status": "TODO", "master_file": "enemy_a.png"},
                {"tile_id": "40", "palette": "BB", "status": "TODO", "master_file": "enemy_b.png"},
            ]
            workspace = self._workspace(root, masters, states)
            plan = build_family_aware_batch([self._seed("40", "AA", "ENEMY")], workspace, 4)
            self.assertEqual(plan["selected_count"], 2)
            peer = next(row for row in plan["selection"] if row["palette"] == "BB")
            self.assertIn("palette-sibling", peer["reasons"])

    def test_world_seed_remains_single_item(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            masters = [self._master("grass.png", "50", "AA", "WORLD", "world_grass")]
            states = [{"tile_id": "50", "palette": "AA", "status": "TODO", "master_file": "grass.png"}]
            workspace = self._workspace(root, masters, states)
            plan = build_family_aware_batch([self._seed("50", "AA", "WORLD")], workspace, 1)
            self.assertEqual(plan["selected_count"], 1)
            self.assertEqual(plan["family_bundle_count"], 0)

    def test_second_family_is_deferred_instead_of_split(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            masters = [
                self._master("hero_a.png", "2E", "AA", "PLAYER", "hero_walk_1"),
                self._master("hero_b.png", "2F", "AA", "PLAYER", "hero_walk_2"),
                self._master("boss_a.png", "60", "CC", "BOSS", "boss_phase_1"),
                self._master("boss_b.png", "61", "CC", "BOSS", "boss_phase_2"),
            ]
            states = [
                {"tile_id": "2E", "palette": "AA", "status": "TODO", "master_file": "hero_a.png"},
                {"tile_id": "2F", "palette": "AA", "status": "TODO", "master_file": "hero_b.png"},
                {"tile_id": "60", "palette": "CC", "status": "TODO", "master_file": "boss_a.png"},
                {"tile_id": "61", "palette": "CC", "status": "TODO", "master_file": "boss_b.png"},
            ]
            workspace = self._workspace(root, masters, states)
            seeds = [self._seed("2E", "AA", "PLAYER", 1000), self._seed("60", "CC", "BOSS", 900)]
            plan = build_family_aware_batch(seeds, workspace, 3)
            self.assertEqual({row["tile_id"] for row in plan["selection"]}, {"2E", "2F"})
            self.assertEqual(plan["deferred_family_count"], 1)
            self.assertEqual(plan["deferred"][0]["seed_tile_id"], "60")


if __name__ == "__main__":
    unittest.main()
