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

import regression_capture_gap_recovery as recovery


class RegressionCaptureGapRecoveryTests(unittest.TestCase):
    def _status(self, *, category: str = "CAPTURE_GAP", key: str = "bosses", fp: str = "runtime-old") -> tuple[dict, dict]:
        case = {
            "order": 7,
            "key": key,
            "label": "Bosses",
            "state": "FAIL",
            "failure_category": category,
            "failure_notes": "unmapped HD frame during second phase",
        }
        return ({"pack_fingerprint": fp, "next_case": case}, case)

    def _acceptance(self, *, fp: str, mission_keys=("bosses_all_phases",), status: str = "VERIFIED_IN_GAME", same: bool = True, regression_count: int = 0) -> dict:
        return {
            "capture_fingerprint_sha256": fp,
            "capture_integrity": {
                "admission_gate": "PASS",
                "regression_count": regression_count,
                "structural_blockers": [],
            },
            "source_counts": {
                "mapping_count": 100,
                "unique_tile_ids": 50,
                "unique_palettes": 10,
                "condition_count": 20,
                "referenced_images": 4,
            },
            "missions": [
                {
                    "key": key,
                    "label": key.replace("_", " "),
                    "group": "BOSS",
                    "status": status,
                    "same_as_current_capture": same,
                }
                for key in mission_keys
            ],
        }

    def test_requires_authoritative_capture_gap_fail(self):
        status, case = self._status(category="ANIMATION_SEAM")
        with patch.object(recovery, "cockpit_status", return_value=status):
            with self.assertRaisesRegex(recovery.CaptureGapRecoveryError, "not CAPTURE_GAP"):
                recovery._require_capture_gap_failure(Path("root"), Path("pack"))

    def test_choose_session_prefers_regression_case_mission(self):
        route = {
            "sessions": [
                {
                    "session_key": "primary_route_sweep",
                    "score": 900,
                    "missions": [{"key": "world_route_1"}],
                    "gap_targets": [],
                },
                {
                    "session_key": "boss_combat_sweep",
                    "score": 100,
                    "missions": [{"key": "bosses_all_phases"}],
                    "gap_targets": [{"kind": "STATE_GAP", "art_group": "BOSS"}],
                },
            ]
        }
        chosen = recovery._choose_session(route, "bosses")
        self.assertEqual("boss_combat_sweep", chosen["session_key"])

    def test_plan_binds_case_runtime_capture_and_target_session(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "CAPTURE_MISSIONS.json").write_text("{}", encoding="utf-8")
            acceptance = self._acceptance(fp="capture-old")
            gap = {"queue": [], "comparison": {"regressions": []}}
            route = {
                "planned_session_count": 1,
                "sessions": [{
                    "session_key": "boss_combat_sweep",
                    "label": "Boss + player combat/damage sweep",
                    "route_mode": "BOSS_AND_COMBAT_PASS",
                    "score": 50,
                    "instructions": ["Expose every boss phase."],
                    "missions": [{"key": "bosses_all_phases"}],
                    "gap_targets": [{"kind": "STATE_GAP", "art_group": "BOSS", "family": "boss", "target": "phase", "reason": "gap"}],
                }],
            }
            status, case = self._status()
            with patch.object(recovery, "_require_capture_gap_failure", return_value=(status, case)), \
                 patch.object(recovery, "build_acceptance_manifest", return_value=acceptance), \
                 patch.object(recovery, "build_capture_queue", return_value=gap), \
                 patch.object(recovery, "write_gap_outputs", return_value={"json": str(root / "gap.json"), "csv": "", "html": ""}), \
                 patch.object(recovery, "build_session_plan", return_value=route), \
                 patch.object(recovery, "write_route_outputs", return_value={"json": "route.json", "csv": "", "html": ""}):
                (root / "gap.json").write_text(json.dumps(gap), encoding="utf-8")
                result = recovery.plan_recovery(root, root / "runtime", root / "capture", output_dir=root / "Reports")
            self.assertEqual("CAPTURE_GAP_RECOVERY_PLANNED", result["status"])
            self.assertEqual("boss_combat_sweep", result["preferred_session"]["session_key"])
            token = json.loads((root / "Reports" / "REGRESSION_CAPTURE_GAP_TOKEN.json").read_text(encoding="utf-8"))
            self.assertEqual("runtime-old", token["source_runtime_fingerprint"])
            self.assertEqual("capture-old", token["source_capture_fingerprint"])
            self.assertEqual(["bosses_all_phases"], token["target_mission_keys"])

    def test_verify_rejects_unchanged_capture_fingerprint(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            token = {
                "schema": recovery.TOKEN_SCHEMA,
                "case_key": "bosses",
                "case_label": "Bosses",
                "source_capture_fingerprint": "same",
                "target_mission_keys": ["bosses_all_phases"],
                "source_counts": {},
            }
            token_path = root / "token.json"
            token_path.write_text(json.dumps(token), encoding="utf-8")
            with patch.object(recovery, "build_acceptance_manifest", return_value=self._acceptance(fp="same")):
                result = recovery.verify_recovery(root, root / "capture", token_path, output_dir=root / "out")
            self.assertEqual("CAPTURE_RECOVERY_BLOCKED", result["status"])
            self.assertTrue(any("did not change" in item for item in result["blockers"]))

    def test_verify_rejects_capture_regression_even_with_new_fingerprint(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            token = {
                "schema": recovery.TOKEN_SCHEMA,
                "case_key": "bosses",
                "case_label": "Bosses",
                "source_capture_fingerprint": "old",
                "target_mission_keys": ["bosses_all_phases"],
                "source_counts": {},
            }
            token_path = root / "token.json"
            token_path.write_text(json.dumps(token), encoding="utf-8")
            acceptance = self._acceptance(fp="new", regression_count=1)
            with patch.object(recovery, "build_acceptance_manifest", return_value=acceptance):
                result = recovery.verify_recovery(root, root / "capture", token_path, output_dir=root / "out")
            self.assertEqual("CAPTURE_RECOVERY_BLOCKED", result["status"])
            self.assertTrue(any("CAPTURE_REGRESSION" in item for item in result["blockers"]))

    def test_verify_requires_current_fingerprint_bound_verified_missions(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            token = {
                "schema": recovery.TOKEN_SCHEMA,
                "case_key": "bosses",
                "case_label": "Bosses",
                "source_capture_fingerprint": "old",
                "target_mission_keys": ["bosses_all_phases"],
                "source_counts": {},
            }
            token_path = root / "token.json"
            token_path.write_text(json.dumps(token), encoding="utf-8")
            acceptance = self._acceptance(fp="new", status="VERIFIED_IN_GAME", same=False)
            with patch.object(recovery, "build_acceptance_manifest", return_value=acceptance):
                result = recovery.verify_recovery(root, root / "capture", token_path, output_dir=root / "out")
            self.assertEqual("CAPTURE_RECOVERY_BLOCKED", result["status"])
            self.assertTrue(any("not bound" in item for item in result["blockers"]))

    def test_verify_success_routes_to_hd_art_handoff_without_passing_regression(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            token = {
                "schema": recovery.TOKEN_SCHEMA,
                "case_key": "bosses",
                "case_label": "Bosses",
                "source_capture_fingerprint": "old",
                "target_mission_keys": ["bosses_all_phases"],
                "source_counts": {"mapping_count": 95},
            }
            token_path = root / "token.json"
            token_path.write_text(json.dumps(token), encoding="utf-8")
            acceptance = self._acceptance(fp="new")
            with patch.object(recovery, "build_acceptance_manifest", return_value=acceptance):
                result = recovery.verify_recovery(root, root / "capture", token_path, output_dir=root / "out")
            self.assertEqual("CAPTURE_RECOVERED_READY_FOR_HD_HANDOFF", result["status"])
            self.assertEqual([], result["blockers"])
            self.assertIn("SAME regression case", result["roadmap_policy"])
            self.assertFalse(result["privacy_contract"]["capture_pixels"])

    def test_windows_launcher_chains_capture_verify_and_art_handoff(self):
        source = (WINDOWS / "Regression_Capture_Gap_Recovery.ps1").read_text(encoding="utf-8")
        self.assertIn("regression_capture_gap_recovery.py", source)
        self.assertIn("Guided_Capture_Marathon.ps1", source)
        self.assertIn("'verify'", source)
        self.assertIn("Evidence_Bound_Art_Handoff.ps1", source)
        self.assertIn("SAME failed regression case", source)


if __name__ == "__main__":
    unittest.main()
