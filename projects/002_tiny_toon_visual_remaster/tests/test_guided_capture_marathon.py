from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
WINDOWS = ROOT / "windows"
sys.path.insert(0, str(TOOLS))

from guided_capture_marathon import ATTESTATION, build_plan, confirm_mission, write_dashboard  # noqa: E402


class GuidedCaptureMarathonTests(unittest.TestCase):
    @staticmethod
    def _capture(folder: Path, extra: bool = False) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        image.save(folder / "tiles.png")
        lines = ["<ver>106", "<scale>4", "<img>tiles.png", "[hero_player_idle]<tile>0,2E,FF16360F,0,0,1,N"]
        if extra:
            lines.append("[boss_final_attack_1]<tile>0,30,FF27160F,32,0,1,N")
        (folder / "hires.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_plan_starts_empty_and_orders_priority_missions(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            manifest = Path(td) / "CAPTURE_MISSIONS.json"
            plan = build_plan(manifest)
            self.assertEqual(plan["done"], 0)
            self.assertEqual(plan["total"], 11)
            self.assertEqual(plan["release_capture_gate"], "BLOCKED")
            self.assertEqual(plan["next"]["key"], "boot_title_menu")
            self.assertEqual(plan["attestation_required"], ATTESTATION)

    def test_confirmation_requires_explicit_ingame_attestation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = root / "CAPTURE_MISSIONS.json"
            capture = root / "capture"
            self._capture(capture)
            with self.assertRaises(ValueError):
                confirm_mission(manifest, capture, "boot_title_menu", attestation="yes")
            self.assertEqual(build_plan(manifest)["done"], 0)

    def test_verified_mission_records_real_capture_session(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = root / "CAPTURE_MISSIONS.json"
            capture = root / "capture"
            self._capture(capture, extra=True)
            result = confirm_mission(manifest, capture, "boot_title_menu", attestation=ATTESTATION)
            self.assertEqual(result["status"], "RECORDED")
            self.assertEqual(result["plan"]["done"], 1)
            self.assertIn("boot_title_menu", result["session"]["completed_missions"])
            self.assertEqual(result["session"]["capture"]["scale"], 4)

    def test_no_tile_growth_does_not_auto_complete_another_mission(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = root / "CAPTURE_MISSIONS.json"
            capture = root / "capture"
            self._capture(capture)
            confirm_mission(manifest, capture, "boot_title_menu", attestation=ATTESTATION)
            result = confirm_mission(manifest, capture, "player_idle_walk_run", attestation=ATTESTATION)
            self.assertTrue(result["stagnating_warning"])
            plan = result["plan"]
            self.assertEqual(plan["done"], 2)
            self.assertFalse(next(row for row in plan["pending"] if row["key"] == "bosses_all_phases")["done"])

    def test_dashboard_is_metadata_text_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = root / "CAPTURE_MISSIONS.json"
            dashboard = root / "Reports" / "CaptureMarathon" / "CAPTURE_MARATHON.html"
            write_dashboard(manifest, dashboard)
            self.assertTrue(dashboard.is_file())
            self.assertTrue(dashboard.with_suffix(".json").is_file())
            self.assertEqual(list(dashboard.parent.glob("*.png")), [])
            self.assertIn("Tile-count growth never auto-completes", dashboard.read_text(encoding="utf-8"))

    def test_windows_marathon_uses_verified_fullscreen_and_explicit_attestation(self) -> None:
        source = (WINDOWS / "Guided_Capture_Marathon.ps1").read_text(encoding="utf-8")
        self.assertIn("launch_remaster.ps1", source)
        self.assertIn("$LaunchSucceeded = $?", source)
        self.assertIn("VERIFIED_IN_GAME", source)
        self.assertIn("Local_Capture_Bridge.ps1", source)
        self.assertNotIn("if ($LASTEXITCODE -ne 0) { throw 'Could not start a verified-fullscreen MesenCE session.' }", source)


if __name__ == "__main__":
    unittest.main()
