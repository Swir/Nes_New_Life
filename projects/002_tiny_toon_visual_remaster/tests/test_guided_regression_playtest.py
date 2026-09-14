from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
TOOLS = PROJECT / "tools"
WINDOWS = PROJECT / "windows"
sys.path.insert(0, str(TOOLS))

import guided_regression_playtest as guided


class GuidedRegressionPlaytestTests(unittest.TestCase):
    def status(self, *, state="PENDING", key="boot_title_menu", category=""):
        counts = {"PASS": 0, "FAIL": 0, "STALE": 0, "PENDING": 10}
        if state != "PENDING":
            counts["PENDING"] -= 1
            counts[state] += 1
        return {
            "pack_fingerprint": "abc",
            "gate": "BLOCKED",
            "counts": counts,
            "next_case": {
                "order": 1,
                "key": key,
                "label": "case label",
                "state": state,
                "failure_category": category,
                "failure_notes": "visible problem" if category else "",
            },
        }

    def test_pending_case_contains_specific_route_and_cues(self):
        with patch.object(guided, "cockpit_status", return_value=self.status()), patch.object(guided, "pack_fingerprint", return_value="abc"):
            result = guided.build_session(Path("manifest"), Path("pack"))
        self.assertEqual("PLAYTEST_CASE_REQUIRED", result["state"])
        self.assertEqual("boot_title_menu", result["next_case"]["key"])
        self.assertTrue(result["next_case"]["route"])
        self.assertGreaterEqual(len(result["next_case"]["cues"]), 3)
        self.assertIn("auto-PASS", result["policy"])

    def test_failed_case_is_routed_to_repair_before_pending_work(self):
        with patch.object(guided, "cockpit_status", return_value=self.status(state="FAIL", key="player_movement", category="ANIMATION_SEAM")), patch.object(guided, "pack_fingerprint", return_value="abc"):
            result = guided.build_session(Path("manifest"), Path("pack"))
        self.assertEqual("REPAIR_FAILED_CASE", result["state"])
        self.assertIn("animation", result["next_action"].lower())
        self.assertEqual("ANIMATION_SEAM", result["next_case"]["failure_category"])

    def test_capture_gap_failure_routes_back_to_real_capture(self):
        with patch.object(guided, "cockpit_status", return_value=self.status(state="FAIL", key="world_route_2", category="CAPTURE_GAP")), patch.object(guided, "pack_fingerprint", return_value="abc"):
            result = guided.build_session(Path("manifest"), Path("pack"))
        self.assertIn("Capture Review Director", result["next_action"])
        self.assertIn("real gameplay evidence", result["next_action"])

    def test_10_of_10_pass_routes_to_final_release(self):
        complete = {"pack_fingerprint": "abc", "gate": "PASS", "counts": {"PASS": 10, "FAIL": 0, "STALE": 0, "PENDING": 0}, "next_case": None}
        with patch.object(guided, "cockpit_status", return_value=complete), patch.object(guided, "pack_fingerprint", return_value="abc"):
            result = guided.build_session(Path("manifest"), Path("pack"))
        self.assertEqual("REGRESSION_COMPLETE", result["state"])
        self.assertIn("Final Release Gate", result["next_action"])

    def test_record_refuses_out_of_order_case(self):
        with patch.object(guided, "build_session", return_value={"next_case": {"key": "bosses"}, "pack_fingerprint": "abc"}):
            with self.assertRaisesRegex(ValueError, "next authoritative case is bosses"):
                guided.record(Path("manifest"), Path("pack"), "enemies", "PASS")

    def test_record_refuses_fingerprint_drift(self):
        planned = {"next_case": {"key": "bosses"}, "pack_fingerprint": "old"}
        with patch.object(guided, "build_session", return_value=planned), patch.object(guided, "pack_fingerprint", return_value="new"):
            with self.assertRaisesRegex(ValueError, "fingerprint changed"):
                guided.record(Path("manifest"), Path("pack"), "bosses", "PASS")

    def test_record_pass_calls_authoritative_cockpit_recorder(self):
        planned = {"next_case": {"key": "bosses"}, "pack_fingerprint": "abc"}
        complete = {"state": "REGRESSION_COMPLETE", "pack_fingerprint": "abc", "counts": {"PASS": 10, "FAIL": 0, "STALE": 0, "PENDING": 0}, "next_case": None, "next_action": "Final Release Gate"}
        with patch.object(guided, "build_session", side_effect=[planned, complete]), patch.object(guided, "pack_fingerprint", return_value="abc"), patch.object(guided, "record_case_result", return_value={"case": "bosses", "result": "PASS"}) as recorder:
            result = guided.record(Path("manifest"), Path("pack"), "bosses", "PASS")
        recorder.assert_called_once()
        self.assertEqual("REGRESSION_COMPLETE", result["session"]["state"])

    def test_report_is_metadata_only(self):
        session = {
            "schema": guided.SCHEMA,
            "state": "PLAYTEST_CASE_REQUIRED",
            "pack_fingerprint": "f" * 64,
            "counts": {"PASS": 0, "FAIL": 0, "STALE": 0, "PENDING": 10},
            "next_case": {"order": 1, "key": "boot_title_menu", "label": "Boot", "prior_state": "PENDING", "failure_category": "", "failure_notes": "", "route": "boot", "cues": ["look"]},
            "next_action": "test",
            "policy": "No auto-PASS",
        }
        with tempfile.TemporaryDirectory() as td:
            outputs = guided.write_outputs(session, Path(td))
            data = json.loads((Path(td) / "GUIDED_REGRESSION_PLAYTEST.json").read_text(encoding="utf-8"))
            self.assertNotIn(str(Path(td).resolve()), json.dumps(data))
            self.assertTrue((Path(td) / "GUIDED_REGRESSION_PLAYTEST.html").is_file())
            self.assertIn("dashboard", outputs)

    def test_windows_launcher_enforces_verified_fullscreen_and_manual_result(self):
        source = (WINDOWS / "Guided_Regression_Playtest.ps1").read_text(encoding="utf-8")
        self.assertIn("launch_remaster.ps1", source)
        self.assertIn("-PackDir $RuntimePack", source)
        self.assertIn("P = PASS after real visual verification", source)
        self.assertIn("Failure categories", source)
        self.assertIn("CAPTURE_GAP", source)
        self.assertIn("RunAll", source)

    def test_every_authoritative_case_has_guidance(self):
        from release_candidate import REGRESSION_CASES
        self.assertEqual({key for key, _ in REGRESSION_CASES}, set(guided.CASE_GUIDANCE))


if __name__ == "__main__":
    unittest.main()
