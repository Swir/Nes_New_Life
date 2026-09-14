from __future__ import annotations

import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
WINDOWS = PROJECT / "windows"


class GuidedRegressionAutoRepairHandoffTests(unittest.TestCase):
    def test_guided_runner_prepares_repair_only_after_authoritative_fail_record(self) -> None:
        source = (WINDOWS / "Guided_Regression_Playtest.ps1").read_text(encoding="utf-8")
        self.assertIn("regression_repair_sprint.py", source)
        self.assertIn("function Start-RepairHandoff", source)
        record_marker = "'record', $Manifest, $RuntimePack, $case.key, 'FAIL'"
        handoff_marker = "Start-RepairHandoff $case $category $target"
        self.assertIn(record_marker, source)
        self.assertIn(handoff_marker, source)
        self.assertLess(source.index(record_marker), source.index(handoff_marker))

    def test_auto_handoff_never_overwrites_existing_repair_sprint(self) -> None:
        source = (WINDOWS / "Guided_Regression_Playtest.ps1").read_text(encoding="utf-8")
        function_source = source[source.index("function Start-RepairHandoff"):source.index("if (-not $RuntimePack)")]
        self.assertIn("'prepare', $ProjectRoot, $RuntimePack", function_source)
        self.assertNotIn("--overwrite", function_source)
        self.assertIn("authoritative FAIL is safely recorded", function_source)
        self.assertIn("Regression_Repair_Loop.bat", function_source)

    def test_guided_handoff_opens_exact_family_board_and_editable_folder(self) -> None:
        source = (WINDOWS / "Guided_Regression_Playtest.ps1").read_text(encoding="utf-8")
        self.assertIn("FAMILY_CONTACT_BOARDS.json", source)
        self.assertIn("$Target.family", source)
        self.assertIn("Start-Process $familyBoard", source)
        self.assertIn("Start-Process explorer.exe $editable", source)
        self.assertIn("AUTOMATIC REPAIR HANDOFF READY", source)

    def test_manual_repair_loop_prefers_family_board_too(self) -> None:
        source = (WINDOWS / "Regression_Repair_Loop.ps1").read_text(encoding="utf-8")
        self.assertIn("function Resolve-PreferredRepairBoard", source)
        self.assertIn("FAMILY_CONTACT_BOARDS.json", source)
        self.assertIn("$familyBoard = Resolve-PreferredRepairBoard", source)
        self.assertIn("Start-Process $familyBoard", source)
        self.assertLess(source.index("Start-Process $familyBoard"), source.index("Start-Process $board"))

    def test_non_art_failures_are_not_forced_into_pixel_repair(self) -> None:
        source = (WINDOWS / "Guided_Regression_Playtest.ps1").read_text(encoding="utf-8")
        function_source = source[source.index("function Start-RepairHandoff"):source.index("if (-not $RuntimePack)")]
        for category in ("MAPPING", "SCALE_OR_FILTER", "CAPTURE_GAP"):
            self.assertNotIn(f"'{category}'", function_source.split("if ($Category -notin $artCategories)")[0])
        self.assertIn("if ($Category -notin $artCategories) { return $null }", function_source)


if __name__ == "__main__":
    unittest.main()
