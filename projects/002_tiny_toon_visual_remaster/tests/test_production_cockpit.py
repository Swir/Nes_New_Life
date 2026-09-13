from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from production_cockpit import decide_next


class ProductionCockpitTests(unittest.TestCase):
    def test_release_pass_has_highest_priority(self) -> None:
        result = decide_next({
            "final_release": {"release_gate": "PASS"},
            "art_session": {"status": "BLOCKED_QA"},
        })
        self.assertEqual(result["stage"], "RELEASE_READY")
        self.assertEqual(result["launcher"], "Final_Release_Gate.bat")

    def test_art_qa_blocker_beats_capture_history(self) -> None:
        result = decide_next({
            "art_session": {"status": "BLOCKED_QA", "next_action": "Fix QA"},
            "capture_to_hd": {"production_decision": "SAFE_INCREMENTAL_ART"},
        })
        self.assertEqual(result["stage"], "BLOCKED_QA")
        self.assertEqual(result["next_action"], "Fix QA")

    def test_active_batch_routes_to_continuation_controller(self) -> None:
        result = decide_next({"hd_art_autopilot": {"status": "HIGH_IMPACT_SPRINT_READY"}})
        self.assertEqual(result["stage"], "ART_BATCH_ACTIVE")
        self.assertEqual(result["launcher"], "Continue_HD_Art_Session.bat")

    def test_safe_capture_without_autopilot_routes_to_full_autopilot(self) -> None:
        result = decide_next({"capture_to_hd": {"production_decision": "SAFE_INCREMENTAL_ART"}})
        self.assertEqual(result["stage"], "SAFE_CAPTURE_NEEDS_ART_ROUTING")
        self.assertEqual(result["launcher"], "Full_Capture_To_HD_Autopilot.bat")

    def test_unsafe_capture_stays_fail_closed(self) -> None:
        result = decide_next({
            "capture_to_hd": {
                "capture_decision": "FIX_REGRESSION",
                "production_decision": "BLOCK_PRODUCTION",
                "next_action": "Replay missing route",
            }
        })
        self.assertEqual(result["stage"], "FIX_REGRESSION")
        self.assertEqual(result["severity"], "block")
        self.assertEqual(result["next_action"], "Replay missing route")

    def test_empty_state_starts_full_authoritative_path(self) -> None:
        result = decide_next({})
        self.assertEqual(result["stage"], "START_CAPTURE_TO_HD_AUTOPILOT")
        self.assertEqual(result["launcher"], "Full_Capture_To_HD_Autopilot.bat")


if __name__ == "__main__":
    unittest.main()
