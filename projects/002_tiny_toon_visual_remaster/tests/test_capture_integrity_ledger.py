from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from capture_integrity_ledger import assert_capture_admissible, build_ledger, capture_fingerprint, write_dashboard  # noqa: E402
from capture_mission_control import MISSION_ITEMS, record_session  # noqa: E402


class CaptureIntegrityLedgerTests(unittest.TestCase):
    @staticmethod
    def _capture(folder: Path, *, extra: bool = False, scale: int = 4, missing_image: bool = False) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        if not missing_image:
            Image.new("RGBA", (64, 64), (0, 0, 0, 0)).save(folder / "tiles.png")
        lines = ["<ver>106", f"<scale>{scale}", "<img>tiles.png", "[hero_idle]<tile>0,2E,FF16360F,0,0,1,N"]
        if extra:
            lines.extend([
                "[boss_phase]<tile>0,30,FF27160F,32,0,1,N",
                "[effect_flash]<tile>0,31,FF17263F,48,0,1,N",
            ])
        (folder / "hires.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_fingerprint_changes_when_mapping_changes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            capture = Path(td) / "capture"
            self._capture(capture)
            before = capture_fingerprint(capture)
            self._capture(capture, extra=True)
            after = capture_fingerprint(capture)
            self.assertNotEqual(before, after)

    def test_regressed_current_capture_blocks_recording_but_allows_gameplay_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = root / "CAPTURE_MISSIONS.json"
            rich = root / "rich"
            thin = root / "thin"
            self._capture(rich, extra=True)
            self._capture(thin, extra=False)
            record_session(manifest, rich, ["bosses_all_phases"], "verified")
            ledger = build_ledger(manifest, thin)
            self.assertEqual(ledger["integrity_gate"], "BLOCKED")
            self.assertEqual(ledger["admission_gate"], "BLOCKED")
            self.assertIn("capture_regression_against_verified_history", ledger["structural_blockers"])
            self.assertTrue(ledger["regressions"])
            self.assertEqual(ledger["at_risk_missions"][0]["mission"], "bosses_all_phases")
            self.assertEqual(ledger["recovery"]["mode"], "GAMEPLAY_RECOVERY_REQUIRED")
            self.assertTrue(ledger["recovery"]["gameplay_launch_allowed"])
            self.assertFalse(ledger["recovery"]["mission_recording_allowed"])
            self.assertTrue(any(row["kind"] == "RESTORE_CAPTURE_METRIC" for row in ledger["recovery"]["targets"]))
            with self.assertRaises(ValueError):
                assert_capture_admissible(manifest, thin)

    def test_incomplete_missions_do_not_block_structurally_clean_admission(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = root / "CAPTURE_MISSIONS.json"
            capture = root / "capture"
            self._capture(capture, extra=True)
            ledger = assert_capture_admissible(manifest, capture)
            self.assertEqual(ledger["admission_gate"], "PASS")
            self.assertEqual(ledger["integrity_gate"], "BLOCKED")
            self.assertEqual(ledger["structural_blockers"], [])
            self.assertEqual(ledger["recovery"]["mode"], "CLEAN")
            self.assertTrue(ledger["recovery"]["mission_recording_allowed"])
            self.assertIn("capture_missions_incomplete", ledger["blockers"])

    def test_wrong_scale_and_missing_image_are_hard_preflight_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = root / "CAPTURE_MISSIONS.json"
            wrong_scale = root / "wrong_scale"
            missing = root / "missing"
            self._capture(wrong_scale, scale=2)
            self._capture(missing, missing_image=True)
            scale_ledger = build_ledger(manifest, wrong_scale)
            missing_ledger = build_ledger(manifest, missing)
            self.assertEqual(scale_ledger["admission_gate"], "BLOCKED")
            self.assertIn("capture_scale_is_not_4x", scale_ledger["structural_blockers"])
            self.assertEqual(scale_ledger["recovery"]["mode"], "HARD_BLOCKED")
            self.assertFalse(scale_ledger["recovery"]["gameplay_launch_allowed"])
            self.assertEqual(missing_ledger["admission_gate"], "BLOCKED")
            self.assertIn("missing_referenced_images", missing_ledger["structural_blockers"])
            self.assertEqual(missing_ledger["recovery"]["mode"], "HARD_BLOCKED")
            self.assertFalse(missing_ledger["recovery"]["gameplay_launch_allowed"])

    def test_ledger_never_auto_completes_missions(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = root / "CAPTURE_MISSIONS.json"
            capture = root / "capture"
            self._capture(capture, extra=True)
            ledger = build_ledger(manifest, capture)
            self.assertEqual(ledger["missions"]["done"], 0)
            self.assertEqual(ledger["missions"]["total"], len(MISSION_ITEMS))
            self.assertIn("capture_missions_incomplete", ledger["blockers"])

    def test_all_verified_clean_capture_can_pass_integrity_gate(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = root / "CAPTURE_MISSIONS.json"
            capture = root / "capture"
            self._capture(capture, extra=True)
            record_session(manifest, capture, [key for key, *_ in MISSION_ITEMS], "verified all")
            ledger = build_ledger(manifest, capture)
            self.assertEqual(ledger["admission_gate"], "PASS")
            self.assertEqual(ledger["integrity_gate"], "PASS")
            self.assertEqual(ledger["recovery"]["mode"], "CLEAN")
            self.assertEqual(ledger["blockers"], [])

    def test_dashboard_is_metadata_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = root / "CAPTURE_MISSIONS.json"
            capture = root / "capture"
            output = root / "Reports" / "CaptureIntegrity" / "CAPTURE_INTEGRITY.html"
            self._capture(capture)
            write_dashboard(manifest, capture, output)
            self.assertTrue(output.is_file())
            self.assertTrue(output.with_suffix(".json").is_file())
            self.assertEqual(list(output.parent.glob("*.png")), [])
            html_text = output.read_text(encoding="utf-8")
            self.assertIn("Mission admission gate: PASS", html_text)
            self.assertIn("Recovery mode: <b>CLEAN</b>", html_text)
            self.assertIn("never auto-completes", html_text)


if __name__ == "__main__":
    unittest.main()