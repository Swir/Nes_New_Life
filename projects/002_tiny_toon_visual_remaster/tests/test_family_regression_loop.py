from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import family_regression_loop as mod


class FamilyRegressionLoopTests(unittest.TestCase):
    def regression(self, *, state: str | None = "PENDING", category: str = "") -> dict:
        row = None if state is None else {
            "order": 2,
            "key": "player_movement",
            "label": "Player movement / transitions",
            "state": state,
            "failure_category": category,
            "failure_notes": "visible seam" if state == "FAIL" else "",
        }
        passes = 10 if row is None else 4
        return {"gate": "PASS" if row is None else "BLOCKED", "total": 10, "counts": {"PASS": passes, "FAIL": 1 if state == "FAIL" else 0, "STALE": 1 if state == "STALE" else 0, "PENDING": 1 if state == "PENDING" else 0}, "next_case": row}

    def fullscreen(self, gate: str = "PASS") -> dict:
        return {"gate": gate, "fullscreen_verified": gate == "PASS", "fingerprint_matches": gate == "PASS"}

    def test_fullscreen_must_match_before_regression(self) -> None:
        result = mod.decide_next(self.regression(), self.fullscreen("BLOCKED"), None)
        self.assertEqual(result["state"], "FULLSCREEN_EVIDENCE_REQUIRED")
        self.assertEqual(result["launcher"], "Build_HD_Playtest.bat")

    def test_fail_is_always_repaired_before_pending_cases(self) -> None:
        active = {"family": "PLAYER_RUN", "priority": 1}
        result = mod.decide_next(self.regression(state="FAIL", category="ANIMATION_SEAM"), self.fullscreen(), active)
        self.assertEqual(result["state"], "REGRESSION_REPAIR_REQUIRED")
        self.assertIn("transition", result["action"].lower())
        self.assertEqual(result["active_family"]["family"], "PLAYER_RUN")

    def test_capture_gap_routes_back_to_capture_review(self) -> None:
        result = mod.decide_next(self.regression(state="FAIL", category="CAPTURE_GAP"), self.fullscreen(), None)
        self.assertEqual(result["launcher"], "Capture_Review_Director.bat")

    def test_pending_or_stale_requires_real_mesen_verification(self) -> None:
        for state in ("PENDING", "STALE"):
            result = mod.decide_next(self.regression(state=state), self.fullscreen(), None)
            self.assertEqual(result["state"], "REGRESSION_VERIFICATION_REQUIRED")
            self.assertEqual(result["launcher"], "Final_Regression_Cockpit.bat")

    def test_ten_of_ten_pass_advances_to_next_family(self) -> None:
        result = mod.decide_next(self.regression(state=None), self.fullscreen(), None)
        self.assertEqual(result["state"], "CURRENT_BUILD_REGRESSION_PASS")
        self.assertIn("next highest-impact family", result["action"])

    def test_run_loop_does_not_autopilot_until_current_build_regression_passes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            capture = root / "capture"
            runtime = root / "runtime"
            capture.mkdir(); runtime.mkdir()
            with patch.object(mod, "build_regression", return_value={**self.regression(), "pack_fingerprint": "fp"}), \
                 patch.object(mod, "fullscreen_evidence_status", return_value=self.fullscreen()), \
                 patch.object(mod, "run_autopilot") as autopilot:
                result = mod.run_loop(root, capture, runtime, prepare_next_family=True)
            autopilot.assert_not_called()
            self.assertEqual(result["decision"]["state"], "REGRESSION_VERIFICATION_REQUIRED")

    def test_regression_pass_may_prepare_next_family(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            capture = root / "capture"
            runtime = root / "runtime"
            kit = root / "Artwork" / "CurrentImpactSprint"
            capture.mkdir(); runtime.mkdir(); kit.mkdir(parents=True)
            with patch.object(mod, "build_regression", return_value={**self.regression(state=None), "pack_fingerprint": "fp"}), \
                 patch.object(mod, "fullscreen_evidence_status", return_value=self.fullscreen()), \
                 patch.object(mod, "run_autopilot", return_value={"status": "HIGH_IMPACT_SPRINT_READY", "allowed": True, "capture_fingerprint_sha256": "cap", "visual_completion": {}, "sprint": {"status": "READY"}}), \
                 patch.object(mod, "_safe_family", return_value={"status": "ACTIVE_FAMILY_READY", "family": "BOSS_FINAL", "priority": 1, "members": 4, "board": "family.png", "editable_dir": "editable", "editable_files": []}):
                result = mod.run_loop(root, capture, runtime, prepare_next_family=True)
            self.assertEqual(result["decision"]["state"], "NEXT_FAMILY_READY")
            self.assertEqual(result["active_family"]["family"], "BOSS_FINAL")

    def test_report_is_metadata_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            result = {
                "runtime_fingerprint": "f" * 64,
                "fullscreen": {"gate": "PASS"},
                "regression": {"counts": {"PASS": 2}, "total": 10},
                "decision": {"state": "REGRESSION_VERIFICATION_REQUIRED", "action": "Verify in game", "launcher": "Final_Regression_Cockpit.bat"},
                "active_family": None,
                "next_art_autopilot": None,
                "privacy_contract": {"metadata_only": True, "absolute_local_paths": False},
            }
            outputs = mod._write_outputs(result, Path(td))
            payload = json.loads((Path(td) / outputs["json"]).read_text(encoding="utf-8"))
            self.assertTrue(payload["privacy_contract"]["metadata_only"])
            self.assertNotIn(str(Path(td).resolve()), json.dumps(payload))


if __name__ == "__main__":
    unittest.main()
