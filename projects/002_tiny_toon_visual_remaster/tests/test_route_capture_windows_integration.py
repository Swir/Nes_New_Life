from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WINDOWS = ROOT / "windows"
TOOLS = ROOT / "tools"


class RouteCaptureWindowsIntegrationTests(unittest.TestCase):
    def test_guided_marathon_runs_route_sequencer_and_keeps_per_mission_attestation(self) -> None:
        source = (WINDOWS / "Guided_Capture_Marathon.ps1").read_text(encoding="utf-8")
        for token in (
            "route_capture_sequencer.py",
            "Refresh-RoutePlan",
            "PLAY ONCE — COVER TOGETHER",
            "VERIFIED_IN_GAME",
            "Route-aware grouped pass",
            "Local_Capture_Bridge.ps1",
        ):
            self.assertIn(token, source)
        self.assertIn("$MarathonTool, 'confirm'", source)
        self.assertNotIn("--complete-all", source)

    def test_route_sequencer_is_metadata_only_and_read_only(self) -> None:
        source = (TOOLS / "route_capture_sequencer.py").read_text(encoding="utf-8")
        self.assertIn("ROUTE_CAPTURE_SESSION_PLAN.json", source)
        self.assertIn("ROUTE_CAPTURE_SESSIONS.csv", source)
        self.assertIn("ROUTE_CAPTURE_SESSION_PLAN.html", source)
        self.assertNotIn(".save(", source)
        self.assertNotIn("write_bytes", source)
        self.assertNotIn("ROADMAP.md", source)
        self.assertNotIn('"done"] = True', source)

    def test_no_rom_or_capture_payload_is_added_by_route_workflow(self) -> None:
        source = (TOOLS / "route_capture_sequencer.py").read_text(encoding="utf-8").lower()
        self.assertNotIn("copyfile", source)
        self.assertNotIn("copy2", source)
        self.assertNotIn("shutil.copy", source)
        self.assertNotIn(".nes", source)
        self.assertNotIn("save state", source)


if __name__ == "__main__":
    unittest.main()
