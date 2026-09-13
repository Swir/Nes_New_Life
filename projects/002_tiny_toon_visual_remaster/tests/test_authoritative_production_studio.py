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
            "OPEN ACTIVE FAMILY WORKBENCH",
            "Finish_Family_And_Playtest.bat",
            "ACTIVE FAMILY ART WORKBENCH",
            "DO THIS NEXT",
            "ROADMAP Gate A–D",
        ):
            self.assertIn(token, source)

    def test_required_authoritative_launchers_exist(self) -> None:
        required = {
            "Full_Capture_To_HD_Autopilot.bat",
            "Continue_HD_Art_Session.bat",
            "Roadmap_Evidence_Readiness.bat",
            "Finish_Family_And_Playtest.bat",
            "Finish_Family_And_Playtest.ps1",
            "Final_Release_Gate.bat",
            "Authoritative_Remaster_Studio.bat",
        }
        self.assertEqual([], sorted(name for name in required if not (WINDOWS / name).is_file()))

    def test_family_finish_is_fail_closed_before_playtest(self) -> None:
        ps1 = (WINDOWS / "Finish_Family_And_Playtest.ps1").read_text(encoding="utf-8")
        finish_pos = ps1.index("High_Impact_Art_Sprint.ps1")
        playtest_pos = ps1.index("Build_HD_Playtest.ps1")
        self.assertLess(finish_pos, playtest_pos)
        self.assertIn("Playtest was NOT started", ps1)
        self.assertIn("-Finish", ps1)
        self.assertIn("-Overwrite", ps1)

    def test_evidence_readiness_launcher_is_read_only(self) -> None:
        ps1 = (WINDOWS / "Roadmap_Evidence_Readiness.ps1").read_text(encoding="utf-8")
        tool = (TOOLS / "roadmap_evidence_readiness.py").read_text(encoding="utf-8")
        self.assertIn("never edits ROADMAP Gate A-D", ps1)
        self.assertIn("READ-ONLY", tool)
        self.assertNotIn("write_text(roadmap", tool.lower())


if __name__ == "__main__":
    unittest.main()
