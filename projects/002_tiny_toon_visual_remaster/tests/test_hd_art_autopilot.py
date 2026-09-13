from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


PROJECT = Path(__file__).resolve().parents[1]
TOOLS = PROJECT / "tools"
WINDOWS = PROJECT / "windows"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

spec = importlib.util.spec_from_file_location("hd_art_autopilot", TOOLS / "hd_art_autopilot.py")
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class HDArtAutopilotTests(unittest.TestCase):
    def _director(self, *, fingerprint: str = "abc", production: str = "SAFE_INCREMENTAL_ART", promotion: str = "PROMOTED") -> dict:
        return {
            "decision": {"production_decision": production},
            "acceptance": {"capture_fingerprint_sha256": fingerprint},
            "promotion": {"promotion_gate": promotion},
        }

    def test_stale_capture_blocks_before_art(self) -> None:
        result = mod.evaluate_autopilot(self._director(fingerprint="old"), "new", sprint_exists=False, next_batch_count=10)
        self.assertFalse(result["allowed"])
        self.assertEqual("BLOCKED_STALE_CAPTURE", result["status"])

    def test_unsafe_or_unpromoted_capture_blocks(self) -> None:
        result = mod.evaluate_autopilot(
            self._director(production="BLOCK_PRODUCTION", promotion="NOT_RUN"),
            "abc",
            sprint_exists=False,
            next_batch_count=10,
        )
        self.assertFalse(result["allowed"])
        self.assertEqual("BLOCKED_UNSAFE_PRODUCTION", result["status"])

    def test_existing_artist_sprint_is_never_overwritten(self) -> None:
        result = mod.evaluate_autopilot(self._director(), "abc", sprint_exists=True, next_batch_count=10)
        self.assertTrue(result["allowed"])
        self.assertEqual("RESUME_EXISTING_SPRINT", result["status"])

    def test_safe_incremental_capture_routes_to_exact_high_impact_batch(self) -> None:
        result = mod.evaluate_autopilot(self._director(), "abc", sprint_exists=False, next_batch_count=25)
        self.assertTrue(result["allowed"])
        self.assertEqual("PREPARE_HIGH_IMPACT_SPRINT", result["status"])

    def test_full_capture_ready_uses_same_art_path(self) -> None:
        result = mod.evaluate_autopilot(
            self._director(production="FULL_CAPTURE_READY"),
            "abc",
            sprint_exists=False,
            next_batch_count=5,
        )
        self.assertTrue(result["allowed"])
        self.assertEqual("PREPARE_HIGH_IMPACT_SPRINT", result["status"])

    def test_zero_batch_reports_captured_art_complete_without_faking_release(self) -> None:
        result = mod.evaluate_autopilot(self._director(), "abc", sprint_exists=False, next_batch_count=0)
        self.assertTrue(result["allowed"])
        self.assertEqual("CAPTURED_ART_COMPLETE", result["status"])
        self.assertIn("capture", result["next_action"].lower())

    def test_report_is_metadata_only_and_contains_no_absolute_local_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = {
                "status": "HIGH_IMPACT_SPRINT_READY",
                "next_action": "Edit the exact batch.",
                "capture_fingerprint_sha256": "f" * 64,
                "visual_completion": {"overall_weighted_percent": 10.0, "captured_unfinished": 20, "next_batch_count": 10},
                "sprint": {"exported": 10},
                "privacy_contract": {"metadata_only": True, "absolute_local_paths": False},
            }
            outputs = mod._write_report(result, Path(tmp))
            payload = json.loads((Path(tmp) / outputs["json"]).read_text(encoding="utf-8"))
            text = json.dumps(payload)
            self.assertNotIn(str(Path(tmp).resolve()), text)
            self.assertTrue(payload["privacy_contract"]["metadata_only"])

    def test_windows_launcher_chains_full_pipeline_before_art_autopilot(self) -> None:
        source = (WINDOWS / "Full_Capture_To_HD_Autopilot.ps1").read_text(encoding="utf-8")
        self.assertIn("Full_Capture_To_HD_Production.ps1", source)
        self.assertIn("hd_art_autopilot.py", source)
        self.assertLess(source.index("& $FullPipeline"), source.index("& $exe @args"))
        self.assertIn("AUTOPILOT STOPPED", source)
        self.assertIn("never overwritten automatically", source)

    def test_roadmap_gate_checkboxes_are_not_modified_by_autopilot_contract(self) -> None:
        source = (TOOLS / "hd_art_autopilot.py").read_text(encoding="utf-8")
        self.assertIn("never edits Gate A-D", source)
        self.assertNotIn("ROADMAP.md", source)


if __name__ == "__main__":
    unittest.main()
