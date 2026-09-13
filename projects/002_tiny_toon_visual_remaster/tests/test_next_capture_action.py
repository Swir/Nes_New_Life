from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from next_capture_action import resolve_next_action, write_outputs  # noqa: E402


class NextCaptureActionTests(unittest.TestCase):
    def test_regression_session_is_exposed_as_highest_urgency(self) -> None:
        plan = {
            "sessions": [
                {
                    "session_index": 1,
                    "session_key": "boss_combat_sweep",
                    "label": "Boss + player combat/damage sweep",
                    "route_mode": "BOSS_AND_COMBAT_PASS",
                    "score": 900,
                    "instructions": ["Exercise the boss fight."],
                    "missions": [{"key": "bosses_all_phases", "label": "Every boss phase"}],
                    "gap_targets": [
                        {
                            "kind": "CAPTURE_REGRESSION",
                            "art_group": "BOSS",
                            "family": "BOSS_ALPHA",
                            "target": "restore coverage",
                            "reason": "previous coverage disappeared",
                        }
                    ],
                }
            ]
        }
        result = resolve_next_action(plan)
        self.assertEqual(result["status"], "RECOVER_CAPTURE_REGRESSION")
        self.assertEqual(result["session"]["session_key"], "boss_combat_sweep")
        self.assertEqual(result["session"]["capture_regressions"], 1)

    def test_first_ranked_session_is_the_only_action(self) -> None:
        plan = {
            "sessions": [
                {
                    "session_index": 1,
                    "session_key": "primary_route_sweep",
                    "label": "Primary route",
                    "route_mode": "NORMAL_ROUTE_PASS",
                    "score": 500,
                    "instructions": [],
                    "missions": [{"key": "world_route_1", "label": "Normal route"}],
                    "gap_targets": [],
                },
                {
                    "session_index": 2,
                    "session_key": "ending_ui_effects_sweep",
                    "label": "Ending",
                    "route_mode": "ENDING_PASS",
                    "score": 100,
                    "instructions": [],
                    "missions": [{"key": "ending_credits", "label": "Ending"}],
                    "gap_targets": [],
                },
            ]
        }
        result = resolve_next_action(plan)
        self.assertEqual(result["status"], "CAPTURE_HIGHEST_IMPACT_SESSION")
        self.assertEqual(result["session"]["session_key"], "primary_route_sweep")
        self.assertNotIn("ending_credits", result["session"]["mission_keys"])

    def test_empty_plan_never_claims_gate_a_complete(self) -> None:
        result = resolve_next_action({"sessions": []})
        self.assertEqual(result["status"], "NO_CAPTURE_SESSION_PENDING")
        self.assertIsNone(result["session"])
        self.assertIn("Capture Coverage Acceptance", result["next_action"])
        self.assertNotIn("Gate A complete", result["next_action"])

    def test_outputs_are_metadata_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            result = resolve_next_action({"sessions": []})
            paths = write_outputs(result, root)
            self.assertTrue(Path(paths["json"]).is_file())
            self.assertTrue(Path(paths["dashboard"]).is_file())
            self.assertEqual(list(root.glob("*.png")), [])
            payload = Path(paths["json"]).read_text(encoding="utf-8")
            self.assertNotIn(str(root.resolve()), payload)

    def test_source_cannot_mutate_missions_or_roadmap(self) -> None:
        source = (TOOLS / "next_capture_action.py").read_text(encoding="utf-8")
        self.assertNotIn('"done"] = True', source)
        self.assertNotIn("ROADMAP.md", source)
        self.assertIn("VERIFIED_IN_GAME", source)


if __name__ == "__main__":
    unittest.main()
