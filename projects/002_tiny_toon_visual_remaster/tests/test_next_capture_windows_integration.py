from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WINDOWS = ROOT / "windows"
TOOLS = ROOT / "tools"


class NextCaptureWindowsIntegrationTests(unittest.TestCase):
    def test_launcher_routes_to_single_highest_impact_session(self) -> None:
        wrapper = (WINDOWS / "Capture_Next_Best_Loop.ps1").read_text(encoding="utf-8")
        single = (WINDOWS / "Capture_Single_Best_Session.ps1").read_text(encoding="utf-8")
        self.assertIn("Capture_Single_Best_Session.ps1", wrapper)
        self.assertIn("route_capture_sequencer.py", single)
        self.assertIn("@($RoutePlan.sessions)[0]", single)
        self.assertIn("VERIFIED_IN_GAME", single)
        self.assertIn("Capture_Coverage_Acceptance.ps1", single)
        self.assertIn("next_capture_action.py", single)

    def test_single_session_refreshes_safe_evidence_after_gameplay(self) -> None:
        source = (WINDOWS / "Capture_Single_Best_Session.ps1").read_text(encoding="utf-8")
        self.assertIn("Local_Capture_Bridge.ps1", source)
        self.assertLess(source.index("& $Launcher"), source.index("& $Bridge"))
        self.assertLess(source.index("& $Bridge"), source.index("& $Acceptance"))
        self.assertIn("Refresh-GapAndRoute", source)

    def test_local_path_memory_is_outside_repository_and_clearable(self) -> None:
        source = (WINDOWS / "Capture_Single_Best_Session.ps1").read_text(encoding="utf-8")
        self.assertIn("$env:LOCALAPPDATA", source)
        self.assertIn("capture-session.json", source)
        self.assertIn("ForgetSavedPaths", source)
        self.assertNotIn("Set-Content -Encoding UTF8 -Path $ProjectRoot", source)

    def test_launcher_does_not_write_roadmap_completion(self) -> None:
        wrapper = (WINDOWS / "Capture_Next_Best_Loop.ps1").read_text(encoding="utf-8")
        single = (WINDOWS / "Capture_Single_Best_Session.ps1").read_text(encoding="utf-8")
        self.assertNotIn("ROADMAP.md", wrapper)
        self.assertNotIn("ROADMAP.md", single)
        self.assertNotIn("done =", wrapper.lower())
        self.assertNotIn("done =", single.lower())

    def test_bat_entry_points_exist(self) -> None:
        wrapper = (WINDOWS / "Capture_Next_Best_Loop.bat").read_text(encoding="utf-8")
        single = (WINDOWS / "Capture_Single_Best_Session.bat").read_text(encoding="utf-8")
        self.assertIn("Capture_Next_Best_Loop.ps1", wrapper)
        self.assertIn("Capture_Single_Best_Session.ps1", single)

    def test_resolver_is_metadata_only(self) -> None:
        source = (TOOLS / "next_capture_action.py").read_text(encoding="utf-8")
        self.assertNotIn("copyfile", source)
        self.assertNotIn("shutil", source)
        self.assertNotIn(".png\"", source.lower())


if __name__ == "__main__":
    unittest.main()
