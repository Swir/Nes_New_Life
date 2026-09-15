from __future__ import annotations

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

from final_regression_cockpit import record_case_result  # noqa: E402
from regression_auto_continue import build_plan  # noqa: E402
from release_candidate import REGRESSION_CASES  # noqa: E402


class RegressionAutoContinueTests(unittest.TestCase):
    @staticmethod
    def _write_pack(folder: Path, color=(20, 70, 150, 255)) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        Image.new("RGBA", (32, 32), color).save(folder / "tiles.png")
        (folder / "hires.txt").write_text(
            "<ver>106\n<scale>4\n<img>tiles.png\n[hero_player]<tile>0,2E,FF16360F,0,0,1,N\n",
            encoding="utf-8",
        )

    def test_empty_regression_starts_first_guided_case(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); pack = root / "pack"; manifest = root / "regression.json"; recovery = root / "recovery.json"
            self._write_pack(pack)
            plan = build_plan(manifest, pack, recovery)
            self.assertEqual("PLAYTEST_CASE_REQUIRED", plan["state"])
            self.assertEqual(REGRESSION_CASES[0][0], plan["case"]["key"])
            self.assertEqual("Guided_Regression_Playtest.bat", plan["launcher"])

    def test_current_fail_is_routed_to_persistent_repair_before_next_case(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); pack = root / "pack"; manifest = root / "regression.json"; recovery = root / "recovery.json"
            self._write_pack(pack)
            first = REGRESSION_CASES[0][0]
            record_case_result(manifest, first, pack, "FAIL", failure_category="ANIMATION_SEAM", failure_notes="jump seam")
            plan = build_plan(manifest, pack, recovery)
            self.assertEqual("RECOVERY_REPAIR_REQUIRED", plan["state"])
            self.assertEqual(first, plan["case"]["key"])
            self.assertEqual("Resume_Regression_Recovery.bat", plan["launcher"])

    def test_repaired_fingerprint_forces_same_failed_case_before_earlier_stale_case(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); pack = root / "pack"; manifest = root / "regression.json"; recovery = root / "recovery.json"
            self._write_pack(pack)
            first = REGRESSION_CASES[0][0]
            second = REGRESSION_CASES[1][0]
            record_case_result(manifest, first, pack, "PASS", notes="verified")
            record_case_result(manifest, second, pack, "FAIL", failure_category="WRONG_PALETTE", failure_notes="landing palette")
            before = build_plan(manifest, pack, recovery)
            self.assertEqual("RECOVERY_REPAIR_REQUIRED", before["state"])

            self._write_pack(pack, color=(190, 40, 30, 255))
            repaired = build_plan(manifest, pack, recovery)
            self.assertEqual("SAME_CASE_RETEST_REQUIRED", repaired["state"])
            self.assertEqual(second, repaired["case"]["key"])

    def test_after_same_case_pass_normal_order_revalidates_stale_prior_passes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); pack = root / "pack"; manifest = root / "regression.json"; recovery = root / "recovery.json"
            self._write_pack(pack)
            first = REGRESSION_CASES[0][0]
            second = REGRESSION_CASES[1][0]
            record_case_result(manifest, first, pack, "PASS")
            record_case_result(manifest, second, pack, "FAIL", failure_category="TRANSPARENCY", failure_notes="halo")
            build_plan(manifest, pack, recovery)
            self._write_pack(pack, color=(80, 160, 40, 255))
            same_case = build_plan(manifest, pack, recovery)
            self.assertEqual(second, same_case["case"]["key"])
            record_case_result(manifest, second, pack, "PASS", notes="same-case retest")

            resumed = build_plan(manifest, pack, recovery)
            self.assertEqual("PLAYTEST_CASE_REQUIRED", resumed["state"])
            self.assertEqual(first, resumed["case"]["key"])
            self.assertEqual("STALE", resumed["case"]["prior_state"])

    def test_ten_current_build_passes_dispatch_final_release_gate(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); pack = root / "pack"; manifest = root / "regression.json"; recovery = root / "recovery.json"
            self._write_pack(pack)
            for key, _label in REGRESSION_CASES:
                record_case_result(manifest, key, pack, "PASS", notes="verified in MesenCE")
            plan = build_plan(manifest, pack, recovery)
            self.assertEqual("REGRESSION_COMPLETE", plan["state"])
            self.assertEqual("Final_Release_Gate.bat", plan["launcher"])
            self.assertEqual(10, plan["counts"]["PASS"])

    def test_windows_loop_delegates_real_observation_and_stops_at_repair_boundary(self) -> None:
        source = (WINDOWS / "Auto_Continue_Final_Regression.ps1").read_text(encoding="utf-8")
        self.assertIn("Guided_Regression_Playtest.ps1", source)
        self.assertIn("Resume_Regression_Recovery.ps1", source)
        self.assertIn("Final_Release_Gate.bat", source)
        self.assertIn("RECOVERY_REPAIR_REQUIRED", source)
        self.assertIn("SAME_CASE_RETEST_REQUIRED", source)
        self.assertIn("exceeded 30 orchestration iterations", source)
        self.assertNotIn("record_case_result", source)

    def test_outputs_are_metadata_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); pack = root / "pack"; manifest = root / "regression.json"; recovery = root / "recovery.json"
            self._write_pack(pack)
            plan = build_plan(manifest, pack, recovery)
            blob = json.dumps(plan)
            self.assertNotIn(".png", blob.lower())
            self.assertNotIn("rom_path", blob.lower())


if __name__ == "__main__":
    unittest.main()
