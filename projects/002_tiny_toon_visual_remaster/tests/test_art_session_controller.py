from __future__ import annotations

import unittest

from pathlib import Path
import sys

TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from art_session_controller import decide_next


class ArtSessionControllerDecisionTests(unittest.TestCase):
    def test_pixel_qa_failure_blocks_next_batch(self):
        result = decide_next(qa_gate="FAIL", mapping_preserved=True, captured_unfinished=12, blocking_items=0)
        self.assertEqual(result["status"], "BLOCKED_QA")
        self.assertFalse(result["continue_art"])

    def test_mapping_change_blocks_next_batch(self):
        result = decide_next(qa_gate="PASS", mapping_preserved=False, captured_unfinished=12, blocking_items=0)
        self.assertEqual(result["status"], "BLOCKED_QA")
        self.assertFalse(result["continue_art"])

    def test_matrix_blocker_stops_automatic_rollover(self):
        result = decide_next(qa_gate="PASS", mapping_preserved=True, captured_unfinished=12, blocking_items=2)
        self.assertEqual(result["status"], "BLOCKED_MATRIX")
        self.assertFalse(result["continue_art"])

    def test_clear_captured_backlog_does_not_fake_whole_game_completion(self):
        result = decide_next(qa_gate="PASS", mapping_preserved=True, captured_unfinished=0, blocking_items=0)
        self.assertEqual(result["status"], "CAPTURED_ART_COMPLETE")
        self.assertFalse(result["continue_art"])
        self.assertIn("gameplay capture", result["next_action"])

    def test_safe_post_qa_state_requests_exact_next_batch(self):
        result = decide_next(qa_gate="PASS", mapping_preserved=True, captured_unfinished=9, blocking_items=0)
        self.assertEqual(result["status"], "NEXT_BATCH_READY")
        self.assertTrue(result["continue_art"])


if __name__ == "__main__":
    unittest.main()
