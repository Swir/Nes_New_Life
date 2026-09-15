from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
TOOLS = PROJECT / "tools"
WINDOWS = PROJECT / "windows"
sys.path.insert(0, str(TOOLS))

import regression_failure_router as router


class RegressionFailureRouterTests(unittest.TestCase):
    def _status(self, *, state="FAIL", category="ANIMATION_SEAM", key="player_movement", gate="BLOCKED"):
        case = None if gate == "PASS" else {
            "order": 2,
            "key": key,
            "label": "Player movement",
            "state": state,
            "failure_category": category,
            "failure_notes": "visible defect",
        }
        return {
            "pack_fingerprint": "fp",
            "gate": gate,
            "counts": {"PASS": 0, "FAIL": 1 if state == "FAIL" else 0, "STALE": 0, "PENDING": 9},
            "next_case": case,
        }

    def test_art_fail_routes_to_transactional_repair_loop(self):
        for category in sorted(router.ART_CATEGORIES):
            with self.subTest(category=category), patch.object(router, "cockpit_status", return_value=self._status(category=category)):
                result = router.build_route(Path("root"), Path("pack"))
                self.assertEqual("ROUTE_ART_REPAIR", result["state"])
                self.assertEqual("Regression_Repair_Loop.bat", result["launcher"])

    def test_capture_gap_routes_to_targeted_recovery(self):
        with patch.object(router, "cockpit_status", return_value=self._status(category="CAPTURE_GAP", key="bosses")):
            result = router.build_route(Path("root"), Path("pack"))
        self.assertEqual("ROUTE_CAPTURE_GAP_RECOVERY", result["state"])
        self.assertEqual("Regression_Capture_Gap_Recovery.bat", result["launcher"])

    def test_mapping_routes_to_mapping_workbench(self):
        with patch.object(router, "cockpit_status", return_value=self._status(category="MAPPING")):
            result = router.build_route(Path("root"), Path("pack"))
        self.assertEqual("ROUTE_MAPPING_REPAIR", result["state"])
        self.assertEqual("Regression_Mapping_Repair.bat", result["launcher"])

    def test_scale_filter_routes_to_runtime_playtest_repair(self):
        with patch.object(router, "cockpit_status", return_value=self._status(category="SCALE_OR_FILTER")):
            result = router.build_route(Path("root"), Path("pack"))
        self.assertEqual("ROUTE_RUNTIME_REPAIR", result["state"])
        self.assertEqual("Build_HD_Playtest.bat", result["launcher"])

    def test_no_fail_routes_to_guided_regression(self):
        with patch.object(router, "cockpit_status", return_value=self._status(state="PENDING", category="")):
            result = router.build_route(Path("root"), Path("pack"))
        self.assertEqual("ROUTE_GUIDED_REGRESSION", result["state"])
        self.assertEqual("Guided_Regression_Playtest.bat", result["launcher"])

    def test_complete_regression_routes_to_release_gate(self):
        status = self._status(state="PASS", gate="PASS")
        status["counts"] = {"PASS": 10, "FAIL": 0, "STALE": 0, "PENDING": 0}
        with patch.object(router, "cockpit_status", return_value=status):
            result = router.build_route(Path("root"), Path("pack"))
        self.assertEqual("REGRESSION_COMPLETE", result["state"])
        self.assertEqual("Final_Release_Gate.bat", result["launcher"])

    def test_router_windows_dispatcher_has_all_authoritative_paths(self):
        source = (WINDOWS / "Regression_Failure_Router.ps1").read_text(encoding="utf-8")
        for state in (
            "ROUTE_CAPTURE_GAP_RECOVERY",
            "ROUTE_MAPPING_REPAIR",
            "ROUTE_ART_REPAIR",
            "ROUTE_RUNTIME_REPAIR",
            "ROUTE_GUIDED_REGRESSION",
            "REGRESSION_COMPLETE",
        ):
            self.assertIn(state, source)
        self.assertIn("Regression_Failure_Router", source)

    def test_mapping_workbench_backs_up_validates_and_never_clears_regression(self):
        source = (WINDOWS / "Regression_Mapping_Repair.ps1").read_text(encoding="utf-8")
        self.assertIn("mapping-repair-backups", source)
        self.assertIn("validate_hdpack.py", source)
        self.assertIn("Get-FileHash", source)
        self.assertIn("does NOT clear the regression case", source)


if __name__ == "__main__":
    unittest.main()
