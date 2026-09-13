import unittest

from capture_production_director import classify_acceptance


class CaptureProductionDirectorTests(unittest.TestCase):
    def test_regression_has_highest_priority_and_blocks_production(self):
        result = classify_acceptance({
            "acceptance_gate": "BLOCKED",
            "mission_summary": {"pending": 2},
            "hard_blockers": [
                {"kind": "MISSION_COVERAGE", "detail": "2 pending"},
                {"kind": "CAPTURE_REGRESSION", "detail": "1 regression"},
            ],
        })
        self.assertEqual(result["capture_decision"], "FIX_REGRESSION")
        self.assertEqual(result["production_decision"], "BLOCK_PRODUCTION")

    def test_integrity_or_provenance_blocks_production(self):
        for kind in ("INTEGRITY_ADMISSION", "STRUCTURAL_CAPTURE", "MISSION_PROVENANCE"):
            with self.subTest(kind=kind):
                result = classify_acceptance({
                    "acceptance_gate": "BLOCKED",
                    "mission_summary": {"pending": 0},
                    "hard_blockers": [{"kind": kind, "detail": "blocked"}],
                })
                self.assertEqual(result["capture_decision"], "FIX_CAPTURE_INTEGRITY")
                self.assertEqual(result["production_decision"], "BLOCK_PRODUCTION")

    def test_pending_missions_allow_safe_incremental_art_without_claiming_gate_a(self):
        result = classify_acceptance({
            "acceptance_gate": "BLOCKED",
            "mission_summary": {"pending": 7},
            "hard_blockers": [
                {"kind": "MISSION_COVERAGE", "detail": "7 missions pending"},
                {"kind": "GROUP_SIGNAL", "detail": "BOSS not captured yet"},
            ],
        })
        self.assertEqual(result["capture_decision"], "CAPTURE_MORE")
        self.assertEqual(result["production_decision"], "SAFE_INCREMENTAL_ART")
        self.assertIn("7 mission", result["next_action"])

    def test_clean_acceptance_is_review_ready_not_auto_complete(self):
        result = classify_acceptance({
            "acceptance_gate": "READY_FOR_GATE_A_REVIEW",
            "mission_summary": {"pending": 0},
            "hard_blockers": [],
        })
        self.assertEqual(result["capture_decision"], "READY_FOR_GATE_A_REVIEW")
        self.assertEqual(result["production_decision"], "FULL_CAPTURE_READY")
        self.assertIn("manually", result["next_action"].lower())

    def test_at_risk_verified_mission_routes_to_regression_repair(self):
        result = classify_acceptance({
            "acceptance_gate": "BLOCKED",
            "mission_summary": {"pending": 0},
            "hard_blockers": [{"kind": "AT_RISK_MISSION", "detail": "boss evidence at risk"}],
        })
        self.assertEqual(result["capture_decision"], "FIX_REGRESSION")
        self.assertEqual(result["production_decision"], "BLOCK_PRODUCTION")


if __name__ == "__main__":
    unittest.main()
