from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
WINDOWS = ROOT / "windows"
sys.path.insert(0, str(TOOLS))

from final_regression_cockpit import cockpit_status, record_case_result  # noqa: E402
from regression_recovery_session import plan_retest, record_retest, sync_session  # noqa: E402
from release_candidate import REGRESSION_CASES  # noqa: E402


class RegressionRecoverySessionTests(unittest.TestCase):
    @staticmethod
    def _write_pack(folder: Path, color=(20, 70, 150, 255)) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        Image.new("RGBA", (32, 32), color).save(folder / "tiles.png")
        (folder / "hires.txt").write_text(
            "<ver>106\n<scale>4\n<img>tiles.png\n[hero_player]<tile>0,2E,FF16360F,0,0,1,N\n",
            encoding="utf-8",
        )

    def test_fail_starts_persistent_repair_session(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); pack = root / "pack"; manifest = root / "regression.json"; state = root / "state.json"
            self._write_pack(pack)
            case = REGRESSION_CASES[1][0]
            record_case_result(manifest, case, pack, "FAIL", failure_category="ANIMATION_SEAM", failure_notes="landing seam")
            session = sync_session(manifest, pack, state)
            self.assertEqual("REPAIR_REQUIRED", session["phase"])
            self.assertEqual(case, session["failed_case"]["key"])
            self.assertEqual("Regression_Repair_Loop.bat", session["route_launcher"])
            saved = json.loads(state.read_text(encoding="utf-8"))
            self.assertEqual(session["session_id"], saved["session_id"])
            self.assertNotIn("rom", state.read_text(encoding="utf-8").lower())

    def test_runtime_change_forces_same_case_retest_even_if_earlier_case_is_stale(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); pack = root / "pack"; manifest = root / "regression.json"; state = root / "state.json"
            self._write_pack(pack)
            first = REGRESSION_CASES[0][0]
            failed = REGRESSION_CASES[2][0]
            record_case_result(manifest, first, pack, "PASS")
            record_case_result(manifest, failed, pack, "FAIL", failure_category="WRONG_PALETTE", failure_notes="damage palette")
            started = sync_session(manifest, pack, state)
            self._write_pack(pack, color=(180, 30, 90, 255))
            normal = cockpit_status(manifest, pack)
            self.assertEqual(first, normal["next_case"]["key"])
            self.assertEqual("STALE", normal["next_case"]["state"])
            resumed = sync_session(manifest, pack, state)
            self.assertEqual("RETEST_REQUIRED", resumed["phase"])
            self.assertEqual(failed, resumed["failed_case"]["key"])
            plan = plan_retest(manifest, pack, state)
            self.assertEqual(failed, plan["case"]["key"])
            self.assertNotEqual(started["source_fingerprint"], plan["planned_fingerprint"])

    def test_same_case_pass_completes_recovery_without_passing_other_cases(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); pack = root / "pack"; manifest = root / "regression.json"; state = root / "state.json"
            self._write_pack(pack)
            case = REGRESSION_CASES[3][0]
            record_case_result(manifest, case, pack, "FAIL", failure_category="MISSING_HD", failure_notes="background hole")
            sync_session(manifest, pack, state)
            self._write_pack(pack, color=(60, 170, 90, 255))
            sync_session(manifest, pack, state)
            result = record_retest(manifest, pack, state, "PASS", notes="verified after repair")
            self.assertEqual("COMPLETE", result["recovery"]["phase"])
            status = cockpit_status(manifest, pack)
            row = next(item for item in status["cases"] if item["key"] == case)
            self.assertEqual("PASS", row["state"])
            self.assertLess(status["counts"]["PASS"], 10)

    def test_same_case_fail_rebases_repair_cycle_to_new_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); pack = root / "pack"; manifest = root / "regression.json"; state = root / "state.json"
            self._write_pack(pack)
            case = REGRESSION_CASES[4][0]
            record_case_result(manifest, case, pack, "FAIL", failure_category="MAPPING", failure_notes="wrong mapping")
            initial = sync_session(manifest, pack, state)
            self._write_pack(pack, color=(90, 90, 220, 255))
            sync_session(manifest, pack, state)
            result = record_retest(manifest, pack, state, "FAIL", category="MAPPING", failure_notes="still wrong")
            recovery = result["recovery"]
            self.assertEqual("REPAIR_REQUIRED", recovery["phase"])
            self.assertEqual("Regression_Mapping_Repair.bat", recovery["route_launcher"])
            self.assertNotEqual(initial["source_fingerprint"], recovery["source_fingerprint"])
            self.assertEqual(recovery["source_fingerprint"], recovery["current_fingerprint"])

    def test_windows_resume_uses_verified_fullscreen_and_router_respects_retest_lock(self) -> None:
        resume = (WINDOWS / "Resume_Regression_Recovery.ps1").read_text(encoding="utf-8")
        router = (WINDOWS / "Regression_Failure_Router.ps1").read_text(encoding="utf-8")
        self.assertIn("RETEST_REQUIRED", resume)
        self.assertIn("launch_remaster.ps1", resume)
        self.assertIn("FULLSCREEN_PLAYTEST.json", resume)
        self.assertIn("Perform ONLY the remembered case", resume)
        self.assertIn("regression-recovery-session.json", router)
        self.assertIn("RECOVERY LOCK ACTIVE", router)
        self.assertIn("Resume_Regression_Recovery.ps1", router)

    def test_authoritative_studio_auto_surfaces_recovery_state(self) -> None:
        studio = (TOOLS / "AuthoritativeProductionStudio.py").read_text(encoding="utf-8")
        self.assertIn("refresh_regression_recovery_state", studio)
        self.assertIn("CTRL+ALT+F11  RESUME REGRESSION RECOVERY", studio)
        self.assertIn("regression-recovery-session.json", studio)
        self.assertIn("Normal regression ordering must not bypass", studio)


if __name__ == "__main__":
    unittest.main()
