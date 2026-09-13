from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
TOOLS = PROJECT / "tools"
WINDOWS = PROJECT / "windows"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))


class AuthoritativeProductionStudioTests(unittest.TestCase):
    def test_module_imports_without_constructing_gui(self) -> None:
        path = TOOLS / "AuthoritativeProductionStudio.py"
        spec = importlib.util.spec_from_file_location("authoritative_production_studio", path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertTrue(hasattr(module, "AuthoritativeProductionStudio"))
        self.assertTrue(callable(module.main))

    def test_primary_studio_launcher_targets_production_cockpit(self) -> None:
        source = (WINDOWS / "Authoritative_Remaster_Studio.bat").read_text(encoding="utf-8")
        self.assertIn("AuthoritativeProductionStudio.py", source)
        self.assertNotIn("tools\\AuthoritativeRemasterStudio.py", source)

    def test_studio_exposes_current_highest_level_workflows(self) -> None:
        source = (TOOLS / "AuthoritativeProductionStudio.py").read_text(encoding="utf-8")
        for token in (
            "Full_Capture_To_HD_Autopilot.bat",
            "Continue_HD_Art_Session.bat",
            "PRODUCTION_COCKPIT",
            "ROADMAP EVIDENCE READINESS",
            "READY_FOR_HUMAN_REVIEW",
            "DO THIS NEXT",
            "ROADMAP Gate A–D",
        ):
            self.assertIn(token, source)

    def test_required_authoritative_launchers_exist(self) -> None:
        required = {
            "Full_Capture_To_HD_Autopilot.bat",
            "Continue_HD_Art_Session.bat",
            "Roadmap_Evidence_Readiness.bat",
            "Final_Release_Gate.bat",
            "Authoritative_Remaster_Studio.bat",
        }
        self.assertEqual([], sorted(name for name in required if not (WINDOWS / name).is_file()))

    def test_evidence_readiness_launcher_is_read_only(self) -> None:
        ps1 = (WINDOWS / "Roadmap_Evidence_Readiness.ps1").read_text(encoding="utf-8")
        tool = (TOOLS / "roadmap_evidence_readiness.py").read_text(encoding="utf-8")
        self.assertIn("never edits ROADMAP Gate A-D", ps1)
        self.assertIn("READ-ONLY", tool)
        self.assertNotIn("write_text(roadmap", tool.lower())


if __name__ == "__main__":
    unittest.main()
