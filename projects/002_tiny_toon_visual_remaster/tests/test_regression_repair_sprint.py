from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

PROJECT = Path(__file__).resolve().parents[1]
TOOLS = PROJECT / "tools"
WINDOWS = PROJECT / "windows"
sys.path.insert(0, str(TOOLS))

import regression_repair_sprint as repair


class RegressionRepairSprintTests(unittest.TestCase):
    def _status(self, category="ANIMATION_SEAM", key="player_movement", fp="oldfp") -> tuple[dict, dict]:
        case = {
            "order": 2,
            "key": key,
            "label": "Player movement",
            "state": "FAIL",
            "failure_category": category,
            "failure_notes": "visible seam",
        }
        return ({"pack_fingerprint": fp, "next_case": case}, case)

    def _write_workspace_and_sprint(self, root: Path) -> None:
        workspace = root / "Artwork" / "MasterWorkspace"
        (workspace / "editable").mkdir(parents=True)
        (workspace / "original").mkdir(parents=True)
        (workspace / "MASTER_TILES.json").write_text("{}", encoding="utf-8")
        image = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        for y in range(8, 24):
            for x in range(8, 24):
                image.putpixel((x, y), (100, 180, 230, 255))
        image.save(workspace / "editable" / "hero.png")
        image.save(workspace / "original" / "hero.png")
        sprint = root / "Artwork" / "CurrentImpactSprint"
        sprint.mkdir(parents=True)
        (sprint / repair.MANIFEST_NAME).write_text(json.dumps({
            "schema": 4,
            "items": [{
                "priority": 1,
                "priority_score": 100,
                "impact_score": 100,
                "group": "PLAYER",
                "tile_id": "2E",
                "palette": "FF16360F",
                "seed_tile_id": "2E",
                "seed_palette": "FF16360F",
                "uses": 4,
                "condition_count": 2,
                "visual_variants": 1,
                "reasons": ["PLAYER"],
                "master_file": "hero.png",
                "kit_file": "001_hero.png",
            }],
        }), encoding="utf-8")

    def test_non_art_capture_gap_routes_without_creating_sprint(self):
        status, case = self._status(category="CAPTURE_GAP", key="world_route_2")
        with tempfile.TemporaryDirectory() as td, patch.object(repair, "_current_failure", return_value=(status, case)):
            result = repair.prepare_repair_sprint(Path(td), Path(td) / "pack")
            self.assertEqual("CAPTURE_REVIEW_REQUIRED", result["status"])
            self.assertFalse(result["repair_sprint_created"])
            self.assertFalse((Path(td) / "Artwork" / "CurrentRepairSprint").exists())

    def test_prepare_reexports_selected_family_from_current_masterworkspace(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_workspace_and_sprint(root)
            status, case = self._status()
            active = {"family": "PLAYER::2E::FF16360F", "priority": 1, "members": 1, "editable_files": ["001_hero.png"]}
            with patch.object(repair, "_current_failure", return_value=(status, case)), patch.object(repair, "resolve_active_family_workbench", return_value=active):
                result = repair.prepare_repair_sprint(root, root / "runtime")
            self.assertEqual("REPAIR_SPRINT_READY", result["status"])
            self.assertEqual(1, result["repair_items"])
            kit = root / "Artwork" / "CurrentRepairSprint"
            manifest = json.loads((kit / repair.MANIFEST_NAME).read_text(encoding="utf-8"))
            self.assertEqual("failed-regression-minimal-repair", manifest["selection_mode"])
            self.assertEqual("oldfp", manifest["expected_runtime_fingerprint"])
            self.assertTrue((kit / "editable" / manifest["items"][0]["kit_file"]).is_file())
            self.assertTrue((kit / "reference" / manifest["items"][0]["kit_file"]).is_file())
            self.assertNotIn(str(root.resolve()), json.dumps(result))

    def test_explicit_tile_hint_expands_only_matching_family(self):
        case = {"key": "enemies", "failure_notes": "[SWIR_TARGET tile=AA palette=BB] wrong frame"}
        items = [
            {"group": "ENEMY", "tile_id": "AA", "palette": "BB", "seed_tile_id": "AA", "seed_palette": "BB", "kit_file": "a"},
            {"group": "ENEMY", "tile_id": "AB", "palette": "BC", "seed_tile_id": "AA", "seed_palette": "BB", "kit_file": "b"},
            {"group": "ENEMY", "tile_id": "CC", "palette": "DD", "seed_tile_id": "CC", "seed_palette": "DD", "kit_file": "c"},
        ]
        selected = repair.select_repair_items(case, {"items": items}, None)
        self.assertEqual({"a", "b"}, {row["kit_file"] for row in selected})

    def test_finish_refuses_case_or_fingerprint_drift_before_transaction(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            kit = root / "Artwork" / "CurrentRepairSprint"
            kit.mkdir(parents=True)
            (kit / repair.MANIFEST_NAME).write_text(json.dumps({
                "selection_mode": "failed-regression-minimal-repair",
                "expected_runtime_fingerprint": "oldfp",
                "failed_case": {"key": "player_movement", "label": "Player", "failure_category": "ANIMATION_SEAM"},
                "items": [],
            }), encoding="utf-8")
            status, case = self._status(fp="newfp")
            with patch.object(repair, "_current_failure", return_value=(status, case)), patch.object(repair, "transactional_finish_sprint") as tx:
                with self.assertRaisesRegex(repair.RepairSprintError, "fingerprint changed"):
                    repair.finish_repair(root, root / "runtime")
            tx.assert_not_called()

    def test_finish_committed_creates_exact_case_retest_token(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            kit = root / "Artwork" / "CurrentRepairSprint"
            kit.mkdir(parents=True)
            (kit / repair.MANIFEST_NAME).write_text(json.dumps({
                "selection_mode": "failed-regression-minimal-repair",
                "expected_runtime_fingerprint": "oldfp",
                "failed_case": {"key": "player_movement", "label": "Player movement", "failure_category": "ANIMATION_SEAM"},
                "items": [],
            }), encoding="utf-8")
            status, case = self._status()
            tx_result = {"transaction_status": "COMMITTED", "qa_gate": "PASS", "mapping_preserved": True, "committed_files": ["hero.png"]}
            with patch.object(repair, "_current_failure", return_value=(status, case)), patch.object(repair, "transactional_finish_sprint", return_value=tx_result), patch.object(repair, "pack_fingerprint", return_value="newfp"):
                result = repair.finish_repair(root, root / "runtime", output_pack=root / "candidate")
            self.assertEqual("REPAIR_COMMITTED_RETEST_REQUIRED", result["status"])
            token = json.loads((kit / "REPAIR_RETEST_TOKEN.json").read_text(encoding="utf-8"))
            self.assertEqual("player_movement", token["case_key"])
            self.assertEqual("oldfp", token["source_runtime_fingerprint"])
            self.assertEqual("newfp", token["repaired_runtime_fingerprint"])

    def test_retest_requires_original_authoritative_fail_history(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            kit = root / "Artwork" / "CurrentRepairSprint"
            kit.mkdir(parents=True)
            token = {"schema": repair.RETEST_SCHEMA, "case_key": "player_movement", "failure_category": "ANIMATION_SEAM", "source_runtime_fingerprint": "oldfp", "repaired_runtime_fingerprint": "newfp"}
            (kit / "REPAIR_RETEST_TOKEN.json").write_text(json.dumps(token), encoding="utf-8")
            (root / "FINAL_REGRESSION.json").write_text(json.dumps({"history": []}), encoding="utf-8")
            with patch.object(repair, "pack_fingerprint", return_value="newfp"):
                with self.assertRaisesRegex(repair.RepairSprintError, "not backed"):
                    repair.record_retest(root, root / "candidate", "PASS")

    def test_retest_pass_records_target_even_if_full_cockpit_still_has_stale_work(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            kit = root / "Artwork" / "CurrentRepairSprint"
            kit.mkdir(parents=True)
            token = {"schema": repair.RETEST_SCHEMA, "case_key": "player_movement", "failure_category": "ANIMATION_SEAM", "source_runtime_fingerprint": "oldfp", "repaired_runtime_fingerprint": "newfp"}
            (kit / "REPAIR_RETEST_TOKEN.json").write_text(json.dumps(token), encoding="utf-8")
            (root / "FINAL_REGRESSION.json").write_text(json.dumps({"history": [{"case": "player_movement", "result": "FAIL", "pack_fingerprint": "oldfp", "failure_category": "ANIMATION_SEAM"}]}), encoding="utf-8")
            after = {"counts": {"PASS": 1, "FAIL": 0, "STALE": 4, "PENDING": 5}, "gate": "BLOCKED", "next_case": {"key": "boot_title_menu", "state": "STALE"}}
            with patch.object(repair, "pack_fingerprint", return_value="newfp"), patch.object(repair, "record_case_result", return_value={"case": "player_movement", "result": "PASS"}) as recorder, patch.object(repair, "cockpit_status", return_value=after):
                result = repair.record_retest(root, root / "candidate", "PASS")
            recorder.assert_called_once()
            self.assertEqual("REPAIR_RETEST_PASS", result["status"])
            self.assertEqual("BLOCKED", result["cockpit_gate"])
            self.assertIn("all 10", result["roadmap_policy"])

    def test_windows_loop_runs_transactional_finish_and_same_case_retest(self):
        source = (WINDOWS / "Regression_Repair_Loop.ps1").read_text(encoding="utf-8")
        self.assertIn("regression_repair_sprint.py", source)
        self.assertIn("'finish'", source)
        self.assertIn("launch_remaster.ps1", source)
        self.assertIn("Perform ONLY the SAME failed case", source)
        self.assertIn("'retest'", source)
        self.assertIn("verified-fullscreen", source)


if __name__ == "__main__":
    unittest.main()
