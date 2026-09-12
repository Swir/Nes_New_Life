from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from capture_integrity_ledger import build_ledger, capture_fingerprint, write_dashboard  # noqa: E402
from capture_mission_control import MISSION_ITEMS, record_session  # noqa: E402


class CaptureIntegrityLedgerTests(unittest.TestCase):
    @staticmethod
    def _capture(folder: Path, *, extra: bool = False) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        Image.new("RGBA", (64, 64), (0, 0, 0, 0)).save(folder / "tiles.png")
        lines = ["<ver>106", "<scale>4", "<img>tiles.png", "[hero_idle]<tile>0,2E,FF16360F,0,0,1,N"]
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

    def test_regressed_current_capture_blocks_verified_history(self) -> None:
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
            self.assertTrue(ledger["regressions"])
            self.assertEqual(ledger["at_risk_missions"][0]["mission"], "bosses_all_phases")

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
            self.assertEqual(ledger["integrity_gate"], "PASS")
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
            self.assertIn("never auto-completes", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
