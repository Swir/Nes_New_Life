from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WINDOWS = ROOT / "windows"
TOOLS = ROOT / "tools"


class NextCaptureWindowsIntegrationTests(unittest.TestCase):
    def test_launcher_runs_authoritative_guided_capture_before_resolution(self) -> None:
        source = (WINDOWS / "Capture_Next_Best_Loop.ps1").read_text(encoding="utf-8")
        self.assertIn("Guided_Capture_Marathon.ps1", source)
        self.assertIn("ROUTE_CAPTURE_SESSION_PLAN.json", source)
        self.assertIn("next_capture_action.py", source)
        self.assertLess(source.index("& $Guided"), source.index("& $exe @args"))

    def test_launcher_does_not_write_capture_or_roadmap_completion(self) -> None:
        source = (WINDOWS / "Capture_Next_Best_Loop.ps1").read_text(encoding="utf-8")
        self.assertNotIn("CAPTURE_MISSIONS.json", source)
        self.assertNotIn("ROADMAP.md", source)
        self.assertNotIn("done =", source.lower())

    def test_bat_entry_point_exists(self) -> None:
        source = (WINDOWS / "Capture_Next_Best_Loop.bat").read_text(encoding="utf-8")
        self.assertIn("Capture_Next_Best_Loop.ps1", source)

    def test_resolver_is_metadata_only(self) -> None:
        source = (TOOLS / "next_capture_action.py").read_text(encoding="utf-8")
        self.assertNotIn("copyfile", source)
        self.assertNotIn("shutil", source)
        self.assertNotIn(".png\"", source.lower())


if __name__ == "__main__":
    unittest.main()
