from pathlib import Path
import unittest

PROJECT = Path(__file__).resolve().parents[1]
TOOLS = PROJECT / "tools"
WINDOWS = PROJECT / "windows"


class RegressionRepairStudioIntegrationTests(unittest.TestCase):
    def test_authoritative_production_studio_exposes_repair_loop(self) -> None:
        source = (TOOLS / "AuthoritativeProductionStudio.py").read_text(encoding="utf-8")
        self.assertIn("REPAIR FAILED REGRESSION", source)
        self.assertIn("Regression_Repair_Loop.bat", source)
        self.assertIn("<Control-Alt-F10>", source)

    def test_windows_entrypoints_exist(self) -> None:
        self.assertTrue((WINDOWS / "Regression_Repair_Loop.bat").is_file())
        self.assertTrue((WINDOWS / "Regression_Repair_Loop.ps1").is_file())


if __name__ == "__main__":
    unittest.main()
