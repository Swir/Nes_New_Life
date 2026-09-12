from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from final_release_director import final_release_audit, write_final_dashboard  # noqa: E402


class FinalReleaseDirectorTests(unittest.TestCase):
    def _base_pass(self) -> dict:
        return {
            "release_gate": "PASS",
            "release_ready": True,
            "pack_fingerprint": "fp-current",
            "pack": {"scale": 4, "missing_images": []},
            "validator": {"errors": [], "warnings": [], "stats": {}},
            "capture": {"release_capture_gate": "PASS", "done": 11, "total": 11},
            "art_queue": {"exists": True, "rows": 40, "done": 40, "todo": 0, "unassigned": 0},
            "visual_context": {
                "exists": True,
                "gate": "PASS",
                "review_required": 12,
                "reviewed": 12,
                "pending": 0,
                "stale": 0,
            },
            "art_qa": {"exists": True, "gate": "PASS", "fingerprint_matches": True},
            "regression": {
                "gate": "PASS",
                "counts": {"PASS": 10, "FAIL": 0, "STALE": 0, "PENDING": 0},
                "total": 10,
            },
            "blockers": [],
        }

    @staticmethod
    def _fullscreen(gate: str, *, exists: bool = True, verified: bool = True, matches: bool = True) -> dict:
        return {
            "exists": exists,
            "gate": gate,
            "fullscreen_verified": verified,
            "fingerprint_matches": matches,
            "current_pack_fingerprint": "fp-current",
            "recorded_pack_fingerprint": "fp-current" if matches else "fp-old",
            "method": "window_bounds",
            "attempts": 1,
            "path": "local/FULLSCREEN_PLAYTEST.json",
        }

    def _run(self, base: dict, fullscreen: dict) -> dict:
        dummy = Path("dummy")
        with patch("final_release_director.audit_release_candidate", return_value=base), patch(
            "final_release_director.fullscreen_evidence_status", return_value=fullscreen
        ):
            return final_release_audit(dummy, dummy, dummy, dummy, dummy, dummy, dummy)

    def test_base_pass_is_still_blocked_without_fullscreen_evidence(self) -> None:
        result = self._run(
            self._base_pass(),
            self._fullscreen("BLOCKED", exists=False, verified=False, matches=False),
        )
        self.assertEqual(result["release_gate"], "BLOCKED")
        self.assertFalse(result["release_ready"])
        self.assertIn("Verified fullscreen playtest evidence is missing", result["blockers"])
        self.assertEqual(result["next_stage"]["name"], "VERIFIED FULLSCREEN")

    def test_stale_fullscreen_evidence_blocks_current_build(self) -> None:
        result = self._run(
            self._base_pass(),
            self._fullscreen("BLOCKED", exists=True, verified=True, matches=False),
        )
        self.assertEqual(result["release_gate"], "BLOCKED")
        self.assertIn("Fullscreen playtest evidence is stale", " ".join(result["blockers"]))
        fullscreen_stage = next(item for item in result["stages"] if item["name"] == "VERIFIED FULLSCREEN")
        self.assertEqual(fullscreen_stage["gate"], "BLOCKED")

    def test_all_exact_build_gates_allow_release(self) -> None:
        result = self._run(self._base_pass(), self._fullscreen("PASS"))
        self.assertEqual(result["release_gate"], "PASS")
        self.assertTrue(result["release_ready"])
        self.assertIsNone(result["next_stage"])
        self.assertEqual(result["blockers"], [])
        self.assertTrue(all(stage["gate"] == "PASS" for stage in result["stages"]))

    def test_next_action_prioritizes_earlier_production_blocker(self) -> None:
        base = self._base_pass()
        base["release_gate"] = "BLOCKED"
        base["release_ready"] = False
        base["capture"] = {"release_capture_gate": "BLOCKED", "done": 6, "total": 11}
        base["blockers"] = ["Capture missions incomplete (6/11)"]
        result = self._run(base, self._fullscreen("PASS"))
        self.assertEqual(result["next_stage"]["name"], "CAPTURE COVERAGE")
        self.assertEqual(result["release_gate"], "BLOCKED")

    def test_dashboard_is_metadata_only_and_actionable(self) -> None:
        result = self._run(
            self._base_pass(),
            self._fullscreen("BLOCKED", exists=False, verified=False, matches=False),
        )
        with tempfile.TemporaryDirectory() as td:
            path = write_final_dashboard(result, Path(td))
            text = path.read_text(encoding="utf-8")
            self.assertIn("FINAL RELEASE GATE: BLOCKED", text)
            self.assertIn("VERIFIED FULLSCREEN", text)
            self.assertIn("DO THIS NEXT", text)
            self.assertNotIn("data:image", text)
            self.assertNotIn(".nes", text.lower())


if __name__ == "__main__":
    unittest.main()
