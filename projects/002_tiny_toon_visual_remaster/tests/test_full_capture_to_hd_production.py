from __future__ import annotations

from pathlib import Path
import unittest


PROJECT = Path(__file__).resolve().parents[1]
WINDOWS = PROJECT / "windows"


class FullCaptureToHDProductionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ps1 = WINDOWS / "Full_Capture_To_HD_Production.ps1"
        self.bat = WINDOWS / "Full_Capture_To_HD_Production.bat"
        self.source = self.ps1.read_text(encoding="utf-8")

    def test_one_click_launchers_exist(self) -> None:
        self.assertTrue(self.ps1.is_file())
        self.assertTrue(self.bat.is_file())

    def test_orchestrator_chains_authoritative_capture_and_production(self) -> None:
        for token in (
            "Guided_Capture_Marathon.ps1",
            "Capture_To_Art_Pipeline.ps1",
            "CAPTURE_PRODUCTION_DIRECTOR.json",
            "-NoGitHubPrompt",
            "-PreviousCapture",
            "-CreateSprint",
        ):
            self.assertIn(token, self.source)

    def test_capture_failure_stops_before_production(self) -> None:
        marathon_call = self.source.index("& $Marathon @marathonArgs")
        marathon_guard = self.source.index("if ($MarathonRc -ne 0)")
        production_call = self.source.index("& $Production @productionArgs")
        self.assertLess(marathon_call, marathon_guard)
        self.assertLess(marathon_guard, production_call)
        self.assertIn("Production will NOT run", self.source)

    def test_unsafe_production_is_fail_closed(self) -> None:
        self.assertIn("BLOCK_PRODUCTION", self.source)
        self.assertIn("exit 3", self.source)
        self.assertIn("unsafe capture evidence was not allowed to mutate production state", self.source)

    def test_session_report_is_metadata_only_and_roadmap_safe(self) -> None:
        for token in (
            "metadata_only = $true",
            "rom_bytes = $false",
            "save_states = $false",
            "capture_pixels = $false",
            "emulator_binaries = $false",
            "absolute_local_paths = $false",
            "never auto-complete Gate A-D",
        ):
            self.assertIn(token, self.source)

    def test_explicit_skip_gameplay_still_revalidates_existing_capture(self) -> None:
        self.assertIn("[switch]$SkipGameplay", self.source)
        self.assertIn("Existing local capture will still be fully revalidated", self.source)
        self.assertIn("Running fingerprint-bound acceptance and guarded production", self.source)


if __name__ == "__main__":
    unittest.main()
