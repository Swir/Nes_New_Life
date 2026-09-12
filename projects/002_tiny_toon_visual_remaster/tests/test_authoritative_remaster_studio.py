from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


PROJECT = Path(__file__).resolve().parents[1]
TOOLS = PROJECT / "tools"
WINDOWS = PROJECT / "windows"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))


class AuthoritativeRemasterStudioTests(unittest.TestCase):
    def test_module_imports_without_constructing_gui(self) -> None:
        path = TOOLS / "AuthoritativeRemasterStudio.py"
        spec = importlib.util.spec_from_file_location("authoritative_remaster_studio", path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertTrue(hasattr(module, "AuthoritativeRemasterStudio"))
        self.assertTrue(callable(module.main))

    def test_authoritative_windows_launchers_exist(self) -> None:
        required = {
            "Guided_Capture_Marathon.bat",
            "Local_Capture_Bridge.bat",
            "Promote_Capture_To_HD.bat",
            "Studio_Grade_Art_Pass.bat",
            "Finish_High_Impact_Art_Sprint.bat",
            "Build_HD_Playtest.bat",
            "Final_Regression_Cockpit.bat",
            "Final_Release_Gate.bat",
            "Authoritative_Remaster_Studio.bat",
        }
        missing = sorted(name for name in required if not (WINDOWS / name).is_file())
        self.assertEqual([], missing)

    def test_high_impact_launcher_offers_quality_polish_before_finish(self) -> None:
        source = (WINDOWS / "High_Impact_Art_Sprint.bat").read_text(encoding="utf-8")
        self.assertIn("Studio-Grade Art Pass", source)
        self.assertIn("Studio_Grade_Art_Pass.bat", source)
        self.assertIn("Finish + Pixel QA", source)

    def test_studio_source_names_current_authoritative_gates(self) -> None:
        source = (TOOLS / "AuthoritativeRemasterStudio.py").read_text(encoding="utf-8")
        for token in (
            "GUIDED CAPTURE MARATHON",
            "Local Capture Bridge",
            "High-Impact Sprint",
            "Verified fullscreen playtest",
            "Final Regression Cockpit",
            "Final Release Gate",
            "ROADMAP release percentage",
        ):
            self.assertIn(token, source)


if __name__ == "__main__":
    unittest.main()
